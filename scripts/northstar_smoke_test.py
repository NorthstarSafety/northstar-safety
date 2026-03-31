from __future__ import annotations

import os
import sys
from urllib.parse import urljoin

import requests


BASE_URL = os.getenv("NORTHSTAR_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
WORKSPACE_PATHS = ["/workspace", "/products", "/evidence", "/alerts", "/cases", "/settings"]
PUBLIC_PATHS = [
    "/",
    "/app?shop=demo.myshopify.com&host=test-host",
    "/product",
    "/pricing",
    "/shopify",
    "/security",
    "/support",
    "/contact",
    "/privacy",
    "/terms",
    "/billing",
    "/healthz",
]


def build_session() -> requests.Session:
    session = requests.Session()
    username = os.getenv("BASIC_AUTH_USERNAME", "")
    password = os.getenv("BASIC_AUTH_PASSWORD", "")
    if username and password:
        session.auth = (username, password)
    return session


def login_if_configured(session: requests.Session) -> None:
    email = os.getenv("NORTHSTAR_WORKSPACE_EMAIL", "").strip()
    password = os.getenv("NORTHSTAR_WORKSPACE_PASSWORD", "").strip()
    if not email or not password:
        return
    response = session.post(
        urljoin(BASE_URL, "/login"),
        data={"email": email, "password": password, "next_path": "/workspace"},
        timeout=20,
        allow_redirects=True,
    )
    if response.status_code != 200 or "/login" in response.url:
        raise RuntimeError("Workspace login failed during smoke test.")


def fetch(session: requests.Session, path: str) -> tuple[int, str]:
    response = session.get(urljoin(BASE_URL, path), timeout=20, allow_redirects=True)
    return response.status_code, response.url


def main() -> int:
    session = build_session()
    failures: list[str] = []
    try:
        login_if_configured(session)
    except Exception as exc:  # pragma: no cover - operator utility
        failures.append(f"login -> ERROR: {exc}")

    for path in PUBLIC_PATHS:
        try:
            status, final_url = fetch(session, path)
            print(f"{path} -> {status} ({final_url})")
            if status != 200:
                failures.append(path)
        except Exception as exc:  # pragma: no cover - operator utility
            failures.append(path)
            print(f"{path} -> ERROR: {exc}")

    for path in WORKSPACE_PATHS:
        try:
            status, final_url = fetch(session, path)
            print(f"{path} -> {status} ({final_url})")
            if status != 200:
                failures.append(path)
            elif "/login" in final_url and not os.getenv("NORTHSTAR_WORKSPACE_EMAIL", "").strip():
                print(f"{path} -> NOTE: redirected to login because workspace users are enabled.")
        except Exception as exc:  # pragma: no cover - operator utility
            failures.append(path)
            print(f"{path} -> ERROR: {exc}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
