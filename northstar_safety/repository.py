from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
from typing import Any
from urllib.parse import urlparse

from .auth import hash_password, verify_password
from .config import BACKUP_DIR, DATABASE_BACKEND, DATABASE_URL
from .config import settings
from .config import UPLOAD_DIR
from .domain import (
    CASE_STATUS_LABELS,
    CLASSIFICATION_LABELS,
    DOCUMENT_STATUS_LABELS,
    EVIDENCE_STATUS_LABELS,
    MATCH_STATUS_LABELS,
    SEVERITY_LABELS,
    badge_tone,
    derive_evidence_status,
    evidence_rollup,
    make_id,
    now_iso,
    parse_tags,
)
from .mailer import smtp_snapshot


def _dicts(rows) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _parse_product(row: dict[str, Any]) -> dict[str, Any]:
    row["tags"] = parse_tags(json.loads(row["tags_json"]))
    row["classification_label"] = CLASSIFICATION_LABELS.get(row["classification"], row["classification"])
    return row


def _parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _document_lifecycle(document: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    valid_until = _parse_iso_datetime(document.get("valid_until", ""))
    verified_at = _parse_iso_datetime(document.get("verified_at", ""))
    days_until_expiry = None
    expires_label = "No expiry date"
    lifecycle_code = "no_expiry"
    lifecycle_tone = "neutral"

    if valid_until:
        days_until_expiry = (valid_until.date() - now.date()).days
        if days_until_expiry < 0:
            lifecycle_code = "expired"
            lifecycle_tone = "danger"
            expires_label = f"Expired {-days_until_expiry} days ago"
        elif days_until_expiry <= 30:
            lifecycle_code = "expiring_soon"
            lifecycle_tone = "warning"
            expires_label = f"Expires in {days_until_expiry} days"
        else:
            lifecycle_code = "current_window"
            lifecycle_tone = "success"
            expires_label = f"Expires in {days_until_expiry} days"
    elif document.get("status") == "expired":
        lifecycle_code = "expired"
        lifecycle_tone = "danger"
        expires_label = "Marked expired"

    review_label = "No verified review date"
    review_tone = "neutral"
    if verified_at:
        review_age_days = (now.date() - verified_at.date()).days
        if review_age_days > 365:
            review_label = f"Verified review is {review_age_days} days old"
            review_tone = "warning"
        else:
            review_label = f"Verified review is {review_age_days} days old"
            review_tone = "success"

    return {
        "days_until_expiry": days_until_expiry,
        "expires_label": expires_label,
        "lifecycle_code": lifecycle_code,
        "lifecycle_tone": lifecycle_tone,
        "review_label": review_label,
        "review_tone": review_tone,
    }


def _setting_enabled(value: str | None, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _setting_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return max(1, int(str(value).strip()))
    except ValueError:
        return default


def latest_sync_run(connection, source_name: str, run_type: str, status: str = "completed") -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT *
        FROM sync_runs
        WHERE source_name = ? AND run_type = ? AND status = ?
        ORDER BY started_at DESC
        LIMIT 1
        """,
        (source_name, run_type, status),
    ).fetchone()
    return dict(row) if row else None


def _pilot_checklist(connection, counts: dict[str, int], effective_shopify: dict[str, Any], settings_map: dict[str, str]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    live_sync_completed = int(
        connection.execute(
            "SELECT COUNT(*) AS count FROM sync_runs WHERE source_name = 'shopify-live' AND run_type = 'catalog-sync' AND status = 'completed'"
        ).fetchone()["count"]
    )
    cpsc_sync_completed = int(
        connection.execute(
            "SELECT COUNT(*) AS count FROM sync_runs WHERE source_name = 'cpsc-live' AND run_type = 'alert-ingest' AND status = 'completed'"
        ).fetchone()["count"]
    )
    reviewed_matches = int(
        connection.execute(
            "SELECT COUNT(*) AS count FROM matches WHERE status IN ('confirmed', 'dismissed')"
        ).fetchone()["count"]
    )
    checklist = [
        {
            "title": "Connect the live Shopify store",
            "description": "Store domain and Shopify credentials are configured for the pilot workspace.",
            "completed": bool(effective_shopify["store_domain"] and (effective_shopify["token_present"] or effective_shopify["client_credentials_present"])),
            "href": "/settings",
            "cta": "Open settings",
        },
        {
            "title": "Run the first live catalog sync",
            "description": "Northstar has completed at least one live sync against the connected store.",
            "completed": live_sync_completed > 0,
            "href": "/",
            "cta": "Run sync",
        },
        {
            "title": "Get the first live SKU into scope",
            "description": "At least one live Shopify product is available for evidence and recall review.",
            "completed": counts["products"] > 0,
            "href": "/products",
            "cta": "Review catalog",
        },
        {
            "title": "Upload the first evidence packet",
            "description": "A real document is attached so the evidence workflow becomes concrete.",
            "completed": counts["documents"] > 0,
            "href": "/evidence",
            "cta": "Open evidence queue",
        },
        {
            "title": "Refresh official alerts",
            "description": "CPSC ingestion has run in the current workspace.",
            "completed": cpsc_sync_completed > 0,
            "href": "/alerts",
            "cta": "Open alerts",
        },
        {
            "title": "Review the first alert match",
            "description": "An operator has confirmed or dismissed at least one match candidate.",
            "completed": reviewed_matches > 0,
            "href": "/alerts",
            "cta": "Review matches",
        },
    ]
    next_step = next((item for item in checklist if not item["completed"]), None)
    if next_step and counts["products"] == 0 and settings_map.get("catalog_mode") == "shopify":
        next_step = {
            **next_step,
            "title": "Import or create the first Shopify product",
            "description": "The live store is connected, but Shopify is currently returning zero products. Import the pilot CSV or add one test product in Shopify admin, then sync again.",
            "href": "/static/northstar-pilot-products.csv",
            "cta": "Download pilot CSV",
        }
    return checklist, next_step


def list_settings(connection) -> dict[str, str]:
    rows = connection.execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def get_setting(connection, key: str, default: str = "") -> str:
    row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if not row:
        return default
    return str(row["value"])


def set_setting(connection, key: str, value: str) -> None:
    connection.execute(
        """
        INSERT INTO settings (key, value, updated_at) VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """,
        (key, value, now_iso()),
    )


def _hydrate_documents(rows) -> list[dict[str, Any]]:
    documents = _dicts(rows)
    for document in documents:
        document["status_label"] = DOCUMENT_STATUS_LABELS.get(document["status"], document["status"])
        document["status_tone"] = badge_tone(document["status"])
        document.update(_document_lifecycle(document))
    return documents


def refresh_evidence_statuses(connection) -> None:
    evidence_items = _dicts(
        connection.execute(
            """
            SELECT e.*, d.status AS document_status, d.valid_until, d.verified_at, d.id AS linked_document_id
            FROM evidence_items e
            LEFT JOIN documents d ON d.id = e.document_id
            """
        ).fetchall()
    )
    for item in evidence_items:
        document = None
        if item["linked_document_id"]:
            document = {
                "status": item["document_status"],
                "valid_until": item["valid_until"],
                "verified_at": item["verified_at"],
            }
        new_status = derive_evidence_status(document, item["stale_after"])
        if new_status != item["status"]:
            connection.execute(
                "UPDATE evidence_items SET status = ?, updated_at = ? WHERE id = ?",
                (new_status, now_iso(), item["id"]),
            )
    connection.commit()


def dashboard_snapshot(connection) -> dict[str, Any]:
    refresh_evidence_statuses(connection)
    counts = {}
    queries = {
        "products": "SELECT COUNT(*) AS count FROM products",
        "alerts": "SELECT COUNT(*) AS count FROM alerts",
        "open_cases": "SELECT COUNT(*) AS count FROM cases WHERE triage_status != 'closed'",
        "missing_evidence": "SELECT COUNT(*) AS count FROM evidence_items WHERE status = 'missing'",
        "stale_evidence": "SELECT COUNT(*) AS count FROM evidence_items WHERE status = 'stale'",
        "critical_alerts": "SELECT COUNT(*) AS count FROM alerts WHERE severity = 'critical'",
        "documents": "SELECT COUNT(*) AS count FROM documents",
    }
    for key, query in queries.items():
        counts[key] = int(connection.execute(query).fetchone()["count"])

    products = list_products(connection)
    recent_cases = [case for case in list_cases(connection) if case["triage_status"] != "closed"][:5]
    recent_alerts = list_alerts(connection)[:5]
    stale_items = list_evidence(connection, status="stale")[:5]
    missing_items = list_evidence(connection, status="missing")[:5]
    sync_runs = _dicts(
        connection.execute(
            "SELECT * FROM sync_runs ORDER BY started_at DESC LIMIT 6"
        ).fetchall()
    )
    settings = list_settings(connection)
    effective_shopify = effective_shopify_config(connection)
    pilot_checklist, next_step = _pilot_checklist(connection, counts, effective_shopify, settings)
    automation = automation_snapshot(connection)
    evidence_reminders = evidence_reminder_snapshot(connection)

    return {
        "counts": counts,
        "products": products,
        "recent_cases": recent_cases,
        "recent_alerts": recent_alerts,
        "stale_items": stale_items,
        "missing_items": missing_items,
        "sync_runs": sync_runs,
        "settings": settings,
        "effective_shopify": effective_shopify,
        "pilot_checklist": pilot_checklist,
        "next_step": next_step,
        "automation": automation,
        "evidence_reminders": evidence_reminders,
    }


def list_products(connection, search: str = "") -> list[dict[str, Any]]:
    query = "SELECT * FROM products"
    params: list[Any] = []
    if search.strip():
        query += " WHERE lower(title) LIKE ? OR lower(vendor) LIKE ? OR lower(product_type) LIKE ?"
        needle = f"%{search.strip().lower()}%"
        params.extend([needle, needle, needle])
    query += " ORDER BY title"
    products = [_parse_product(item) for item in _dicts(connection.execute(query, params).fetchall())]
    for product in products:
        evidence_counts = connection.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM evidence_items
            WHERE product_id = ?
            GROUP BY status
            """,
            (product["id"],),
        ).fetchall()
        product["evidence_summary"] = {row["status"]: row["count"] for row in evidence_counts}
        total_evidence = sum(product["evidence_summary"].values())
        current_evidence = product["evidence_summary"].get("current", 0)
        product["readiness_score"] = int(round((current_evidence / total_evidence) * 100)) if total_evidence else 0
        primary_variant = connection.execute(
            "SELECT sku FROM variants WHERE product_id = ? AND sku != '' ORDER BY title LIMIT 1",
            (product["id"],),
        ).fetchone()
        product["primary_sku"] = primary_variant["sku"] if primary_variant else "SKU missing"
        product["case_count"] = int(
            connection.execute("SELECT COUNT(*) AS count FROM cases WHERE product_id = ? AND triage_status != 'closed'", (product["id"],)).fetchone()[
                "count"
            ]
        )
        product["case_history_count"] = int(
            connection.execute("SELECT COUNT(*) AS count FROM cases WHERE product_id = ?", (product["id"],)).fetchone()["count"]
        )
        product["alert_count"] = int(
            connection.execute(
                "SELECT COUNT(*) AS count FROM matches WHERE product_id = ? AND status != 'dismissed'",
                (product["id"],),
            ).fetchone()["count"]
        )
    return products


def get_product_detail(connection, product_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row:
        return None
    product = _parse_product(dict(row))
    variants = _dicts(connection.execute("SELECT * FROM variants WHERE product_id = ? ORDER BY title", (product_id,)).fetchall())
    documents = _hydrate_documents(connection.execute("SELECT * FROM documents WHERE product_id = ? ORDER BY updated_at DESC", (product_id,)).fetchall())
    evidence = _dicts(
        connection.execute(
            """
            SELECT e.*, d.title AS document_title, d.doc_type AS document_type
            FROM evidence_items e
            LEFT JOIN documents d ON d.id = e.document_id
            WHERE e.product_id = ?
            ORDER BY e.title
            """,
            (product_id,),
        ).fetchall()
    )
    for item in evidence:
        item["status_label"] = EVIDENCE_STATUS_LABELS.get(item["status"], item["status"])
        item["status_tone"] = badge_tone(item["status"])
    matches = _dicts(
        connection.execute(
            """
            SELECT m.*, a.title AS alert_title, a.severity, a.source_name, a.alert_date, a.source_url
            FROM matches m
            JOIN alerts a ON a.id = m.alert_id
            WHERE m.product_id = ?
            ORDER BY m.score DESC, a.alert_date DESC
            """,
            (product_id,),
        ).fetchall()
    )
    for match in matches:
        match["severity_label"] = SEVERITY_LABELS.get(match["severity"], match["severity"])
        match["severity_tone"] = badge_tone(match["severity"])
        match["confidence_tone"] = badge_tone("action_needed" if match["confidence"] == "high" else "monitoring")
        match["status_label"] = MATCH_STATUS_LABELS.get(match["status"], match["status"])
        match["status_tone"] = badge_tone(match["status"])
        match["reviewed_at_short"] = match["reviewed_at"][:10] if match.get("reviewed_at") else ""
    cases = list_cases(connection, product_id=product_id)
    active_case_count = sum(1 for case in cases if case["triage_status"] != "closed")
    evidence_summary = evidence_rollup(evidence)
    profile_gaps = []
    if not product.get("supplier_name"):
        profile_gaps.append("Supplier")
    if not product.get("country_of_origin"):
        profile_gaps.append("Country of origin")
    if not product.get("age_grade"):
        profile_gaps.append("Age grade")
    suggested_requirement = next((item["requirement_code"] for item in evidence if item["status"] != "current"), "")
    return {
        "product": product,
        "variants": variants,
        "documents": documents,
        "evidence": evidence,
        "matches": matches,
        "cases": cases,
        "active_case_count": active_case_count,
        "evidence_summary": evidence_summary,
        "profile_gaps": profile_gaps,
        "classification_options": [{"value": key, "label": value} for key, value in CLASSIFICATION_LABELS.items()],
        "readiness_score": int(round((evidence_summary["current"] / evidence_summary["total"]) * 100)) if evidence_summary["total"] else 0,
        "suggested_requirement": suggested_requirement,
    }


def list_evidence(connection, status: str = "", product_id: str = "", search: str = "") -> list[dict[str, Any]]:
    query = """
        SELECT e.*, p.title AS product_title, p.classification, d.title AS document_title, d.doc_type AS document_type
        FROM evidence_items e
        JOIN products p ON p.id = e.product_id
        LEFT JOIN documents d ON d.id = e.document_id
        WHERE 1 = 1
    """
    params: list[Any] = []
    if status:
        query += " AND e.status = ?"
        params.append(status)
    if product_id:
        query += " AND e.product_id = ?"
        params.append(product_id)
    if search.strip():
        query += " AND (lower(p.title) LIKE ? OR lower(e.title) LIKE ? OR lower(COALESCE(d.title, '')) LIKE ? OR lower(COALESCE(p.vendor, '')) LIKE ?)"
        needle = f"%{search.strip().lower()}%"
        params.extend([needle, needle, needle, needle])
    query += " ORDER BY CASE e.status WHEN 'missing' THEN 0 WHEN 'stale' THEN 1 WHEN 'review' THEN 2 ELSE 3 END, p.title, e.title"
    items = _dicts(connection.execute(query, params).fetchall())
    for item in items:
        item["status_label"] = EVIDENCE_STATUS_LABELS.get(item["status"], item["status"])
        item["status_tone"] = badge_tone(item["status"])
        item["classification_label"] = CLASSIFICATION_LABELS.get(item["classification"], item["classification"])
    return items


def list_alerts(connection, search: str = "", severity: str = "") -> list[dict[str, Any]]:
    query = """
            SELECT a.*,
                COUNT(DISTINCT CASE WHEN m.status != 'dismissed' THEN m.id END) AS match_count,
                COUNT(DISTINCT CASE WHEN m.status = 'confirmed' THEN m.id END) AS confirmed_count,
                COUNT(DISTINCT CASE WHEN m.status = 'dismissed' THEN m.id END) AS dismissed_count,
                MAX(CASE WHEN m.status != 'dismissed' THEN m.score END) AS top_score,
                MAX(CASE WHEN m.status != 'dismissed' THEN CASE m.confidence WHEN 'high' THEN 3 WHEN 'medium' THEN 2 WHEN 'low' THEN 1 ELSE 0 END END) AS confidence_rank
            FROM alerts a
            LEFT JOIN matches m ON m.alert_id = a.id
            WHERE 1 = 1
    """
    params: list[Any] = []
    if search.strip():
        needle = f"%{search.strip().lower()}%"
        query += " AND (lower(a.title) LIKE ? OR lower(a.product_name) LIKE ? OR lower(a.hazard) LIKE ? OR lower(a.source_name) LIKE ?)"
        params.extend([needle, needle, needle, needle])
    if severity:
        query += " AND a.severity = ?"
        params.append(severity)
    query += """
            GROUP BY a.id
            ORDER BY a.alert_date DESC, a.created_at DESC
    """
    alerts = _dicts(
        connection.execute(query, params).fetchall()
    )
    confidence_lookup = {3: "high", 2: "medium", 1: "low", 0: "none"}
    for alert in alerts:
        alert["severity_label"] = SEVERITY_LABELS.get(alert["severity"], alert["severity"])
        alert["severity_tone"] = badge_tone(alert["severity"])
        alert["top_confidence"] = confidence_lookup.get(alert["confidence_rank"], "none")
        alert["top_confidence_tone"] = badge_tone("action_needed" if alert["top_confidence"] == "high" else "monitoring")
    return alerts


def get_alert_detail(connection, alert_id: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
    if not row:
        return None
    alert = dict(row)
    alert["severity_label"] = SEVERITY_LABELS.get(alert["severity"], alert["severity"])
    alert["severity_tone"] = badge_tone(alert["severity"])
    matches = _dicts(
        connection.execute(
            """
            SELECT m.*, p.title AS product_title, p.classification, p.vendor, c.id AS case_id, c.triage_status, c.priority
            FROM matches m
            JOIN products p ON p.id = m.product_id
            LEFT JOIN cases c ON c.alert_id = m.alert_id AND c.product_id = m.product_id
            WHERE m.alert_id = ?
            ORDER BY m.score DESC
            """,
            (alert_id,),
        ).fetchall()
    )
    summary = {"candidate": 0, "confirmed": 0, "dismissed": 0, "open_cases": 0}
    for match in matches:
        match["classification_label"] = CLASSIFICATION_LABELS.get(match["classification"], match["classification"])
        match["triage_status_label"] = CASE_STATUS_LABELS.get(match["triage_status"], match["triage_status"] or "Unopened")
        match["triage_status_tone"] = badge_tone(match["triage_status"] or "open")
        match["status_label"] = MATCH_STATUS_LABELS.get(match["status"], match["status"])
        match["status_tone"] = badge_tone(match["status"])
        match["confidence_tone"] = badge_tone("action_needed" if match["confidence"] == "high" else "monitoring")
        match["reviewed_at_short"] = match["reviewed_at"][:10] if match.get("reviewed_at") else ""
        if match["status"] in summary:
            summary[match["status"]] += 1
        if match.get("case_id") and match.get("triage_status") != "closed":
            summary["open_cases"] += 1
        if match["status"] == "dismissed":
            match["review_guidance"] = "False positive recorded"
        elif match["status"] == "confirmed":
            match["review_guidance"] = "Confirmed and routed into case workflow"
        elif match["confidence"] == "high":
            match["review_guidance"] = "High-confidence overlap. Review today."
        elif match["confidence"] == "medium":
            match["review_guidance"] = "Medium-confidence overlap. Confirm or dismiss after checking supplier and model details."
        else:
            match["review_guidance"] = "Low-confidence overlap. Dismiss if the model or seller does not match."
    return {"alert": alert, "matches": matches, "summary": summary}


def list_cases(connection, triage_status: str = "", product_id: str = "", search: str = "") -> list[dict[str, Any]]:
    query = """
        SELECT c.*, p.title AS product_title, p.classification, a.title AS alert_title, a.severity, a.source_name, a.alert_date
        FROM cases c
        JOIN products p ON p.id = c.product_id
        JOIN alerts a ON a.id = c.alert_id
        WHERE 1 = 1
    """
    params: list[Any] = []
    if triage_status:
        query += " AND c.triage_status = ?"
        params.append(triage_status)
    if product_id:
        query += " AND c.product_id = ?"
        params.append(product_id)
    if search.strip():
        needle = f"%{search.strip().lower()}%"
        query += " AND (lower(p.title) LIKE ? OR lower(a.title) LIKE ? OR lower(c.owner) LIKE ? OR lower(c.decision) LIKE ?)"
        params.extend([needle, needle, needle, needle])
    query += """
        ORDER BY
            CASE WHEN c.triage_status = 'closed' THEN 1 ELSE 0 END,
            CASE c.priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
            c.updated_at DESC
    """
    cases = _dicts(connection.execute(query, params).fetchall())
    for case in cases:
        case["classification_label"] = CLASSIFICATION_LABELS.get(case["classification"], case["classification"])
        case["triage_status_label"] = CASE_STATUS_LABELS.get(case["triage_status"], case["triage_status"])
        case["triage_status_tone"] = badge_tone(case["triage_status"])
        case["severity_label"] = SEVERITY_LABELS.get(case["severity"], case["severity"])
        case["severity_tone"] = badge_tone(case["severity"])
    return cases


def get_case_detail(connection, case_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT c.*, p.title AS product_title, p.classification, p.vendor, a.title AS alert_title, a.severity, a.hazard, a.source_url, a.alert_date
        FROM cases c
        JOIN products p ON p.id = c.product_id
        JOIN alerts a ON a.id = c.alert_id
        WHERE c.id = ?
        """,
        (case_id,),
    ).fetchone()
    if not row:
        return None
    case = dict(row)
    case["classification_label"] = CLASSIFICATION_LABELS.get(case["classification"], case["classification"])
    case["triage_status_label"] = CASE_STATUS_LABELS.get(case["triage_status"], case["triage_status"])
    case["triage_status_tone"] = badge_tone(case["triage_status"])
    case["severity_label"] = SEVERITY_LABELS.get(case["severity"], case["severity"])
    case["severity_tone"] = badge_tone(case["severity"])
    events = _dicts(
        connection.execute(
            "SELECT * FROM case_events WHERE case_id = ? ORDER BY created_at DESC",
            (case_id,),
        ).fetchall()
    )
    return {"case": case, "events": events}


def evidence_reminder_snapshot(connection, limit: int = 6) -> dict[str, Any]:
    rows = _dicts(
        connection.execute(
            """
            SELECT
                p.id AS product_id,
                p.title AS product_title,
                p.vendor,
                SUM(CASE WHEN e.status = 'missing' THEN 1 ELSE 0 END) AS missing_count,
                SUM(CASE WHEN e.status = 'stale' THEN 1 ELSE 0 END) AS stale_count
            FROM evidence_items e
            JOIN products p ON p.id = e.product_id
            WHERE e.status IN ('missing', 'stale')
            GROUP BY p.id, p.title, p.vendor
            ORDER BY missing_count DESC, stale_count DESC, p.title
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    )
    products: list[dict[str, Any]] = []
    total_items = 0
    for row in rows:
        requirement_rows = connection.execute(
            """
            SELECT title, status
            FROM evidence_items
            WHERE product_id = ? AND status IN ('missing', 'stale')
            ORDER BY CASE status WHEN 'missing' THEN 0 ELSE 1 END, title
            LIMIT 3
            """,
            (row["product_id"],),
        ).fetchall()
        requirements = [item["title"] for item in requirement_rows]
        total_items += int(row["missing_count"] or 0) + int(row["stale_count"] or 0)
        products.append(
            {
                **row,
                "requirement_preview": ", ".join(requirements),
            }
        )
    return {
        "products": products,
        "product_count": len(products),
        "item_count": total_items,
    }


def document_lifecycle_snapshot(connection, limit: int = 8) -> dict[str, Any]:
    documents = _hydrate_documents(
        connection.execute(
            """
            SELECT d.*, p.title AS product_title, p.vendor
            FROM documents d
            JOIN products p ON p.id = d.product_id
            ORDER BY COALESCE(d.valid_until, '9999-12-31T00:00:00Z'), d.updated_at DESC
            """
        ).fetchall()
    )
    expiring = [
        item
        for item in documents
        if item["lifecycle_code"] in {"expired", "expiring_soon"}
    ][:limit]
    return {
        "items": expiring,
        "count": len(expiring),
    }


def automation_snapshot(connection) -> dict[str, Any]:
    settings_map = list_settings(connection)
    effective_shopify = effective_shopify_config(connection)
    now = datetime.now(timezone.utc)

    catalog_enabled = _setting_enabled(settings_map.get("auto_catalog_sync_enabled"), False)
    catalog_interval_hours = _setting_int(settings_map.get("auto_catalog_sync_interval_hours"), 12)
    catalog_last_run = latest_sync_run(connection, "shopify-live", "catalog-sync")
    catalog_last_completed = _parse_iso_datetime((catalog_last_run or {}).get("completed_at") or (catalog_last_run or {}).get("started_at", ""))
    catalog_next_due = catalog_last_completed + timedelta(hours=catalog_interval_hours) if catalog_last_completed else None
    catalog_ready = settings_map.get("catalog_mode", "demo") == "shopify" and bool(
        effective_shopify["store_domain"] and (effective_shopify["token_present"] or effective_shopify["client_credentials_present"])
    )
    catalog_due_now = bool(catalog_enabled and catalog_ready and (catalog_next_due is None or catalog_next_due <= now))

    alert_enabled = _setting_enabled(settings_map.get("auto_alert_ingest_enabled"), False)
    alert_interval_hours = _setting_int(settings_map.get("auto_alert_ingest_interval_hours"), 24)
    cpsc_last_run = latest_sync_run(connection, "cpsc-live", "alert-ingest")
    canada_last_run = latest_sync_run(connection, "health-canada-live", "alert-ingest")
    alert_last_run = cpsc_last_run
    if canada_last_run and (
        not alert_last_run
        or (canada_last_run.get("completed_at") or canada_last_run.get("started_at", "")) > (alert_last_run.get("completed_at") or alert_last_run.get("started_at", ""))
    ):
        alert_last_run = canada_last_run
    alert_last_completed = _parse_iso_datetime((alert_last_run or {}).get("completed_at") or (alert_last_run or {}).get("started_at", ""))
    alert_next_due = alert_last_completed + timedelta(hours=alert_interval_hours) if alert_last_completed else None
    alert_ready = settings_map.get("live_cpsc_enabled", "yes") == "yes" or settings.enable_live_health_canada
    alert_due_now = bool(alert_enabled and alert_ready and (alert_next_due is None or alert_next_due <= now))

    reminder_frequency_days = _setting_int(settings_map.get("evidence_reminder_frequency_days"), 7)
    reminder_contact_email = settings_map.get("reminder_contact_email", "").strip() or settings.public_support_email

    return {
        "catalog_sync": {
            "enabled": catalog_enabled,
            "ready": catalog_ready,
            "interval_hours": catalog_interval_hours,
            "last_run": catalog_last_run,
            "next_due_at": catalog_next_due.isoformat().replace("+00:00", "Z") if catalog_next_due else "",
            "due_now": catalog_due_now,
        },
        "alert_ingest": {
            "enabled": alert_enabled,
            "ready": alert_ready,
            "interval_hours": alert_interval_hours,
            "last_run": alert_last_run,
            "next_due_at": alert_next_due.isoformat().replace("+00:00", "Z") if alert_next_due else "",
            "due_now": alert_due_now,
            "sources_label": "CPSC + Health Canada live feeds" if settings.enable_live_health_canada else "CPSC live feed",
        },
        "reminders": {
            "contact_email": reminder_contact_email,
            "frequency_days": reminder_frequency_days,
        },
    }


def _public_base_url_status() -> dict[str, Any]:
    host = (urlparse(settings.public_base_url).hostname or "").lower()
    live_ready = bool(host and host not in {"127.0.0.1", "localhost"} and not host.endswith("loca.lt"))
    return {
        "value": settings.public_base_url,
        "live_ready": live_ready,
        "notes": "Public host looks production-ready." if live_ready else "Set PUBLIC_BASE_URL to the permanent HTTPS host before launch.",
    }


def launch_readiness_snapshot(connection) -> dict[str, Any]:
    billing = get_billing_snapshot(connection)
    smtp = smtp_snapshot()
    current_users = list_workspace_users(connection)
    public_base_url = _public_base_url_status()
    using_postgres = DATABASE_BACKEND == "postgres"
    billing_ready = not settings.shopify_billing_required or bool(billing and billing["status"] == "active")
    billing_notes = "Shopify billing is active." if billing_ready else (
        billing["notes"] if billing else "No billing event recorded yet. Use the direct-invoice bridge until Shopify billing is active."
    )
    return {
        "public_base_url": public_base_url,
        "database": {
            "backend": DATABASE_BACKEND,
            "recommended_ready": using_postgres,
            "notes": "PostgreSQL configured." if using_postgres else "SQLite is still active. Move to NORTHSTAR_DATABASE_URL for the first paid pilot.",
            "database_url_present": bool(DATABASE_URL),
        },
        "secret_key": {
            "configured": settings.app_secret_key_configured,
            "notes": "Explicit APP_SECRET_KEY is set." if settings.app_secret_key_configured else "APP_SECRET_KEY is still ephemeral. Set a strong production secret before launch.",
        },
        "smtp": {
            **smtp,
            "notes": "SMTP is ready for real delivery." if smtp["configured"] else "SMTP is not configured yet. Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL.",
        },
        "billing": {
            "required": settings.shopify_billing_required,
            "ready": billing_ready,
            "notes": billing_notes,
        },
        "users": {
            "count": len(current_users),
            "ready": bool(current_users),
            "notes": "Named operator accounts exist." if current_users else "Create at least one workspace user so actions are attributable beyond shared basic auth.",
        },
        "uploads": {
            "path": str(UPLOAD_DIR),
            "ready": UPLOAD_DIR.exists() or UPLOAD_DIR.parent.exists(),
            "notes": "Upload path is configured.",
        },
        "backups": {
            "path": str(BACKUP_DIR),
            "ready": BACKUP_DIR.exists() or BACKUP_DIR.parent.exists(),
            "notes": "Backup directory is configured.",
        },
    }


def settings_snapshot(connection) -> dict[str, Any]:
    settings = list_settings(connection)
    sync_runs = _dicts(connection.execute("SELECT * FROM sync_runs ORDER BY started_at DESC LIMIT 10").fetchall())
    effective_shopify = effective_shopify_config(connection)
    shop_installs = list_shop_installs(connection)
    billing_snapshot = get_billing_snapshot(connection)
    automation = automation_snapshot(connection)
    evidence_reminders = evidence_reminder_snapshot(connection)
    document_lifecycle = document_lifecycle_snapshot(connection)
    workspace_users = list_workspace_users(connection)
    workspace_invites = list_workspace_invites(connection)
    launch_readiness = launch_readiness_snapshot(connection)
    contact_requests = _dicts(
        connection.execute(
            "SELECT * FROM contact_requests ORDER BY created_at DESC LIMIT 6"
        ).fetchall()
    )
    counts = {
        "products": int(connection.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]),
        "documents": int(connection.execute("SELECT COUNT(*) AS count FROM documents").fetchone()["count"]),
        "evidence_items": int(connection.execute("SELECT COUNT(*) AS count FROM evidence_items").fetchone()["count"]),
        "contact_requests": int(connection.execute("SELECT COUNT(*) AS count FROM contact_requests").fetchone()["count"]),
        "shop_installs": int(connection.execute("SELECT COUNT(*) AS count FROM shop_installs WHERE install_status = 'active'").fetchone()["count"]),
        "shopify_products": int(
            connection.execute("SELECT COUNT(*) AS count FROM products WHERE catalog_source = 'shopify' AND status != 'archived'").fetchone()[
                "count"
            ]
        ),
        "live_ready": int(bool(effective_shopify["store_domain"]) or settings.get("catalog_mode") == "demo"),
    }
    checklist, next_step = _pilot_checklist(connection, counts, effective_shopify, settings)
    return {
        "settings": settings,
        "sync_runs": sync_runs,
        "counts": counts,
        "effective_shopify": effective_shopify,
        "pilot_checklist": checklist,
        "next_step": next_step,
        "contact_requests": contact_requests,
        "shop_installs": shop_installs,
        "billing_snapshot": billing_snapshot,
        "automation": automation,
        "evidence_reminders": evidence_reminders,
        "document_lifecycle": document_lifecycle,
        "workspace_users": workspace_users,
        "workspace_invites": workspace_invites,
        "launch_readiness": launch_readiness,
    }


def effective_shopify_config(connection) -> dict[str, Any]:
    stored = list_settings(connection)
    installed_shop = latest_shop_install(connection)
    store_domain = settings.shopify_store_domain or stored.get("shopify_store_domain", "") or (installed_shop["shop_domain"] if installed_shop else "")
    api_version = stored.get("shopify_api_version") or settings.shopify_api_version
    token = settings.shopify_admin_token or stored.get("shopify_admin_token", "") or (installed_shop["access_token"] if installed_shop else "")
    token_expires_at = stored.get("shopify_admin_token_expires_at", "")
    client_id = settings.shopify_client_id or stored.get("shopify_client_id", "")
    client_secret = settings.shopify_client_secret or stored.get("shopify_client_secret", "")
    return {
        "store_domain": store_domain,
        "api_version": api_version,
        "token": token,
        "token_expires_at": token_expires_at,
        "token_present": bool(token),
        "client_id": client_id,
        "client_secret": client_secret,
        "client_id_present": bool(client_id),
        "client_secret_present": bool(client_secret),
        "client_credentials_present": bool(client_id and client_secret),
        "installed_shop_present": bool(installed_shop),
        "installed_shop_domain": installed_shop["shop_domain"] if installed_shop else "",
        "credential_mode": "token"
        if token
        else "client_credentials"
        if client_id and client_secret
        else "none",
        "source": "env"
        if settings.shopify_store_domain or settings.shopify_admin_token or settings.shopify_client_id or settings.shopify_client_secret
        else "settings",
    }


def create_oauth_state(connection, *, shop_domain: str, next_path: str, expires_at: str) -> str:
    state = secrets.token_urlsafe(24)
    connection.execute(
        """
        INSERT INTO oauth_states (state, shop_domain, next_path, created_at, expires_at, consumed_at)
        VALUES (?, ?, ?, ?, ?, NULL)
        """,
        (state, shop_domain, next_path, now_iso(), expires_at),
    )
    connection.commit()
    return state


def consume_oauth_state(connection, state: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM oauth_states WHERE state = ? AND consumed_at IS NULL",
        (state,),
    ).fetchone()
    if not row:
        return None
    connection.execute("UPDATE oauth_states SET consumed_at = ? WHERE state = ?", (now_iso(), state))
    connection.commit()
    return dict(row)


def upsert_shop_install(
    connection,
    *,
    shop_domain: str,
    access_token: str,
    scope: str,
    app_installation_id: str,
    launch_url: str,
    shop_name: str,
    shop_email: str,
    primary_domain_host: str,
    plan_name: str,
    is_partner_development: bool,
    is_shopify_plus: bool,
    install_status: str = "active",
) -> str:
    now = now_iso()
    existing = connection.execute("SELECT id FROM shop_installs WHERE shop_domain = ?", (shop_domain,)).fetchone()
    install_id = existing["id"] if existing else make_id("install")
    if existing:
        connection.execute(
            """
            UPDATE shop_installs
            SET access_token = ?, scope = ?, app_installation_id = ?, launch_url = ?, shop_name = ?, shop_email = ?,
                primary_domain_host = ?, plan_name = ?, is_partner_development = ?, is_shopify_plus = ?,
                install_status = ?, updated_at = ?, uninstalled_at = CASE WHEN ? = 'active' THEN NULL ELSE uninstalled_at END
            WHERE id = ?
            """,
            (
                access_token,
                scope,
                app_installation_id,
                launch_url,
                shop_name,
                shop_email,
                primary_domain_host,
                plan_name,
                1 if is_partner_development else 0,
                1 if is_shopify_plus else 0,
                install_status,
                now,
                install_status,
                install_id,
            ),
        )
    else:
        connection.execute(
            """
            INSERT INTO shop_installs (
                id, shop_domain, access_token, scope, app_installation_id, launch_url, shop_name, shop_email,
                primary_domain_host, plan_name, is_partner_development, is_shopify_plus, install_status,
                installed_at, updated_at, uninstalled_at, last_synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
            """,
            (
                install_id,
                shop_domain,
                access_token,
                scope,
                app_installation_id,
                launch_url,
                shop_name,
                shop_email,
                primary_domain_host,
                plan_name,
                1 if is_partner_development else 0,
                1 if is_shopify_plus else 0,
                install_status,
                now,
                now,
            ),
        )
    connection.commit()
    return install_id


def mark_shop_synced(connection, *, shop_domain: str) -> None:
    connection.execute(
        "UPDATE shop_installs SET last_synced_at = ?, updated_at = ? WHERE shop_domain = ?",
        (now_iso(), now_iso(), shop_domain),
    )
    connection.commit()


def mark_shop_uninstalled(connection, *, shop_domain: str) -> None:
    now = now_iso()
    connection.execute(
        "UPDATE shop_installs SET install_status = 'uninstalled', updated_at = ?, uninstalled_at = ? WHERE shop_domain = ?",
        (now, now, shop_domain),
    )
    connection.commit()


def latest_shop_install(connection) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT * FROM shop_installs
        WHERE install_status = 'active'
        ORDER BY updated_at DESC, installed_at DESC
        LIMIT 1
        """
    ).fetchone()
    return dict(row) if row else None


def list_shop_installs(connection) -> list[dict[str, Any]]:
    rows = _dicts(
        connection.execute(
            "SELECT * FROM shop_installs ORDER BY updated_at DESC, installed_at DESC LIMIT 10"
        ).fetchall()
    )
    for row in rows:
        row["is_partner_development"] = bool(row["is_partner_development"])
        row["is_shopify_plus"] = bool(row["is_shopify_plus"])
    return rows


def record_billing_event(
    connection,
    *,
    shop_domain: str,
    plan_name: str,
    status: str,
    confirmation_url: str = "",
    subscription_gid: str = "",
    test_mode: bool = False,
    notes: str = "",
) -> str:
    existing = connection.execute(
        "SELECT id FROM billing_events WHERE shop_domain = ? ORDER BY updated_at DESC LIMIT 1",
        (shop_domain,),
    ).fetchone()
    event_id = existing["id"] if existing else make_id("bill")
    now = now_iso()
    if existing:
        connection.execute(
            """
            UPDATE billing_events
            SET plan_name = ?, status = ?, confirmation_url = ?, subscription_gid = ?, test_mode = ?, notes = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                plan_name,
                status,
                confirmation_url or None,
                subscription_gid or None,
                1 if test_mode else 0,
                notes,
                now,
                event_id,
            ),
        )
    else:
        connection.execute(
            """
            INSERT INTO billing_events (
                id, shop_domain, plan_name, status, confirmation_url, subscription_gid, test_mode, notes, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                shop_domain,
                plan_name,
                status,
                confirmation_url or None,
                subscription_gid or None,
                1 if test_mode else 0,
                notes,
                now,
                now,
            ),
        )
    connection.commit()
    return event_id


def get_billing_snapshot(connection) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM billing_events ORDER BY updated_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None
    snapshot = dict(row)
    snapshot["test_mode"] = bool(snapshot["test_mode"])
    return snapshot


def add_document(
    connection,
    product_id: str,
    title: str,
    doc_type: str,
    issuer: str,
    status: str,
    issued_at: str,
    valid_until: str,
    verified_at: str,
    notes: str,
    source_url: str,
    requirement_code: str,
    file_name: str | None = None,
    file_bytes: bytes | None = None,
) -> str:
    doc_id = make_id("doc")
    stored_path = None
    if file_name and file_bytes is not None:
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        destination = UPLOAD_DIR / f"{doc_id}-{Path(file_name).name}"
        destination.write_bytes(file_bytes)
        stored_path = str(destination)
    now = now_iso()
    connection.execute(
        """
        INSERT INTO documents (
            id, product_id, title, doc_type, issuer, source_url, file_name, stored_path, status,
            issued_at, valid_until, verified_at, notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            doc_id,
            product_id,
            title,
            doc_type,
            issuer,
            source_url,
            file_name,
            stored_path,
            status,
            issued_at or None,
            valid_until or None,
            verified_at or None,
            notes,
            now,
            now,
        ),
    )
    if requirement_code:
        connection.execute(
            """
            UPDATE evidence_items
            SET document_id = ?, updated_at = ?
            WHERE product_id = ? AND requirement_code = ?
            """,
            (doc_id, now, product_id, requirement_code),
        )
    refresh_evidence_statuses(connection)
    connection.commit()
    return doc_id


def create_contact_request(
    connection,
    *,
    name: str,
    email: str,
    company: str,
    role_title: str,
    website: str,
    message: str,
    source_page: str,
) -> str:
    request_id = make_id("contact")
    now = now_iso()
    connection.execute(
        """
        INSERT INTO contact_requests (
            id, name, email, company, role_title, website, message, source_page, status, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_id,
            name.strip(),
            email.strip(),
            company.strip(),
            role_title.strip(),
            website.strip(),
            message.strip(),
            source_page.strip() or "contact",
            "new",
            now,
            now,
        ),
    )
    connection.commit()
    return request_id


def record_compliance_webhook(connection, *, topic: str, shop_domain: str, payload_json: str) -> str:
    event_id = make_id("webhook")
    connection.execute(
        """
        INSERT INTO compliance_webhook_events (id, topic, shop_domain, payload_json, received_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (event_id, topic, shop_domain, payload_json, now_iso()),
    )
    connection.commit()
    return event_id


def append_case_event(
    connection,
    case_id: str,
    event_type: str,
    actor_name: str,
    note: str,
    source_url: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO case_events (id, case_id, event_type, actor_name, note, source_url, metadata_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            make_id("evt"),
            case_id,
            event_type,
            actor_name,
            note,
            source_url or None,
            json.dumps(metadata or {}, sort_keys=True),
            now_iso(),
        ),
    )


def update_case(
    connection,
    case_id: str,
    triage_status: str,
    decision: str,
    priority: str,
    owner: str,
    last_action_summary: str,
) -> None:
    closed_at = now_iso() if triage_status == "closed" else None
    connection.execute(
        """
        UPDATE cases
        SET triage_status = ?, decision = ?, priority = ?, owner = ?, last_action_summary = ?, updated_at = ?, closed_at = ?
        WHERE id = ?
        """,
        (triage_status, decision, priority, owner, last_action_summary, now_iso(), closed_at, case_id),
    )
    connection.commit()


def list_workspace_users(connection) -> list[dict[str, Any]]:
    rows = _dicts(
        connection.execute(
            "SELECT id, email, full_name, role, status, created_at, updated_at, last_login_at FROM workspace_users WHERE status = 'active' ORDER BY full_name"
        ).fetchall()
    )
    return rows


def get_workspace_user(connection, user_id: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT id, email, full_name, role, status, created_at, updated_at, last_login_at FROM workspace_users WHERE id = ? AND status = 'active'",
        (user_id,),
    ).fetchone()
    return dict(row) if row else None


def _workspace_user_with_secret(connection, email: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM workspace_users WHERE lower(email) = ? AND status = 'active'",
        (email.strip().lower(),),
    ).fetchone()
    return dict(row) if row else None


def create_workspace_user(connection, *, email: str, full_name: str, role: str, password: str) -> str:
    now = now_iso()
    user_id = make_id("user")
    connection.execute(
        """
        INSERT INTO workspace_users (id, email, full_name, role, password_hash, status, created_at, updated_at, last_login_at)
        VALUES (?, ?, ?, ?, ?, 'active', ?, ?, NULL)
        """,
        (
            user_id,
            email.strip().lower(),
            full_name.strip(),
            role.strip() or "operator",
            hash_password(password),
            now,
            now,
        ),
    )
    connection.commit()
    return user_id


def update_workspace_user_password(connection, *, user_id: str, password: str) -> None:
    connection.execute(
        "UPDATE workspace_users SET password_hash = ?, updated_at = ? WHERE id = ?",
        (hash_password(password), now_iso(), user_id),
    )
    connection.commit()


def create_workspace_invite(connection, *, email: str, role: str, invited_by: str, note: str = "", expires_in_days: int = 7) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(24)
    invite = {
        "id": make_id("invite"),
        "token": token,
        "email": email.strip().lower(),
        "role": role.strip() or "operator",
        "invited_by": invited_by.strip() or "Northstar Safety",
        "note": note.strip(),
        "status": "pending",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "expires_at": (now + timedelta(days=expires_in_days)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    connection.execute(
        """
        INSERT INTO workspace_invites (id, token, email, role, invited_by, note, status, created_at, updated_at, expires_at, accepted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """,
        (
            invite["id"],
            invite["token"],
            invite["email"],
            invite["role"],
            invite["invited_by"],
            invite["note"],
            invite["status"],
            invite["created_at"],
            invite["updated_at"],
            invite["expires_at"],
        ),
    )
    connection.commit()
    return invite


def list_workspace_invites(connection) -> list[dict[str, Any]]:
    invites = _dicts(
        connection.execute(
            """
            SELECT *
            FROM workspace_invites
            WHERE status = 'pending'
            ORDER BY created_at DESC
            """
        ).fetchall()
    )
    now = datetime.now(timezone.utc)
    for invite in invites:
        expires_at = _parse_iso_datetime(invite["expires_at"])
        invite["is_expired"] = bool(expires_at and expires_at < now)
        invite["status_label"] = "Expired" if invite["is_expired"] else "Pending"
        invite["status_tone"] = "warning" if invite["is_expired"] else "neutral"
    return invites


def get_workspace_invite(connection, token: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM workspace_invites WHERE token = ?",
        (token,),
    ).fetchone()
    if not row:
        return None
    invite = dict(row)
    expires_at = _parse_iso_datetime(invite["expires_at"])
    invite["is_expired"] = bool(invite.get("accepted_at") or invite["status"] != "pending" or (expires_at and expires_at < datetime.now(timezone.utc)))
    return invite


def accept_workspace_invite(connection, *, token: str, full_name: str, password: str) -> dict[str, Any]:
    invite = get_workspace_invite(connection, token)
    if not invite:
        raise ValueError("Invite link is invalid.")
    if invite["is_expired"]:
        raise ValueError("Invite link has expired.")
    if _workspace_user_with_secret(connection, invite["email"]):
        raise ValueError("A workspace user with this email already exists.")
    user_id = create_workspace_user(connection, email=invite["email"], full_name=full_name, role=invite["role"], password=password)
    connection.execute(
        "UPDATE workspace_invites SET status = 'accepted', accepted_at = ?, updated_at = ? WHERE token = ?",
        (now_iso(), now_iso(), token),
    )
    connection.commit()
    return get_workspace_user(connection, user_id)


def create_password_reset_token(connection, *, email: str, expires_in_hours: int = 4) -> dict[str, Any] | None:
    user = _workspace_user_with_secret(connection, email)
    if not user:
        return None
    now = datetime.now(timezone.utc)
    token = secrets.token_urlsafe(24)
    payload = {
        "id": make_id("reset"),
        "token": token,
        "user_id": user["id"],
        "created_at": now_iso(),
        "expires_at": (now + timedelta(hours=expires_in_hours)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    connection.execute(
        """
        INSERT INTO password_reset_tokens (id, token, user_id, created_at, expires_at, used_at)
        VALUES (?, ?, ?, ?, ?, NULL)
        """,
        (payload["id"], payload["token"], payload["user_id"], payload["created_at"], payload["expires_at"]),
    )
    connection.commit()
    return payload


def get_password_reset_token(connection, token: str) -> dict[str, Any] | None:
    row = connection.execute(
        """
        SELECT prt.*, u.email, u.full_name
        FROM password_reset_tokens prt
        JOIN workspace_users u ON u.id = prt.user_id
        WHERE prt.token = ?
        """,
        (token,),
    ).fetchone()
    if not row:
        return None
    payload = dict(row)
    expires_at = _parse_iso_datetime(payload["expires_at"])
    payload["is_expired"] = bool(payload.get("used_at") or (expires_at and expires_at < datetime.now(timezone.utc)))
    return payload


def reset_workspace_user_password(connection, *, token: str, password: str) -> dict[str, Any]:
    reset_token = get_password_reset_token(connection, token)
    if not reset_token:
        raise ValueError("Reset link is invalid.")
    if reset_token["is_expired"]:
        raise ValueError("Reset link has expired.")
    update_workspace_user_password(connection, user_id=reset_token["user_id"], password=password)
    connection.execute(
        "UPDATE password_reset_tokens SET used_at = ? WHERE token = ?",
        (now_iso(), token),
    )
    connection.commit()
    return get_workspace_user(connection, reset_token["user_id"])


def change_workspace_user_password(connection, *, user_id: str, current_password: str, new_password: str) -> dict[str, Any]:
    row = connection.execute("SELECT * FROM workspace_users WHERE id = ? AND status = 'active'", (user_id,)).fetchone()
    if not row:
        raise ValueError("Workspace user was not found.")
    user = dict(row)
    if not verify_password(current_password, user["password_hash"]):
        raise ValueError("Current password is incorrect.")
    update_workspace_user_password(connection, user_id=user_id, password=new_password)
    return get_workspace_user(connection, user_id)


def authenticate_workspace_user(connection, *, email: str, password: str) -> dict[str, Any] | None:
    user = _workspace_user_with_secret(connection, email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    connection.execute(
        "UPDATE workspace_users SET last_login_at = ?, updated_at = ? WHERE id = ?",
        (now_iso(), now_iso(), user["id"]),
    )
    connection.commit()
    return get_workspace_user(connection, user["id"])
