from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from .config import BACKUP_DIR, DATA_DIR, DATABASE_BACKEND, DATABASE_PATH, DATABASE_URL, UPLOAD_DIR


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    shopify_product_id TEXT,
    catalog_source TEXT NOT NULL DEFAULT 'demo',
    title TEXT NOT NULL,
    handle TEXT NOT NULL,
    vendor TEXT NOT NULL,
    product_type TEXT NOT NULL,
    status TEXT NOT NULL,
    classification TEXT NOT NULL,
    jurisdiction_scope TEXT NOT NULL,
    supplier_name TEXT,
    country_of_origin TEXT,
    age_grade TEXT,
    tags_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS variants (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    shopify_variant_id TEXT,
    sku TEXT NOT NULL,
    title TEXT NOT NULL,
    barcode TEXT,
    price REAL NOT NULL,
    inventory_quantity INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    issuer TEXT,
    source_url TEXT,
    file_name TEXT,
    stored_path TEXT,
    status TEXT NOT NULL,
    issued_at TEXT,
    valid_until TEXT,
    verified_at TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_items (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    requirement_code TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    last_checked_at TEXT,
    stale_after TEXT,
    document_id TEXT REFERENCES documents(id) ON DELETE SET NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    alert_date TEXT NOT NULL,
    jurisdiction TEXT NOT NULL,
    product_name TEXT NOT NULL,
    hazard TEXT NOT NULL,
    description TEXT NOT NULL,
    source_url TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    raw_payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS matches (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variant_id TEXT REFERENCES variants(id) ON DELETE SET NULL,
    score REAL NOT NULL,
    confidence TEXT NOT NULL,
    rationale TEXT NOT NULL,
    status TEXT NOT NULL,
    operator_note TEXT NOT NULL DEFAULT '',
    reviewed_at TEXT,
    reviewed_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(alert_id, product_id)
);

CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    product_id TEXT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    owner TEXT NOT NULL,
    triage_status TEXT NOT NULL,
    decision TEXT NOT NULL,
    priority TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT,
    last_action_summary TEXT NOT NULL,
    source_link TEXT NOT NULL,
    UNIQUE(alert_id, product_id)
);

CREATE TABLE IF NOT EXISTS case_events (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    actor_name TEXT NOT NULL,
    note TEXT NOT NULL,
    source_url TEXT,
    metadata_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_runs (
    id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    run_type TEXT NOT NULL,
    status TEXT NOT NULL,
    records_processed INTEGER NOT NULL,
    records_created INTEGER NOT NULL,
    records_updated INTEGER NOT NULL,
    notes TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS contact_requests (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    company TEXT NOT NULL,
    role_title TEXT,
    website TEXT,
    message TEXT NOT NULL,
    source_page TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS compliance_webhook_events (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    shop_domain TEXT,
    payload_json TEXT NOT NULL,
    received_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS oauth_states (
    state TEXT PRIMARY KEY,
    shop_domain TEXT NOT NULL,
    next_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT
);

CREATE TABLE IF NOT EXISTS shop_installs (
    id TEXT PRIMARY KEY,
    shop_domain TEXT NOT NULL UNIQUE,
    access_token TEXT NOT NULL,
    scope TEXT NOT NULL,
    app_installation_id TEXT,
    launch_url TEXT,
    shop_name TEXT,
    shop_email TEXT,
    primary_domain_host TEXT,
    plan_name TEXT,
    is_partner_development INTEGER NOT NULL DEFAULT 0,
    is_shopify_plus INTEGER NOT NULL DEFAULT 0,
    install_status TEXT NOT NULL,
    installed_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    uninstalled_at TEXT,
    last_synced_at TEXT
);

CREATE TABLE IF NOT EXISTS billing_events (
    id TEXT PRIMARY KEY,
    shop_domain TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    status TEXT NOT NULL,
    confirmation_url TEXT,
    subscription_gid TEXT,
    test_mode INTEGER NOT NULL DEFAULT 0,
    notes TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS workspace_users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS workspace_invites (
    id TEXT PRIMARY KEY,
    token TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    invited_by TEXT NOT NULL,
    note TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    accepted_at TEXT
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id TEXT PRIMARY KEY,
    token TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL REFERENCES workspace_users(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used_at TEXT
);
"""


class DatabaseConnection:
    def __init__(self, backend: str, raw_connection):
        self.backend = backend
        self.raw_connection = raw_connection

    def execute(self, query: str, params=None):
        params = params or ()
        if self.backend == "postgres":
            translated_query = _translate_postgres_sql(query, params)
            return self.raw_connection.execute(translated_query, params)
        return self.raw_connection.execute(query, params)

    def executescript(self, script: str) -> None:
        if self.backend == "postgres":
            for statement in _split_sql_statements(script):
                if statement.strip():
                    self.raw_connection.execute(statement)
            return
        self.raw_connection.executescript(script)

    def commit(self) -> None:
        self.raw_connection.commit()

    def rollback(self) -> None:
        self.raw_connection.rollback()

    def close(self) -> None:
        self.raw_connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


def _translate_qmark_sql(query: str) -> str:
    translated: list[str] = []
    in_string = False
    previous = ""
    for char in query:
        if char == "'" and previous != "\\":
            in_string = not in_string
        if char == "?" and not in_string:
            translated.append("%s")
        else:
            translated.append(char)
        previous = char
    return "".join(translated)


def _translate_named_sql(query: str) -> str:
    translated: list[str] = []
    in_string = False
    previous = ""
    index = 0
    length = len(query)
    while index < length:
        char = query[index]
        if char == "'" and previous != "\\":
            in_string = not in_string
        if (
            char == ":"
            and not in_string
            and index + 1 < length
            and (query[index + 1].isalpha() or query[index + 1] == "_")
            and previous != ":"
        ):
            end = index + 2
            while end < length and (query[end].isalnum() or query[end] == "_"):
                end += 1
            name = query[index + 1 : end]
            translated.append(f"%({name})s")
            previous = query[end - 1]
            index = end
            continue
        translated.append(char)
        previous = char
        index += 1
    return "".join(translated)


def _translate_postgres_sql(query: str, params) -> str:
    if isinstance(params, dict):
        return _translate_named_sql(query)
    return _translate_qmark_sql(query)


def _split_sql_statements(script: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    in_string = False
    previous = ""
    for char in script:
        if char == "'" and previous != "\\":
            in_string = not in_string
        if char == ";" and not in_string:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
        else:
            current.append(char)
        previous = char
    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)
    return statements


def ensure_paths() -> None:
    for path in (DATA_DIR, UPLOAD_DIR, BACKUP_DIR):
        path.mkdir(parents=True, exist_ok=True)
    if DATABASE_BACKEND == "sqlite":
        Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)


def database_summary() -> dict[str, str]:
    return {
        "backend": DATABASE_BACKEND,
        "database_url_present": "yes" if bool(DATABASE_URL) else "no",
        "database_path": str(DATABASE_PATH),
    }


def get_connection() -> DatabaseConnection:
    ensure_paths()
    if DATABASE_BACKEND == "postgres":
        raw = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        return DatabaseConnection("postgres", raw)
    raw = sqlite3.connect(DATABASE_PATH)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA foreign_keys = ON")
    return DatabaseConnection("sqlite", raw)


@contextmanager
def db_cursor():
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    ensure_paths()
    with get_connection() as connection:
        connection.executescript(SCHEMA_SQL)
        _apply_migrations(connection)
        connection.commit()


def _column_names(connection: DatabaseConnection, table_name: str) -> set[str]:
    if connection.backend == "postgres":
        rows = connection.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = ?
            """,
            (table_name,),
        ).fetchall()
        return {row["column_name"] for row in rows}
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _apply_migrations(connection: DatabaseConnection) -> None:
    product_columns = _column_names(connection, "products")
    if "catalog_source" not in product_columns:
        connection.execute("ALTER TABLE products ADD COLUMN catalog_source TEXT NOT NULL DEFAULT 'demo'")

    match_columns = _column_names(connection, "matches")
    if "operator_note" not in match_columns:
        connection.execute("ALTER TABLE matches ADD COLUMN operator_note TEXT NOT NULL DEFAULT ''")
    if "reviewed_at" not in match_columns:
        connection.execute("ALTER TABLE matches ADD COLUMN reviewed_at TEXT")
    if "reviewed_by" not in match_columns:
        connection.execute("ALTER TABLE matches ADD COLUMN reviewed_by TEXT")

    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_shopify_product_id ON products(shopify_product_id)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_variants_shopify_variant_id ON variants(shopify_variant_id)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_evidence_product_requirement ON evidence_items(product_id, requirement_code)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_shop_installs_shop_domain ON shop_installs(shop_domain)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_workspace_users_email ON workspace_users(email)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_workspace_invites_token ON workspace_invites(token)"
    )
    connection.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_password_reset_tokens_token ON password_reset_tokens(token)"
    )
