from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from northstar_safety.config import settings
from northstar_safety.db import get_connection
from northstar_safety.repository import (
    effective_shopify_config,
    get_billing_snapshot,
    latest_shop_install,
    launch_readiness_snapshot,
)
from northstar_safety.services import billing_snapshot, create_shopify_install_url, ShopifySyncError


def route_check(base_url: str, path: str) -> tuple[str, int | str]:
    try:
        response = requests.get(f"{base_url.rstrip('/')}{path}", timeout=15)
        return path, response.status_code
    except Exception as exc:  # pragma: no cover - operator utility
        return path, f"ERR: {exc}"


def public_host_warning(base_url: str) -> str | None:
    host = urlparse(base_url).hostname or ""
    if host in {"127.0.0.1", "localhost"}:
        return "PUBLIC_BASE_URL still points at localhost."
    if host.endswith("loca.lt"):
        return "PUBLIC_BASE_URL is still using a temporary localtunnel domain."
    return None


def _route_status(base_url: str, path: str) -> tuple[int | str, str]:
    try:
        response = requests.get(f"{base_url.rstrip('/')}{path}", timeout=15, allow_redirects=True)
        return response.status_code, response.url
    except Exception as exc:  # pragma: no cover - operator utility
        return f"ERR: {exc}", ""


def _login_remote(base_url: str, email: str, password: str) -> requests.Session:
    session = requests.Session()
    response = session.post(
        f"{base_url.rstrip('/')}/login",
        data={"email": email, "password": password, "next_path": "/workspace"},
        timeout=20,
        allow_redirects=False,
    )
    if response.status_code not in {302, 303}:
        raise RuntimeError(f"Login failed with status {response.status_code}")
    return session


def _remote_launch_check(base_url: str) -> int:
    print(f"Northstar launch check against {base_url}")
    print()

    blockers: list[str] = []
    warning = public_host_warning(base_url)
    if warning:
        blockers.append(warning)

    for path in ["/", "/login", "/install", "/billing", "/healthz", "/robots.txt", "/sitemap.xml"]:
        status, final_url = _route_status(base_url, path)
        print(f"{path:<14} {status} {final_url}".rstrip())

    email = os.getenv("NORTHSTAR_SESSION_EMAIL", "").strip()
    password = os.getenv("NORTHSTAR_SESSION_PASSWORD", "").strip()
    expected_store = os.getenv("NORTHSTAR_EXPECTED_STORE", "").strip()

    if not email or not password:
        blockers.append("Remote-only launch check needs NORTHSTAR_SESSION_EMAIL and NORTHSTAR_SESSION_PASSWORD to inspect the hosted workspace.")
    else:
        try:
            session = _login_remote(base_url, email, password)
        except Exception as exc:  # pragma: no cover - operator utility
            blockers.append(f"Hosted login failed: {exc}")
            session = None

        if session is not None:
            settings_response = session.get(f"{base_url.rstrip('/')}/settings", timeout=20)
            workspace_response = session.get(f"{base_url.rstrip('/')}/workspace", timeout=20)
            print()
            print("Hosted workspace verification")
            print(f"/settings       {settings_response.status_code}")
            print(f"/workspace      {workspace_response.status_code}")

            settings_html = settings_response.text
            workspace_html = workspace_response.text

            if expected_store:
                store_ready = expected_store in settings_html or expected_store in workspace_html
                print(f"store_domain    {'ready' if store_ready else 'blocked'} | {expected_store}")
                if not store_ready:
                    blockers.append(f"Expected store domain {expected_store} is not visible in the hosted workspace.")

            sqlite_active = "SQLite is still active" in settings_html
            smtp_missing = "SMTP is not configured" in settings_html
            no_named_users = "No named operator accounts yet." in settings_html
            live_products = re.search(r"(\d+)\s+live products", settings_html, re.I)
            live_products_count = int(live_products.group(1)) if live_products else 0

            print(f"database        {'sqlite' if sqlite_active else 'not flagged as sqlite'}")
            print(f"smtp            {'blocked' if smtp_missing else 'not flagged as missing'}")
            print(f"named_users     {'blocked' if no_named_users else 'ready'}")
            print(f"live_products   {live_products_count}")

            if sqlite_active:
                blockers.append("Database is still SQLite. Set NORTHSTAR_DATABASE_URL to PostgreSQL before the first paid pilot.")
            if smtp_missing:
                blockers.append("SMTP is not configured for real delivery.")
            if no_named_users:
                blockers.append("No named workspace user exists yet.")
            if live_products_count == 0:
                blockers.append("Hosted workspace is not showing live Shopify products yet.")

            billing_response = session.post(f"{base_url.rstrip('/')}/billing/start", timeout=30, allow_redirects=True)
            billing_text = billing_response.text.lower()
            print()
            print("Hosted billing verification")
            print(f"/billing/start  {billing_response.status_code} {billing_response.url}")
            if "shop-owned" in billing_text and "partners" in billing_text:
                blockers.append("Billing is blocked because the current Shopify app is still shop-owned.")
            elif billing_response.status_code >= 400:
                blockers.append(f"Hosted billing start failed with status {billing_response.status_code}.")

    print()
    if blockers:
        print("Blockers")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1

    print("No launch blockers detected by the hosted checks.")
    return 0


def main() -> int:
    base_url = os.getenv("NORTHSTAR_BASE_URL", os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000"))
    remote_only = os.getenv("NORTHSTAR_REMOTE_ONLY", "").strip().lower() in {"1", "true", "yes", "on"}
    if remote_only:
        return _remote_launch_check(base_url)
    print(f"Northstar launch check against {base_url}")
    print()

    for path in ["/", "/install", "/billing", "/healthz", "/robots.txt", "/sitemap.xml"]:
        route, status = route_check(base_url, path)
        print(f"{route:<14} {status}")

    blockers: list[str] = []
    warning = public_host_warning(base_url)
    if warning:
        blockers.append(warning)

    with get_connection() as connection:
        shopify = effective_shopify_config(connection)
        install = latest_shop_install(connection)
        billing_event = get_billing_snapshot(connection)
        readiness = launch_readiness_snapshot(connection)

        print()
        print("Launch readiness")
        print(f"public_base_url: {'ready' if readiness['public_base_url']['live_ready'] else 'blocked'} | {readiness['public_base_url']['value']}")
        print(f"database: {readiness['database']['backend']} | {readiness['database']['notes']}")
        print(f"secret_key: {'configured' if readiness['secret_key']['configured'] else 'blocked'} | {readiness['secret_key']['notes']}")
        print(f"smtp: {'ready' if readiness['smtp']['configured'] else 'blocked'} | {readiness['smtp']['notes']}")
        print(f"named_users: {readiness['users']['count']} | {readiness['users']['notes']}")
        print(f"uploads: {'ready' if readiness['uploads']['ready'] else 'blocked'} | {readiness['uploads']['path']}")
        print(f"backups: {'ready' if readiness['backups']['ready'] else 'blocked'} | {readiness['backups']['path']}")
        print(f"health_canada: {'enabled' if settings.enable_live_health_canada else 'disabled'}")

        print()
        print("Shopify config")
        print(f"store_domain: {shopify['store_domain'] or '(missing)'}")
        print(f"client_id: {'present' if shopify['client_id_present'] else 'missing'}")
        print(f"client_secret: {'present' if shopify['client_secret_present'] else 'missing'}")
        print(f"token_mode: {shopify['credential_mode']}")

        if shopify["store_domain"] and shopify["client_id_present"]:
            try:
                install_url = create_shopify_install_url(
                    connection,
                    shop_domain=shopify["store_domain"],
                    next_path="/workspace",
                    public_base_url=base_url,
                )
                print(f"install_url: {install_url}")
            except ShopifySyncError as exc:
                blockers.append(f"Install URL generation failed: {exc}")

        print()
        print("Install record")
        if install:
            print(f"shop: {install['shop_domain']}")
            print(f"status: {install['install_status']}")
            print(f"plan: {install['plan_name'] or '(unknown)'}")
        else:
            print("shop: (none)")
            blockers.append("No active shop install record is present.")

        print()
        print("Billing status")
        try:
            live_billing = billing_snapshot(connection)
            active = live_billing["active_subscription"]
            if active:
                print(f"subscription: active ({active['name']})")
            else:
                print("subscription: none")
        except ShopifySyncError as exc:
            print(f"subscription: blocked ({exc})")
            if "shop-owned" in str(exc):
                blockers.append("Billing is blocked because the current Shopify app is still shop-owned.")
            else:
                blockers.append(f"Billing check failed: {exc}")

        if billing_event:
            print(f"last_billing_event: {billing_event['status']} | {billing_event['notes']}")

        if not readiness["database"]["recommended_ready"]:
            blockers.append("Database is still SQLite. Set NORTHSTAR_DATABASE_URL to PostgreSQL before the first paid pilot.")
        if not readiness["secret_key"]["configured"]:
            blockers.append("APP_SECRET_KEY is not configured.")
        if not readiness["smtp"]["configured"]:
            blockers.append("SMTP is not configured for real delivery.")
        if not readiness["users"]["ready"]:
            blockers.append("No named workspace user exists yet.")

    print()
    if blockers:
        print("Blockers")
        for blocker in blockers:
            print(f"- {blocker}")
        return 1

    print("No launch blockers detected by the scripted checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
