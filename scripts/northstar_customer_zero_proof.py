from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def configure_isolated_env(runtime_dir: Path) -> None:
    os.environ["APP_ENV"] = "production"
    os.environ["APP_HOST"] = "127.0.0.1"
    os.environ["APP_PORT"] = "8050"
    os.environ["APP_SECRET_KEY"] = "northstar-customer-zero-proof-secret"
    os.environ["SESSION_COOKIE_SECURE"] = "false"
    os.environ["PUBLIC_BASE_URL"] = "https://app.northstarsafetyapp.com"
    os.environ["NORTHSTAR_DATA_DIR"] = str(runtime_dir)
    os.environ["NORTHSTAR_DATABASE_PATH"] = str(runtime_dir / "northstar.db")
    os.environ["NORTHSTAR_UPLOAD_DIR"] = str(runtime_dir / "uploads")
    os.environ["NORTHSTAR_BACKUP_DIR"] = str(runtime_dir / "backups")
    os.environ["ENABLE_LIVE_CPSC"] = "true"
    os.environ["CPSC_QUERY_TERMS"] = "high chair,carrier"
    os.environ["ENABLE_LIVE_HEALTH_CANADA"] = "true"
    os.environ["HEALTH_CANADA_QUERY_TERMS"] = "high chair,carrier"
    os.environ["SMTP_MODE"] = "disabled"


def main() -> int:
    parser = argparse.ArgumentParser(description="Rehearse the first Northstar customer workflow and export proof files.")
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "output" / "customer-zero-proof"),
        help="Directory to store the proof packet.",
    )
    args = parser.parse_args()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_dir = Path(args.output_dir).expanduser().resolve() / timestamp
    runtime_dir = output_dir / "runtime"
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    configure_isolated_env(runtime_dir)

    from northstar_safety.app import _case_summary_text, _evidence_reminder_text
    from northstar_safety.db import get_connection, init_db
    from northstar_safety.repository import (
        add_document,
        append_case_event,
        create_workspace_user,
        evidence_reminder_snapshot,
        get_case_detail,
        get_setting,
        list_alerts,
        list_cases,
        list_evidence,
        list_products,
        set_setting,
        update_case,
    )
    from northstar_safety.services import (
        ingest_live_cpsc,
        ingest_live_health_canada,
        review_match,
        sync_demo_catalog,
    )

    init_db()
    report: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "output_dir": str(output_dir),
        "steps": [],
    }

    with get_connection() as connection:
        sync_result = sync_demo_catalog(connection)
        set_setting(connection, "merchant_name", "Northstar Customer Zero")
        set_setting(connection, "default_owner", "Northstar Founder")
        set_setting(connection, "jurisdictions", "United States, Canada")
        set_setting(connection, "catalog_mode", "demo")
        set_setting(connection, "reminder_contact_email", "support@northstarsafetyapp.com")
        report["steps"].append({"step": "sync_demo_catalog", "result": sync_result})

        user_id = create_workspace_user(
            connection,
            email="founder@northstarsafetyapp.com",
            full_name="Northstar Founder",
            role="admin",
            password="PilotProof123!",
        )
        report["steps"].append({"step": "create_workspace_user", "user_id": user_id})

        products = list_products(connection)
        evidence_rows = list_evidence(connection, status="missing")
        alerts = list_alerts(connection)
        report["counts_before_live_ingest"] = {
            "products": len(products),
            "missing_evidence": len(evidence_rows),
            "alerts": len(alerts),
        }

        first_missing = evidence_rows[0]
        add_document(
            connection,
            product_id=first_missing["product_id"],
            title=f"{first_missing['title']} proof packet",
            doc_type="Supplier Packet",
            issuer="Northstar Demo Supplier",
            status="verified",
            issued_at="2026-03-01T00:00:00Z",
            valid_until="2027-03-01T00:00:00Z",
            verified_at="2026-03-05T00:00:00Z",
            notes="Uploaded during customer-zero rehearsal.",
            source_url="https://example.com/supplier-packet",
            requirement_code=first_missing["requirement_code"],
            file_name="customer-zero-proof.txt",
            file_bytes=b"Northstar customer-zero uploaded evidence packet.",
        )
        report["steps"].append(
            {
                "step": "attach_document",
                "product_id": first_missing["product_id"],
                "requirement_code": first_missing["requirement_code"],
            }
        )

        match_row = connection.execute(
            "SELECT id FROM matches WHERE status = 'candidate' ORDER BY score DESC, created_at ASC LIMIT 1"
        ).fetchone()
        if not match_row:
            raise RuntimeError("No candidate match was available in the seeded workspace.")
        review_result = review_match(
            connection,
            match_id=match_row["id"],
            review_status="confirmed",
            reviewed_by="Northstar Founder",
            operator_note="Confirmed during customer-zero rehearsal after checking product family and hazard details.",
        )
        report["steps"].append({"step": "confirm_match", "result": review_result})

        case_id = review_result["case_id"]
        append_case_event(
            connection,
            case_id=case_id,
            event_type="founder_follow_up",
            actor_name="Northstar Founder",
            note="Reached out to supplier for current lot coverage and registration materials.",
            source_url="https://example.com/supplier-follow-up",
            metadata={"mode": "customer_zero"},
        )
        update_case(
            connection,
            case_id=case_id,
            triage_status="under_review",
            decision="Supplier follow-up in progress",
            priority="high",
            owner=get_setting(connection, "default_owner", "Northstar Founder"),
            last_action_summary="Confirmed the overlap, attached a proof packet, and requested current lot coverage.",
        )
        report["steps"].append({"step": "update_case", "case_id": case_id})

        live_ingest = {}
        try:
            live_ingest["cpsc"] = ingest_live_cpsc(connection, limit_per_term=3)
        except Exception as exc:  # pragma: no cover - operator utility
            live_ingest["cpsc_error"] = str(exc)
        try:
            live_ingest["health_canada"] = ingest_live_health_canada(connection, limit_per_term=3)
        except Exception as exc:  # pragma: no cover - operator utility
            live_ingest["health_canada_error"] = str(exc)
        report["live_ingest"] = live_ingest

        case_detail = get_case_detail(connection, case_id)
        if not case_detail:
            raise RuntimeError("Case detail disappeared during rehearsal.")
        reminder_snapshot = evidence_reminder_snapshot(connection)
        reminder_snapshot["contact_email"] = "support@northstarsafetyapp.com"

        case_summary = _case_summary_text(case_detail["case"], case_detail["events"])
        reminder_text = _evidence_reminder_text(reminder_snapshot)

        counts_after = {
            "products": len(list_products(connection)),
            "open_cases": len([item for item in list_cases(connection) if item["triage_status"] != "closed"]),
            "alerts": len(list_alerts(connection)),
            "missing_evidence": len(list_evidence(connection, status="missing")),
            "stale_evidence": len(list_evidence(connection, status="stale")),
        }
        report["counts_after_rehearsal"] = counts_after

    case_summary_path = output_dir / "northstar-case-summary.txt"
    reminder_path = output_dir / "northstar-evidence-reminder.txt"
    report_path = output_dir / "customer-zero-report.json"
    markdown_path = output_dir / "customer-zero-report.md"

    case_summary_path.write_text(case_summary, encoding="utf-8")
    reminder_path.write_text(reminder_text, encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    markdown_lines = [
        "# Northstar Customer-Zero Proof",
        "",
        f"Generated at: {report['generated_at']}",
        "",
        "## Workflow completed",
        "",
        "- Seeded a realistic catalog into an isolated workspace",
        "- Created a named admin user for the workspace",
        "- Attached a real uploaded document to a missing evidence requirement",
        "- Confirmed a candidate alert match and reopened or created the linked case",
        "- Added a case event and updated the case summary",
        "- Exported a case summary and evidence reminder draft",
        "- Attempted live official alert refreshes from CPSC and Health Canada",
        "",
        "## Counts before live ingest",
        "",
        f"- Products: {report['counts_before_live_ingest']['products']}",
        f"- Missing evidence items: {report['counts_before_live_ingest']['missing_evidence']}",
        f"- Alerts: {report['counts_before_live_ingest']['alerts']}",
        "",
        "## Counts after rehearsal",
        "",
        f"- Products: {report['counts_after_rehearsal']['products']}",
        f"- Open cases: {report['counts_after_rehearsal']['open_cases']}",
        f"- Alerts: {report['counts_after_rehearsal']['alerts']}",
        f"- Missing evidence items: {report['counts_after_rehearsal']['missing_evidence']}",
        f"- Stale evidence items: {report['counts_after_rehearsal']['stale_evidence']}",
        "",
        "## Output files",
        "",
        f"- Case summary: `{case_summary_path}`",
        f"- Evidence reminder: `{reminder_path}`",
        f"- JSON report: `{report_path}`",
    ]
    markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    print(f"Customer-zero proof written to {output_dir}")
    print(f"Case summary: {case_summary_path}")
    print(f"Evidence reminder: {reminder_path}")
    print(f"Report: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
