from __future__ import annotations

import os
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from secrets import token_urlsafe


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("NORTHSTAR_DATA_DIR", str(BASE_DIR / "northstar_safety_data")))
UPLOAD_DIR = Path(os.getenv("NORTHSTAR_UPLOAD_DIR", str(DATA_DIR / "uploads")))
DATABASE_PATH = Path(os.getenv("NORTHSTAR_DATABASE_PATH", str(DATA_DIR / "northstar_safety.db")))
BACKUP_DIR = Path(os.getenv("NORTHSTAR_BACKUP_DIR", str(DATA_DIR / "backups")))
DATABASE_URL = os.getenv("NORTHSTAR_DATABASE_URL", "").strip()
DATABASE_BACKEND = "postgres" if DATABASE_URL.startswith(("postgres://", "postgresql://")) else "sqlite"


def _flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _text(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


_configured_secret = _text("APP_SECRET_KEY")
_runtime_secret = _configured_secret or token_urlsafe(32)


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Northstar Safety")
    app_env: str = os.getenv("APP_ENV", "development")
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", os.getenv("PORT", "8000")))
    app_secret_key: str = _runtime_secret
    app_secret_key_configured: bool = bool(_configured_secret)
    session_cookie_name: str = os.getenv("SESSION_COOKIE_NAME", "northstar_session")
    session_max_age_hours: int = int(os.getenv("SESSION_MAX_AGE_HOURS", "12"))
    session_cookie_secure: bool = _flag("SESSION_COOKIE_SECURE", os.getenv("APP_ENV", "development") == "production")
    basic_auth_username: str = os.getenv("BASIC_AUTH_USERNAME", "")
    basic_auth_password: str = os.getenv("BASIC_AUTH_PASSWORD", "")
    shopify_store_domain: str = os.getenv("SHOPIFY_STORE_DOMAIN", "")
    shopify_admin_token: str = os.getenv("SHOPIFY_ADMIN_TOKEN", "")
    shopify_client_id: str = os.getenv("SHOPIFY_CLIENT_ID", "")
    shopify_client_secret: str = os.getenv("SHOPIFY_CLIENT_SECRET", "")
    shopify_api_version: str = os.getenv("SHOPIFY_API_VERSION", "2025-10")
    shopify_app_scopes: str = os.getenv("SHOPIFY_APP_SCOPES", "read_products")
    shopify_embedded_app: bool = _flag("SHOPIFY_EMBEDDED_APP", False)
    shopify_install_redirect_path: str = os.getenv("SHOPIFY_INSTALL_REDIRECT_PATH", "/workspace")
    shopify_billing_required: bool = _flag("SHOPIFY_BILLING_REQUIRED", False)
    shopify_billing_plan_name: str = os.getenv("SHOPIFY_BILLING_PLAN_NAME", "Northstar Safety Founding Plan")
    shopify_billing_price_usd: float = float(os.getenv("SHOPIFY_BILLING_PRICE_USD", "249"))
    shopify_billing_interval: str = os.getenv("SHOPIFY_BILLING_INTERVAL", "EVERY_30_DAYS")
    shopify_billing_trial_days: int = int(os.getenv("SHOPIFY_BILLING_TRIAL_DAYS", "14"))
    shopify_billing_return_path: str = os.getenv("SHOPIFY_BILLING_RETURN_PATH", "/billing/confirm")
    shopify_billing_test_mode: bool = _flag("SHOPIFY_BILLING_TEST_MODE", os.getenv("APP_ENV", "development") != "production")
    public_base_url: str = os.getenv("PUBLIC_BASE_URL", "http://127.0.0.1:8000")
    public_company_name: str = os.getenv("PUBLIC_COMPANY_NAME", "Northstar Safety")
    public_support_email: str = os.getenv("PUBLIC_SUPPORT_EMAIL", "support@northstarsafetyapp.com")
    public_sales_email: str = os.getenv("PUBLIC_SALES_EMAIL", "founder@northstarsafetyapp.com")
    public_demo_link: str = os.getenv(
        "PUBLIC_DEMO_LINK",
        "mailto:founder@northstarsafetyapp.com?subject=Northstar%20Safety%20Demo",
    )
    public_app_install_url: str = os.getenv("PUBLIC_APP_INSTALL_URL", "")
    public_company_location: str = os.getenv("PUBLIC_COMPANY_LOCATION", "United States")
    public_support_hours: str = os.getenv("PUBLIC_SUPPORT_HOURS", "Monday to Friday, 9 AM to 5 PM Eastern")
    public_review_mode: str = os.getenv("PUBLIC_REVIEW_MODE", "private_pilot")
    smtp_mode: str = os.getenv("SMTP_MODE", "disabled")
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", os.getenv("PUBLIC_SUPPORT_EMAIL", "support@northstarsafetyapp.com"))
    smtp_reply_to: str = os.getenv("SMTP_REPLY_TO", "")
    smtp_starttls: bool = _flag("SMTP_STARTTLS", True)
    smtp_ssl: bool = _flag("SMTP_SSL", False)
    public_nav_pages: tuple[str, ...] = field(
        default_factory=lambda: ("home", "product", "pricing", "shopify", "security", "support", "contact")
    )
    enable_live_cpsc: bool = _flag("ENABLE_LIVE_CPSC", True)
    cpsc_query_terms: tuple[str, ...] = tuple(
        term.strip()
        for term in os.getenv(
            "CPSC_QUERY_TERMS",
            "infant,toddler,high chair,carrier,bassinet,bath seat,battery plush,toy",
        ).split(",")
        if term.strip()
    )
    enable_live_health_canada: bool = _flag("ENABLE_LIVE_HEALTH_CANADA", True)
    health_canada_query_terms: tuple[str, ...] = tuple(
        term.strip()
        for term in os.getenv(
            "HEALTH_CANADA_QUERY_TERMS",
            "high chair,carrier,stroller,feeding,bassinet,bath seat,toy",
        ).split(",")
        if term.strip()
    )


settings = Settings()
