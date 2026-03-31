from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from northstar_safety.config import BACKUP_DIR, DATA_DIR, DATABASE_BACKEND, DATABASE_PATH, UPLOAD_DIR, settings


def build_manifest() -> dict[str, object]:
    return {
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "app_name": settings.app_name,
        "public_base_url": settings.public_base_url,
        "database_backend": DATABASE_BACKEND,
        "database_path": str(DATABASE_PATH),
        "data_dir": str(DATA_DIR),
        "upload_dir": str(UPLOAD_DIR),
        "smtp_mode": settings.smtp_mode,
        "billing_required": settings.shopify_billing_required,
        "health_canada_enabled": settings.enable_live_health_canada,
        "notes": (
            "SQLite backups include the database file directly. "
            "If PostgreSQL is in use, take a provider snapshot or pg_dump separately."
        ),
    }


def add_tree(archive: ZipFile, source: Path, prefix: str) -> int:
    count = 0
    if not source.exists():
        return count
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        archive.write(path, arcname=f"{prefix}/{path.relative_to(source).as_posix()}")
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a timestamped Northstar Safety backup archive.")
    parser.add_argument("--output-dir", default=str(BACKUP_DIR), help="Directory to store the backup archive.")
    parser.add_argument("--label", default="", help="Optional suffix such as pilot-a or pre-cutover.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    label = f"-{args.label.strip()}" if args.label.strip() else ""
    archive_path = output_dir / f"northstar-backup-{timestamp}{label}.zip"

    manifest = build_manifest()
    files_added = 0
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        if DATABASE_BACKEND == "sqlite" and DATABASE_PATH.exists():
            archive.write(DATABASE_PATH, arcname=f"data/{DATABASE_PATH.name}")
            files_added += 1
        files_added += add_tree(archive, UPLOAD_DIR, "uploads")

    print(f"Created backup: {archive_path}")
    print(f"Files added: {files_added}")
    if DATABASE_BACKEND != "sqlite":
        print("Database backend is PostgreSQL; capture a database snapshot separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
