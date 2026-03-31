from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


TABLE_ORDER = [
    "settings",
    "products",
    "variants",
    "documents",
    "evidence_items",
    "alerts",
    "matches",
    "cases",
    "case_events",
    "sync_runs",
    "contact_requests",
    "compliance_webhook_events",
    "oauth_states",
    "shop_installs",
    "billing_events",
    "workspace_users",
]


def table_columns(connection, table_name: str) -> list[str]:
    rows = connection.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        """,
        (table_name,),
    ).fetchall()
    return [row["column_name"] for row in rows]


def reset_target(cursor) -> None:
    for table_name in reversed(TABLE_ORDER):
        cursor.execute(f"DELETE FROM {table_name}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy the Northstar SQLite workspace into PostgreSQL.")
    parser.add_argument(
        "--source",
        default=str(ROOT / "northstar_safety_data" / "northstar_safety.db"),
        help="Path to the source SQLite database.",
    )
    parser.add_argument(
        "--target-url",
        default=os.getenv("NORTHSTAR_DATABASE_URL", ""),
        help="Target PostgreSQL connection string. Defaults to NORTHSTAR_DATABASE_URL.",
    )
    parser.add_argument(
        "--reset-target",
        action="store_true",
        help="Delete existing rows in the target before copying data.",
    )
    args = parser.parse_args()

    source_path = Path(args.source).expanduser().resolve()
    if not source_path.exists():
        raise SystemExit(f"Source SQLite database not found: {source_path}")
    if not args.target_url.strip():
        raise SystemExit("Set --target-url or NORTHSTAR_DATABASE_URL before running this migration.")

    os.environ["NORTHSTAR_DATABASE_URL"] = args.target_url.strip()

    from northstar_safety.db import init_db

    init_db()

    source = sqlite3.connect(source_path)
    source.row_factory = sqlite3.Row
    target = psycopg.connect(args.target_url.strip(), row_factory=dict_row)

    copied: dict[str, int] = {}
    try:
        with target.cursor() as cursor:
            if args.reset_target:
                reset_target(cursor)

            for table_name in TABLE_ORDER:
                existing_count = cursor.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()["count"]
                if existing_count and not args.reset_target:
                    raise RuntimeError(
                        f"Target table {table_name} already has {existing_count} rows. "
                        "Re-run with --reset-target if you want to overwrite the target."
                    )

                rows = source.execute(f"SELECT * FROM {table_name}").fetchall()
                if not rows:
                    copied[table_name] = 0
                    continue

                columns = table_columns(cursor, table_name)
                placeholders = ", ".join(["%s"] * len(columns))
                column_list = ", ".join(columns)
                sql = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
                payload = [tuple(row[column] for column in columns) for row in rows]
                cursor.executemany(sql, payload)
                copied[table_name] = len(payload)

        target.commit()
    finally:
        source.close()
        target.close()

    print(f"Migrated {source_path} into PostgreSQL target.")
    for table_name in TABLE_ORDER:
        print(f"{table_name}: {copied.get(table_name, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
