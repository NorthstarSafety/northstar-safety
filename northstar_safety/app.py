from __future__ import annotations

import asyncio
import binascii
import hashlib
import hmac
import json
from datetime import datetime, timezone
from base64 import b64decode
from base64 import b64encode
from contextlib import asynccontextmanager
from pathlib import Path
from secrets import compare_digest
from urllib.parse import quote_plus

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .auth import build_session_token, password_strength_error, read_session_token
from .config import settings
from .db import get_connection, init_db
from .domain import CASE_STATUS_LABELS, DOCUMENT_STATUS_LABELS
from .mailer import send_plain_email, smtp_ready
from .repository import (
    add_document,
    authenticate_workspace_user,
    automation_snapshot,
    append_case_event,
    create_workspace_user,
    create_contact_request,
    dashboard_snapshot,
    evidence_reminder_snapshot,
    effective_shopify_config,
    get_alert_detail,
    get_case_detail,
    get_product_detail,
    get_workspace_user,
    launch_readiness_snapshot,
    list_alerts,
    list_cases,
    list_evidence,
    list_products,
    list_settings,
    list_workspace_users,
    mark_shop_uninstalled,
    record_compliance_webhook,
    set_setting,
    settings_snapshot,
    update_case,
)
from .services import (
    ShopifySyncError,
    billing_snapshot,
    complete_shopify_install,
    create_billing_subscription,
    create_shopify_install_url,
    ensure_seeded,
    ingest_live_health_canada,
    ingest_live_cpsc,
    review_match,
    seed_demo_workspace,
    sync_demo_catalog,
    sync_shopify_catalog,
    update_product_profile,
)


PACKAGE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PACKAGE_DIR / "templates"))
PUBLIC_PATHS = {
    "/",
    "/app",
    "/install",
    "/product",
    "/pricing",
    "/shopify",
    "/security",
    "/support",
    "/contact",
    "/privacy",
    "/terms",
    "/auth/callback",
    "/auth/shopify/callback",
    "/billing/confirm",
    "/dashboard",
    "/healthz",
    "/robots.txt",
    "/sitemap.xml",
    "/webhooks/shopify/compliance",
    "/webhooks/shopify/app-uninstalled",
}
PUBLIC_PREFIXES = ("/static/",)
WORKSPACE_PREFIXES = ("/workspace", "/products", "/evidence", "/alerts", "/cases", "/settings", "/billing")
SESSION_FREE_PATHS = {"/login"}


def _flash_payload(request: Request) -> dict[str, str] | None:
    if not request.query_params.get("flash"):
        return None
    return {
        "message": request.query_params.get("flash"),
        "level": request.query_params.get("level", "success"),
    }


def _request_public_base_url(request: Request) -> str:
    configured = settings.public_base_url.rstrip("/")
    if "127.0.0.1" in configured or "localhost" in configured:
        forwarded_host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").split(",")[0].strip()
        forwarded_proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "https").split(",")[0].strip()
        if forwarded_host:
            return f"{forwarded_proto}://{forwarded_host}"
        return str(request.base_url).rstrip("/")
    return configured


def _public_context(request: Request, active_page: str) -> dict[str, str]:
    public_base_url = _request_public_base_url(request)
    return {
        "company_name": settings.public_company_name,
        "support_email": settings.public_support_email,
        "sales_email": settings.public_sales_email,
        "demo_link": settings.public_demo_link,
        "public_base_url": public_base_url,
        "app_install_url": settings.public_app_install_url or f"{public_base_url}/install",
        "company_location": settings.public_company_location,
        "support_hours": settings.public_support_hours,
        "review_mode": settings.public_review_mode.replace("_", " "),
        "workspace_url": "/workspace",
        "active_public_page": active_page,
    }


def _render(request: Request, template_name: str, active_page: str, **context):
    with get_connection() as connection:
        workspace_settings = list_settings(connection)
    payload = {
        "request": request,
        "app_name": settings.app_name,
        "active_page": active_page,
        "flash": _flash_payload(request),
        "workspace_settings": workspace_settings,
        "runtime_settings": settings,
        "basic_auth_enabled": bool(settings.basic_auth_username and settings.basic_auth_password),
        "case_status_labels": CASE_STATUS_LABELS,
        "document_status_labels": DOCUMENT_STATUS_LABELS,
        "current_user": _workspace_session_user(request),
        "workspace_users_enabled": getattr(request.state, "workspace_users_enabled", False),
    }
    payload.update(context)
    return templates.TemplateResponse(template_name, payload)


def _render_public(request: Request, template_name: str, active_page: str, **context):
    payload = {
        "request": request,
        "app_name": settings.app_name,
        "page_title": context.pop("page_title", None),
        "meta_description": context.pop("meta_description", None),
        "flash": _flash_payload(request),
    }
    payload.update(_public_context(request, active_page))
    payload.update(context)
    return templates.TemplateResponse(template_name, payload)


def _redirect(path: str, message: str, level: str = "success") -> RedirectResponse:
    safe_message = quote_plus(message)
    return RedirectResponse(url=f"{path}?flash={safe_message}&level={level}", status_code=303)


def _case_summary_text(case: dict[str, str], events: list[dict[str, str]]) -> str:
    lines = [
        "Northstar Safety Case Summary",
        "",
        f"Product: {case['product_title']}",
        f"Vendor: {case['vendor']}",
        f"Alert: {case['alert_title']}",
        f"Hazard: {case['hazard']}",
        f"Status: {case['triage_status_label']}",
        f"Priority: {case['priority'].capitalize()}",
        f"Owner: {case['owner']}",
        f"Decision: {case['decision']}",
        f"Opened: {case['opened_at']}",
        f"Updated: {case['updated_at']}",
        f"Source: {case['source_url']}",
        "",
        "Latest action summary",
        case["last_action_summary"],
        "",
        "Timeline",
    ]
    if not events:
        lines.append("- No case events recorded yet.")
    else:
        for event in events:
            lines.append(f"- {event['created_at']} | {event['actor_name']} | {event['event_type']}: {event['note']}")
            if event.get("source_url"):
                lines.append(f"  Source: {event['source_url']}")
    lines.append("")
    return "\n".join(lines)


def _evidence_reminder_text(snapshot: dict[str, object]) -> str:
    reminders = snapshot["products"]
    lines = [
        "Northstar Safety Evidence Reminder Draft",
        "",
        f"Suggested recipient: {snapshot['contact_email']}",
        "",
        "Suggested message",
        "",
        "Hello,",
        "",
        "Here is the current Northstar follow-up list for product evidence that is still missing or needs refresh.",
        "",
    ]
    if not reminders:
        lines.extend(
            [
                "There are no missing or stale evidence items in the current workspace.",
                "",
                "Best,",
                "Northstar Safety",
            ]
        )
        return "\n".join(lines)
    for item in reminders:
        lines.append(
            f"- {item['product_title']}: {item['missing_count']} missing, {item['stale_count']} stale"
        )
        if item.get("requirement_preview"):
            lines.append(f"  Top items: {item['requirement_preview']}")
    lines.extend(
        [
            "",
            "Please send the missing files or confirm when refreshed documents will be available.",
            "",
            "Best,",
            "Northstar Safety",
        ]
    )
    return "\n".join(lines)


def _run_automation_cycle(force: bool = False) -> list[str]:
    messages: list[str] = []
    with get_connection() as connection:
        settings_map = list_settings(connection)
        automation = automation_snapshot(connection)
        if settings_map.get("catalog_mode", "demo") == "shopify":
            catalog_job = automation["catalog_sync"]
            if catalog_job["enabled"] and catalog_job["ready"] and (force or catalog_job["due_now"]):
                try:
                    result = sync_shopify_catalog(connection)
                    messages.append(f"Catalog refresh: {result['notes']}")
                except ShopifySyncError as exc:
                    messages.append(f"Catalog refresh failed: {exc}")
        alert_job = automation["alert_ingest"]
        if alert_job["enabled"] and alert_job["ready"] and (force or alert_job["due_now"]):
            try:
                cpsc_result = ingest_live_cpsc(connection)
                notes = [cpsc_result["notes"]]
                if settings.enable_live_health_canada:
                    canada_result = ingest_live_health_canada(connection)
                    notes.append(canada_result["notes"])
                messages.append(f"Alert refresh: {' | '.join(notes)}")
            except Exception as exc:
                messages.append(f"Alert refresh failed: {exc}")
    return messages


async def _automation_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(_run_automation_cycle, False)
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=300)
        except TimeoutError:
            continue


def _is_public_path(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def _is_workspace_surface(path: str) -> bool:
    if path in {"/app"}:
        return True
    return any(path.startswith(prefix) for prefix in WORKSPACE_PREFIXES)


def _shopify_webhook_secret() -> str:
    with get_connection() as connection:
        effective_shopify = effective_shopify_config(connection)
    return effective_shopify["client_secret"] or settings.shopify_client_secret


def _verify_shopify_hmac(raw_body: bytes, header_value: str, secret: str) -> bool:
    if not header_value or not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    computed = b64encode(digest).decode("utf-8")
    return compare_digest(computed, header_value)


def _is_authorized(request: Request) -> bool:
    if not settings.basic_auth_username or not settings.basic_auth_password:
        return True
    header = request.headers.get("authorization", "")
    if not header.startswith("Basic "):
        return False
    try:
        decoded = b64decode(header.split(" ", 1)[1]).decode("utf-8")
    except (ValueError, UnicodeDecodeError, binascii.Error):
        return False
    username, _, password = decoded.partition(":")
    return compare_digest(username, settings.basic_auth_username) and compare_digest(password, settings.basic_auth_password)


def _workspace_session_user(request: Request) -> dict[str, str] | None:
    return getattr(request.state, "workspace_user", None)


def _workspace_session_name(request: Request, fallback: str = "Operator") -> str:
    current_user = _workspace_session_user(request)
    if current_user and current_user.get("full_name"):
        return current_user["full_name"]
    return fallback


def _set_workspace_session(response: RedirectResponse, user_id: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        build_session_token(user_id=user_id, secret_key=settings.app_secret_key, max_age_hours=settings.session_max_age_hours),
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_max_age_hours * 3600,
        path="/",
    )


def _clear_workspace_session(response: RedirectResponse) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with get_connection() as connection:
        ensure_seeded(connection)
    stop_event = asyncio.Event()
    automation_task = asyncio.create_task(_automation_loop(stop_event))
    try:
        yield
    finally:
        stop_event.set()
        await automation_task


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=str(PACKAGE_DIR / "static")), name="static")

    @app.middleware("http")
    async def basic_auth_gate(request: Request, call_next):
        if _is_workspace_surface(request.url.path) or request.url.path in SESSION_FREE_PATHS:
            with get_connection() as connection:
                workspace_users = list_workspace_users(connection)
                request.state.workspace_users_enabled = bool(workspace_users)
                request.state.workspace_user = None
                if workspace_users:
                    token = request.cookies.get(settings.session_cookie_name, "")
                    user_id = read_session_token(token, settings.app_secret_key)
                    if user_id:
                        request.state.workspace_user = get_workspace_user(connection, user_id)
                if (
                    workspace_users
                    and request.url.path not in SESSION_FREE_PATHS
                    and request.state.workspace_user is None
                ):
                    target = quote_plus(request.url.path or "/workspace")
                    return RedirectResponse(url=f"/login?next={target}", status_code=303)
        else:
            request.state.workspace_users_enabled = False
            request.state.workspace_user = None

        if _is_public_path(request.url.path):
            response = await call_next(request)
        elif _is_authorized(request):
            response = await call_next(request)
        else:
            return PlainTextResponse(
                "Authentication required",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Northstar Safety"'},
            )
        if _is_workspace_surface(request.url.path):
            shop = (request.query_params.get("shop") or "").replace("https://", "").replace("http://", "").split("/")[0]
            if not shop:
                with get_connection() as connection:
                    shop = effective_shopify_config(connection)["store_domain"]
            if shop:
                response.headers["Content-Security-Policy"] = f"frame-ancestors https://{shop} https://admin.shopify.com;"
        return response

    @app.get("/healthz")
    async def healthz():
        return PlainTextResponse("ok")

    @app.get("/")
    async def public_home(request: Request):
        return _render_public(
            request,
            "public_home.html",
            active_page="home",
            page_title="Shopify child-product safety control tower",
            meta_description="Northstar Safety helps child-product merchants keep SKU-level evidence, official recall review, and internal action trails in one place.",
        )

    @app.get("/app")
    async def embedded_app_home(request: Request, shop: str = "", host: str = ""):
        if not shop and not host:
            return RedirectResponse(url="/install", status_code=307)
        with get_connection() as connection:
            snapshot = dashboard_snapshot(connection)
            effective_shopify = effective_shopify_config(connection)
        return templates.TemplateResponse(
            "embedded_app.html",
            {
                "request": request,
                "app_name": settings.app_name,
                "flash": _flash_payload(request),
                "shop": shop,
                "host": host,
                "shopify_api_key": effective_shopify["client_id"] or settings.shopify_client_id,
                "counts": snapshot["counts"],
                "effective_shopify": effective_shopify,
                "public_base_url": _request_public_base_url(request),
            },
        )

    @app.get("/product")
    async def public_product(request: Request):
        return _render_public(
            request,
            "public_product.html",
            active_page="product",
            page_title="Product workflow",
            meta_description="See how Northstar turns catalog sync, evidence, alerts, review, and action logging into one monthly workflow.",
        )

    @app.get("/pricing")
    async def public_pricing(request: Request):
        return _render_public(
            request,
            "public_pricing.html",
            active_page="pricing",
            page_title="Pilot pricing",
            meta_description="Northstar Safety pilot pricing for a single-store Shopify child-product workflow.",
        )

    @app.get("/shopify")
    async def public_shopify(request: Request):
        return _render_public(
            request,
            "public_shopify.html",
            active_page="shopify",
            page_title="Shopify app readiness",
            meta_description="Northstar's current Shopify access, permissions posture, and public-app readiness path.",
        )

    @app.get("/security")
    async def public_security(request: Request):
        return _render_public(
            request,
            "public_security.html",
            active_page="security",
            page_title="Security and trust",
            meta_description="Northstar Safety security posture, access scope, support model, and compliance controls.",
        )

    @app.get("/support")
    async def public_support(request: Request):
        return _render_public(
            request,
            "public_support.html",
            active_page="support",
            page_title="Support",
            meta_description="Support expectations, pilot setup help, and contact routes for Northstar Safety.",
        )

    @app.get("/contact")
    async def public_contact(request: Request):
        return _render_public(
            request,
            "public_contact.html",
            active_page="contact",
            page_title="Contact",
            meta_description="Request a Northstar Safety walkthrough or ask about a private pilot.",
        )

    @app.get("/install")
    async def install_page(request: Request, shop: str = ""):
        if shop:
            with get_connection() as connection:
                try:
                    install_url = create_shopify_install_url(
                        connection,
                        shop_domain=shop,
                        next_path="/workspace",
                        public_base_url=_request_public_base_url(request),
                    )
                except ShopifySyncError as exc:
                    return _redirect("/install", str(exc), "error")
            return RedirectResponse(url=install_url, status_code=303)
        return _render_public(
            request,
            "public_install.html",
            active_page="shopify",
            page_title="Install Northstar",
            meta_description="Start the Shopify install for Northstar Safety.",
            shop_domain=shop,
        )

    @app.post("/install")
    async def start_install(request: Request, shop_domain: str = Form(...), next_path: str = Form("/workspace")):
        with get_connection() as connection:
            try:
                install_url = create_shopify_install_url(
                    connection,
                    shop_domain=shop_domain,
                    next_path=next_path,
                    public_base_url=_request_public_base_url(request),
                )
            except ShopifySyncError as exc:
                return _redirect("/install", str(exc), "error")
        return RedirectResponse(url=install_url, status_code=303)

    @app.post("/contact")
    async def submit_contact_request(
        name: str = Form(...),
        email: str = Form(...),
        company: str = Form(...),
        role_title: str = Form(""),
        website: str = Form(""),
        message: str = Form(...),
        source_page: str = Form("contact"),
    ):
        with get_connection() as connection:
            create_contact_request(
                connection,
                name=name,
                email=email,
                company=company,
                role_title=role_title,
                website=website,
                message=message,
                source_page=source_page,
            )
        if smtp_ready():
            try:
                send_plain_email(
                    to_email=settings.public_support_email,
                    subject=f"New Northstar website inquiry from {company}",
                    body=(
                        f"Name: {name}\n"
                        f"Email: {email}\n"
                        f"Company: {company}\n"
                        f"Role: {role_title or '(not provided)'}\n"
                        f"Website: {website or '(not provided)'}\n"
                        f"Source page: {source_page}\n\n"
                        f"Message:\n{message}\n"
                    ),
                    reply_to=email,
                )
            except Exception:
                pass
        return _redirect("/contact", "Thanks. Northstar saved your request for follow-up.")

    @app.get("/login")
    async def login_page(request: Request, next: str = "/workspace"):
        with get_connection() as connection:
            workspace_users = list_workspace_users(connection)
        if not workspace_users:
            return _redirect("/settings", "Create the first workspace user in Settings before requiring named sign-in.", "warning")
        if _workspace_session_user(request):
            return RedirectResponse(url=next or "/workspace", status_code=303)
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "app_name": settings.app_name,
                "flash": _flash_payload(request),
                "next_path": next or "/workspace",
            },
        )

    @app.post("/login")
    async def login_submit(email: str = Form(...), password: str = Form(...), next_path: str = Form("/workspace")):
        with get_connection() as connection:
            user = authenticate_workspace_user(connection, email=email, password=password)
        if not user:
            return _redirect("/login", "Sign-in failed. Check the email and password.", "error")
        response = RedirectResponse(url=next_path or "/workspace", status_code=303)
        _set_workspace_session(response, user["id"])
        return response

    @app.post("/logout")
    async def logout():
        response = RedirectResponse(url="/login", status_code=303)
        _clear_workspace_session(response)
        return response

    @app.get("/auth/callback")
    @app.get("/auth/shopify/callback")
    async def auth_callback(request: Request):
        params = {key: value for key, value in request.query_params.items()}
        with get_connection() as connection:
            try:
                result = complete_shopify_install(connection, params=params)
            except ShopifySyncError as exc:
                return _redirect("/install", str(exc), "error")
        message = f"Northstar connected {result['shop_name']}."
        if result["sync_result"]:
            message = f"{message} {result['sync_result']['notes']}"
        if result["sync_warning"]:
            message = f"{message} Sync warning: {result['sync_warning']}"
        target = "/billing" if settings.shopify_billing_required else result["next_path"]
        return _redirect(target, message)

    @app.get("/privacy")
    async def public_privacy(request: Request):
        return _render_public(
            request,
            "public_privacy.html",
            active_page="privacy",
            page_title="Privacy policy",
            meta_description="Northstar Safety privacy policy for website contact requests and merchant workspace data.",
        )

    @app.get("/terms")
    async def public_terms(request: Request):
        return _render_public(
            request,
            "public_terms.html",
            active_page="terms",
            page_title="Terms of service",
            meta_description="Northstar Safety terms for website visitors and private pilot customers.",
        )

    @app.get("/robots.txt")
    async def robots(request: Request):
        public_base_url = _request_public_base_url(request)
        lines = [
            "User-agent: *",
            "Allow: /",
            "Disallow: /workspace",
            "Disallow: /products",
            "Disallow: /evidence",
            "Disallow: /alerts",
            "Disallow: /cases",
            "Disallow: /settings",
            f"Sitemap: {public_base_url}/sitemap.xml",
        ]
        return PlainTextResponse("\n".join(lines))

    @app.get("/sitemap.xml")
    async def sitemap(request: Request):
        base = _request_public_base_url(request)
        pages = ["/", "/install", "/product", "/pricing", "/shopify", "/security", "/support", "/contact", "/privacy", "/terms"]
        body = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        for page in pages:
            body.extend(
                [
                    "<url>",
                    f"<loc>{base}{page}</loc>",
                    "</url>",
                ]
            )
        body.append("</urlset>")
        return Response(content="".join(body), media_type="application/xml")

    @app.post("/webhooks/shopify/compliance")
    async def compliance_webhook(request: Request):
        secret = _shopify_webhook_secret()
        raw_body = await request.body()
        hmac_header = request.headers.get("X-Shopify-Hmac-Sha256", "")
        if not _verify_shopify_hmac(raw_body, hmac_header, secret):
            return PlainTextResponse("Unauthorized", status_code=401)
        payload = await request.json()
        with get_connection() as connection:
            record_compliance_webhook(
                connection,
                topic=request.headers.get("X-Shopify-Topic", "unknown"),
                shop_domain=request.headers.get("X-Shopify-Shop-Domain", ""),
                payload_json=json.dumps(payload),
            )
        return PlainTextResponse("ok")

    @app.post("/webhooks/shopify/app-uninstalled")
    async def app_uninstalled_webhook(request: Request):
        secret = _shopify_webhook_secret()
        raw_body = await request.body()
        hmac_header = request.headers.get("X-Shopify-Hmac-Sha256", "")
        if not _verify_shopify_hmac(raw_body, hmac_header, secret):
            return PlainTextResponse("Unauthorized", status_code=401)
        shop_domain = request.headers.get("X-Shopify-Shop-Domain", "")
        payload = await request.json()
        with get_connection() as connection:
            record_compliance_webhook(
                connection,
                topic=request.headers.get("X-Shopify-Topic", "app/uninstalled"),
                shop_domain=shop_domain,
                payload_json=json.dumps(payload),
            )
            if shop_domain:
                mark_shop_uninstalled(connection, shop_domain=shop_domain)
        return PlainTextResponse("ok")

    @app.get("/dashboard")
    async def dashboard_redirect():
        return RedirectResponse(url="/workspace", status_code=307)

    @app.get("/workspace")
    async def dashboard(request: Request):
        with get_connection() as connection:
            snapshot = dashboard_snapshot(connection)
        return _render(request, "dashboard.html", active_page="dashboard", **snapshot)

    @app.get("/products")
    async def products(request: Request, q: str = ""):
        with get_connection() as connection:
            product_rows = list_products(connection, search=q)
        return _render(request, "products.html", active_page="products", products=product_rows, search=q)

    @app.get("/products/{product_id}")
    async def product_detail(request: Request, product_id: str):
        with get_connection() as connection:
            detail = get_product_detail(connection, product_id)
        if not detail:
            return _redirect("/products", "Product not found", "error")
        return _render(request, "product_detail.html", active_page="products", **detail)

    @app.post("/products/{product_id}/documents")
    async def product_add_document(
        product_id: str,
        title: str = Form(...),
        doc_type: str = Form(...),
        issuer: str = Form(""),
        status: str = Form("verified"),
        issued_at: str = Form(""),
        valid_until: str = Form(""),
        verified_at: str = Form(""),
        notes: str = Form(""),
        source_url: str = Form(""),
        requirement_code: str = Form(""),
        file: UploadFile | None = File(default=None),
    ):
        file_name = file.filename if file and file.filename else None
        file_bytes = await file.read() if file and file_name else None
        with get_connection() as connection:
            add_document(
                connection,
                product_id=product_id,
                title=title,
                doc_type=doc_type,
                issuer=issuer,
                status=status,
                issued_at=issued_at,
                valid_until=valid_until,
                verified_at=verified_at,
                notes=notes,
                source_url=source_url,
                requirement_code=requirement_code,
                file_name=file_name,
                file_bytes=file_bytes,
            )
        return _redirect(f"/products/{product_id}", "Document added and evidence refreshed")

    @app.post("/products/{product_id}/profile")
    async def product_update_profile(
        product_id: str,
        classification: str = Form(""),
        supplier_name: str = Form(""),
        country_of_origin: str = Form(""),
        age_grade: str = Form(""),
        jurisdiction_scope: str = Form(""),
    ):
        try:
            with get_connection() as connection:
                update_product_profile(
                    connection,
                    product_id=product_id,
                    classification=classification,
                    supplier_name=supplier_name,
                    country_of_origin=country_of_origin,
                    age_grade=age_grade,
                    jurisdiction_scope=jurisdiction_scope,
                )
        except ShopifySyncError as exc:
            return _redirect(f"/products/{product_id}", str(exc), "error")
        return _redirect(f"/products/{product_id}", "Compliance profile updated")

    @app.get("/evidence")
    async def evidence(request: Request, status: str = ""):
        with get_connection() as connection:
            evidence_rows = list_evidence(connection, status=status)
            reminder_snapshot = evidence_reminder_snapshot(connection)
            reminder_snapshot["contact_email"] = list_settings(connection).get("reminder_contact_email", "").strip() or settings.public_support_email
        return _render(
            request,
            "evidence.html",
            active_page="evidence",
            evidence_rows=evidence_rows,
            selected_status=status,
            reminder_snapshot=reminder_snapshot,
        )

    @app.get("/evidence/reminder-draft.txt")
    async def evidence_reminder_download():
        with get_connection() as connection:
            reminder_snapshot = evidence_reminder_snapshot(connection)
            reminder_snapshot["contact_email"] = list_settings(connection).get("reminder_contact_email", "").strip() or settings.public_support_email
        return PlainTextResponse(
            _evidence_reminder_text(reminder_snapshot),
            headers={"Content-Disposition": 'attachment; filename="northstar-evidence-reminder.txt"'},
        )

    @app.get("/alerts")
    async def alerts(request: Request):
        with get_connection() as connection:
            alert_rows = list_alerts(connection)
        return _render(request, "alerts.html", active_page="alerts", alert_rows=alert_rows)

    @app.get("/alerts/{alert_id}")
    async def alert_detail(request: Request, alert_id: str):
        with get_connection() as connection:
            detail = get_alert_detail(connection, alert_id)
        if not detail:
            return _redirect("/alerts", "Alert not found", "error")
        return _render(request, "alert_detail.html", active_page="alerts", **detail)

    @app.get("/cases")
    async def cases(request: Request, status: str = ""):
        with get_connection() as connection:
            case_rows = list_cases(connection, triage_status=status)
        return _render(request, "cases.html", active_page="cases", case_rows=case_rows, selected_status=status)

    @app.get("/cases/{case_id}")
    async def case_detail(request: Request, case_id: str):
        with get_connection() as connection:
            detail = get_case_detail(connection, case_id)
        if not detail:
            return _redirect("/cases", "Case not found", "error")
        return _render(request, "case_detail.html", active_page="cases", **detail)

    @app.get("/cases/{case_id}/summary.txt")
    async def case_summary_download(case_id: str):
        with get_connection() as connection:
            detail = get_case_detail(connection, case_id)
        if not detail:
            return _redirect("/cases", "Case not found", "error")
        return PlainTextResponse(
            _case_summary_text(detail["case"], detail["events"]),
            headers={"Content-Disposition": f'attachment; filename="northstar-case-{case_id}.txt"'},
        )

    @app.post("/cases/{case_id}/status")
    async def case_update(
        request: Request,
        case_id: str,
        triage_status: str = Form(...),
        decision: str = Form(""),
        priority: str = Form("medium"),
        owner: str = Form(""),
        last_action_summary: str = Form(""),
    ):
        with get_connection() as connection:
            update_case(
                connection,
                case_id,
                triage_status,
                decision,
                priority,
                owner or _workspace_session_name(request, "Unassigned"),
                last_action_summary,
            )
        return _redirect(f"/cases/{case_id}", "Case updated")

    @app.post("/cases/{case_id}/events")
    async def case_add_event(
        request: Request,
        case_id: str,
        actor_name: str = Form(""),
        event_type: str = Form("note"),
        note: str = Form(...),
        source_url: str = Form(""),
    ):
        with get_connection() as connection:
            append_case_event(connection, case_id, event_type, actor_name or _workspace_session_name(request), note, source_url)
            connection.commit()
        return _redirect(f"/cases/{case_id}", "Case log entry added")

    @app.get("/settings")
    async def settings_page(request: Request):
        with get_connection() as connection:
            snapshot = settings_snapshot(connection)
        effective_shopify = snapshot["effective_shopify"]
        launch_status = snapshot["launch_readiness"]
        missing_dependencies = []
        if not effective_shopify["store_domain"]:
            missing_dependencies.append("`SHOPIFY_STORE_DOMAIN` is not set, so live Shopify sync stays in demo mode.")
        if not effective_shopify["token_present"] and not effective_shopify["client_credentials_present"]:
            missing_dependencies.append("Add either a Shopify admin token or a client ID and client secret so Northstar can reach the live store.")
        if not launch_status["public_base_url"]["live_ready"]:
            missing_dependencies.append(launch_status["public_base_url"]["notes"])
        if not launch_status["database"]["recommended_ready"]:
            missing_dependencies.append(launch_status["database"]["notes"])
        if not launch_status["secret_key"]["configured"]:
            missing_dependencies.append(launch_status["secret_key"]["notes"])
        if not launch_status["smtp"]["configured"]:
            missing_dependencies.append(launch_status["smtp"]["notes"])
        if not launch_status["users"]["ready"]:
            missing_dependencies.append(launch_status["users"]["notes"])
        if not settings.enable_live_cpsc:
            missing_dependencies.append("`ENABLE_LIVE_CPSC` is off, so CPSC recall pulls are disabled.")
        if not settings.enable_live_health_canada:
            missing_dependencies.append("`ENABLE_LIVE_HEALTH_CANADA` is off, so Canada recall pulls are disabled.")
        return _render(
            request,
            "settings.html",
            active_page="settings",
            missing_dependencies=missing_dependencies,
            **snapshot,
        )

    @app.get("/billing")
    async def billing_page(request: Request):
        with get_connection() as connection:
            try:
                snapshot = billing_snapshot(connection)
            except ShopifySyncError as exc:
                return _redirect("/settings", str(exc), "error")
        return _render(request, "billing.html", active_page="billing", billing=snapshot)

    @app.get("/billing/confirm")
    async def billing_confirm():
        return _redirect("/billing", "Shopify returned to Northstar. Review the billing status below.")

    @app.post("/billing/start")
    async def billing_start(request: Request):
        with get_connection() as connection:
            try:
                result = create_billing_subscription(connection, public_base_url=_request_public_base_url(request))
            except ShopifySyncError as exc:
                return _redirect("/billing", str(exc), "error")
        if result["status"] == "active":
            return _redirect("/billing", result["notes"])
        return RedirectResponse(url=result["confirmation_url"], status_code=303)

    @app.post("/settings")
    async def update_settings(
        merchant_name: str = Form(""),
        default_owner: str = Form(""),
        jurisdictions: str = Form(""),
        catalog_mode: str = Form("demo"),
        shopify_store_domain: str = Form(""),
        shopify_api_version: str = Form(""),
        shopify_admin_token: str = Form(""),
        shopify_client_id: str = Form(""),
        shopify_client_secret: str = Form(""),
        auto_catalog_sync_enabled: str = Form(""),
        auto_catalog_sync_interval_hours: str = Form("12"),
        auto_alert_ingest_enabled: str = Form(""),
        auto_alert_ingest_interval_hours: str = Form("24"),
        reminder_contact_email: str = Form(""),
        evidence_reminder_frequency_days: str = Form("7"),
    ):
        with get_connection() as connection:
            set_setting(connection, "merchant_name", merchant_name)
            set_setting(connection, "default_owner", default_owner)
            set_setting(connection, "jurisdictions", jurisdictions)
            set_setting(connection, "catalog_mode", catalog_mode)
            set_setting(connection, "shopify_store_domain", shopify_store_domain)
            set_setting(connection, "shopify_api_version", shopify_api_version or settings.shopify_api_version)
            set_setting(connection, "auto_catalog_sync_enabled", "yes" if auto_catalog_sync_enabled else "no")
            set_setting(connection, "auto_catalog_sync_interval_hours", auto_catalog_sync_interval_hours or "12")
            set_setting(connection, "auto_alert_ingest_enabled", "yes" if auto_alert_ingest_enabled else "no")
            set_setting(connection, "auto_alert_ingest_interval_hours", auto_alert_ingest_interval_hours or "24")
            set_setting(connection, "reminder_contact_email", reminder_contact_email.strip())
            set_setting(connection, "evidence_reminder_frequency_days", evidence_reminder_frequency_days or "7")
            if shopify_admin_token.strip():
                set_setting(connection, "shopify_admin_token", shopify_admin_token.strip())
                set_setting(connection, "shopify_admin_token_present", "yes")
                set_setting(connection, "shopify_admin_token_expires_at", "")
            if shopify_client_id.strip():
                set_setting(connection, "shopify_client_id", shopify_client_id.strip())
            if shopify_client_secret.strip():
                set_setting(connection, "shopify_client_secret", shopify_client_secret.strip())
            connection.commit()
        return _redirect("/settings", "Settings saved")

    @app.post("/settings/users")
    async def create_user(
        full_name: str = Form(...),
        email: str = Form(...),
        role: str = Form("operator"),
        password: str = Form(...),
    ):
        strength_error = password_strength_error(password)
        if strength_error:
            return _redirect("/settings", strength_error, "error")
        try:
            with get_connection() as connection:
                create_workspace_user(connection, email=email, full_name=full_name, role=role, password=password)
        except Exception as exc:
            return _redirect("/settings", f"User setup failed: {exc}", "error")
        return _redirect("/settings", "Workspace user created")

    @app.post("/settings/test-email")
    async def send_test_email(test_email: str = Form("")):
        if not smtp_ready():
            return _redirect("/settings", "SMTP is not configured yet.", "error")
        try:
            send_plain_email(
                to_email=test_email.strip() or settings.public_support_email,
                subject="Northstar SMTP test",
                body="Northstar successfully sent this launch-readiness test email.",
            )
        except Exception as exc:
            return _redirect("/settings", f"SMTP test failed: {exc}", "error")
        return _redirect("/settings", "SMTP test sent")

    @app.post("/actions/sync-catalog")
    async def action_sync_catalog():
        with get_connection() as connection:
            mode = list_settings(connection).get("catalog_mode", "demo")
            try:
                result = sync_shopify_catalog(connection) if mode == "shopify" else sync_demo_catalog(connection)
            except ShopifySyncError as exc:
                return _redirect("/settings", str(exc), "error")
        if mode == "shopify":
            message = result["notes"]
        else:
            message = f"Demo catalog sync processed {result['records_processed']} products."
        return _redirect("/workspace", message)

    @app.post("/actions/sync-demo")
    async def action_sync_demo():
        with get_connection() as connection:
            result = sync_demo_catalog(connection)
        return _redirect("/workspace", f"Demo catalog sync processed {result['records_processed']} products.")

    @app.post("/actions/run-automation")
    async def action_run_automation():
        messages = await asyncio.to_thread(_run_automation_cycle, True)
        if not messages:
            return _redirect(
                "/settings",
                "No automatic refresh tasks were eligible. Turn on catalog or alert automation in settings first.",
                "warning",
            )
        return _redirect("/settings", " | ".join(messages[:2]))

    @app.post("/actions/reset-demo")
    async def action_reset_demo():
        with get_connection() as connection:
            result = seed_demo_workspace(connection)
        message = f"Demo workspace reset with {result['products']} products and {result['alerts']} alerts."
        return _redirect("/workspace", message)

    @app.post("/actions/ingest-cpsc")
    async def action_ingest_cpsc():
        try:
            with get_connection() as connection:
                cpsc_result = ingest_live_cpsc(connection)
                notes = [cpsc_result["notes"]]
                if settings.enable_live_health_canada:
                    canada_result = ingest_live_health_canada(connection)
                    notes.append(canada_result["notes"])
            level = "success" if cpsc_result["status"] == "completed" else "warning"
            return _redirect("/workspace", " | ".join(notes), level)
        except Exception as exc:
            return _redirect("/settings", f"Official alert ingestion failed: {exc}", "error")

    @app.post("/matches/{match_id}/review")
    async def match_review(
        request: Request,
        match_id: str,
        review_status: str = Form(...),
        reviewed_by: str = Form(""),
        operator_note: str = Form(""),
        return_to: str = Form("/alerts"),
    ):
        try:
            with get_connection() as connection:
                review_match(connection, match_id, review_status, reviewed_by or _workspace_session_name(request), operator_note)
        except ShopifySyncError as exc:
            return _redirect(return_to or "/alerts", str(exc), "error")
        return _redirect(return_to or "/alerts", f"Match marked as {review_status}.")

    @app.get("/documents/{document_id}/download")
    async def download_document(document_id: str):
        with get_connection() as connection:
            row = connection.execute(
                "SELECT file_name, stored_path FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        if not row or not row["stored_path"]:
            return PlainTextResponse("Document file not found", status_code=404)
        return FileResponse(row["stored_path"], filename=row["file_name"])

    return app


app = create_app()
