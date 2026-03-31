from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4


CLASSIFICATION_LABELS = {
    "durable_infant_toddler": "Durable infant / toddler",
    "childrens_toy": "Children's toy",
    "childrens_feeding": "Children's feeding",
    "battery_childrens": "Battery-powered children's item",
    "general_childrens": "General children's product",
}

CASE_STATUS_LABELS = {
    "open": "Open",
    "under_review": "Under review",
    "monitoring": "Monitoring",
    "action_needed": "Action needed",
    "closed": "Closed",
}

MATCH_STATUS_LABELS = {
    "candidate": "Candidate",
    "confirmed": "Confirmed",
    "dismissed": "Dismissed",
}

DOCUMENT_STATUS_LABELS = {
    "verified": "Verified",
    "pending_review": "Pending review",
    "supplier_sent": "Supplier sent",
    "expired": "Expired",
}

EVIDENCE_STATUS_LABELS = {
    "current": "Current",
    "missing": "Missing",
    "stale": "Stale",
    "review": "Needs review",
}

SEVERITY_LABELS = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}

REQUIREMENTS_BY_CLASS = {
    "durable_infant_toddler": [
        ("cpc", "Children's Product Certificate", "Current CPC tied to the exact SKU family."),
        ("lab_report", "Accredited lab report", "Recent test report covering applicable CPSC rules."),
        ("tracking_label", "Tracking label proof", "Photo or artwork proving lot/date traceability."),
        ("registration_card", "Durable infant registration proof", "Consumer registration card or digital equivalent."),
        ("instruction_manual", "Instruction manual", "Current instructions and warnings used in market."),
        ("supplier_packet", "Supplier conformity packet", "Factory declaration, BOM, and component attestations."),
    ],
    "childrens_toy": [
        ("cpc", "Children's Product Certificate", "Current CPC tied to the product family."),
        ("lab_report", "ASTM / CPSC lab report", "Recent toy testing results."),
        ("tracking_label", "Tracking label proof", "Photo or artwork proving traceability."),
        ("age_grade", "Age grading rationale", "Documented intended age and hazard review."),
        ("supplier_packet", "Supplier conformity packet", "Factory declaration and material attestations."),
    ],
    "childrens_feeding": [
        ("cpc", "Children's Product Certificate", "Current CPC for the feeding set."),
        ("lab_report", "Accredited lab report", "Lead, phthalates, and applicable material testing."),
        ("tracking_label", "Tracking label proof", "Photo or artwork proving traceability."),
        ("food_contact", "Food-contact declaration", "Supplier declaration for food-contact materials."),
        ("supplier_packet", "Supplier conformity packet", "Factory declaration and material attestations."),
    ],
    "battery_childrens": [
        ("cpc", "Children's Product Certificate", "Current CPC for the children's item."),
        ("lab_report", "Accredited lab report", "Recent testing for applicable children's rules."),
        ("tracking_label", "Tracking label proof", "Photo or artwork proving traceability."),
        ("battery_review", "Battery safety assessment", "Overheating, compartment, and warning review."),
        ("warning_art", "Warning label artwork", "Current warning copy for battery and heat hazards."),
        ("supplier_packet", "Supplier conformity packet", "Factory declaration and component attestations."),
    ],
    "general_childrens": [
        ("cpc", "Children's Product Certificate", "Current CPC for the product family."),
        ("lab_report", "Accredited lab report", "Recent testing results."),
        ("tracking_label", "Tracking label proof", "Photo or artwork proving traceability."),
        ("supplier_packet", "Supplier conformity packet", "Factory declaration and material attestations."),
    ],
}


def now_utc() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def now_iso() -> str:
    return now_utc().isoformat().replace("+00:00", "Z")


def iso_days_from_now(days: int) -> str:
    return (now_utc() + timedelta(days=days)).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def tokenise(*values: str) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        if not value:
            continue
        tokens.update(re.findall(r"[a-z0-9]+", value.lower()))
    return {token for token in tokens if len(token) > 2}


def parse_tags(raw_tags: Any) -> list[str]:
    if isinstance(raw_tags, list):
        return [str(tag).strip() for tag in raw_tags if str(tag).strip()]
    if raw_tags is None:
        return []
    return [part.strip() for part in str(raw_tags).split(",") if part.strip()]


def classify_product(title: str, product_type: str, tags: list[str]) -> str:
    haystack = " ".join([title, product_type, " ".join(tags)]).lower()
    if any(keyword in haystack for keyword in ("high chair", "bassinet", "carrier", "walker", "bath seat", "crib")):
        return "durable_infant_toddler"
    if any(keyword in haystack for keyword in ("toy", "sorter", "stacker", "teether")):
        return "childrens_toy"
    if any(keyword in haystack for keyword in ("feeding", "bowl", "plate", "spoon", "cup", "silicone bib")):
        return "childrens_feeding"
    if any(keyword in haystack for keyword in ("battery", "night light", "plush", "electronic", "sound machine")):
        return "battery_childrens"
    return "general_childrens"


def build_evidence_template(classification: str) -> list[dict[str, str]]:
    return [
        {"requirement_code": code, "title": title, "description": description}
        for code, title, description in REQUIREMENTS_BY_CLASS.get(
            classification,
            REQUIREMENTS_BY_CLASS["general_childrens"],
        )
    ]


def badge_tone(status: str) -> str:
    mapping = {
        "current": "success",
        "verified": "success",
        "open": "warning",
        "under_review": "warning",
        "monitoring": "info",
        "action_needed": "danger",
        "closed": "neutral",
        "missing": "danger",
        "stale": "warning",
        "review": "warning",
        "candidate": "info",
        "confirmed": "success",
        "dismissed": "neutral",
        "critical": "danger",
        "high": "danger",
        "medium": "warning",
        "low": "info",
        "pending_review": "warning",
        "supplier_sent": "info",
        "expired": "danger",
    }
    return mapping.get(status, "neutral")


def coalesce_date(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def derive_evidence_status(document: dict[str, Any] | None, stale_after: str | None) -> str:
    if not document:
        return "missing"
    valid_until = coalesce_date(document.get("valid_until"))
    verified_at = coalesce_date(document.get("verified_at"))
    stale_deadline = coalesce_date(stale_after)
    now = now_utc()
    if valid_until and valid_until < now:
        return "stale"
    if stale_deadline and stale_deadline < now:
        return "stale"
    if verified_at and verified_at < now - timedelta(days=365):
        return "stale"
    if document.get("status") == "pending_review":
        return "review"
    return "current"


def evidence_rollup(evidence_items: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"total": len(evidence_items), "current": 0, "missing": 0, "stale": 0, "review": 0}
    for item in evidence_items:
        summary[item["status"]] = summary.get(item["status"], 0) + 1
    return summary


def case_default_from_confidence(confidence: str, severity: str) -> tuple[str, str, str]:
    if confidence == "high":
        return ("action_needed", "Immediate containment", "high")
    if confidence == "medium":
        return ("under_review", "Investigate supplier and lots", "medium")
    return ("monitoring", "Track signal", "low")


def compute_match(product: dict[str, Any], alert: dict[str, Any]) -> dict[str, Any]:
    product_text = " ".join([product["title"], product["vendor"], product["product_type"], " ".join(product["tags"])]).lower()
    alert_text = " ".join([alert["title"], alert["product_name"], alert["hazard"], alert["description"]]).lower()
    product_tokens = tokenise(product["title"], product["vendor"], product["product_type"], " ".join(product["tags"]))
    alert_tokens = tokenise(alert["title"], alert["product_name"], alert["hazard"], alert["description"])
    overlap = product_tokens & alert_tokens
    score = 0.0
    reasons: list[str] = []

    if product["vendor"].lower() in alert_text:
        score += 0.35
        reasons.append("brand mention")
    if overlap:
        score += min(0.35, 0.07 * len(overlap))
        reasons.append(f"shared terms: {', '.join(sorted(list(overlap))[:5])}")

    exact_category_overlap = {
        "high chair": "high-chair type overlap",
        "carrier": "carrier type overlap",
        "bassinet": "bassinet type overlap",
        "bath seat": "bath-seat type overlap",
        "walker": "walker type overlap",
        "shape sorter": "shape-sorter type overlap",
        "plush": "plush type overlap",
    }
    for phrase, label in exact_category_overlap.items():
        if phrase in product_text and phrase in alert_text:
            score += 0.35 if phrase != "plush" else 0.2
            reasons.append(label)

    if product["classification"] == "durable_infant_toddler" and any(
        phrase in product_text and phrase in alert_text
        for phrase in ("high chair", "bassinet", "carrier", "bath seat", "walker")
    ):
        score += 0.15
        reasons.append("durable infant product-type family")
    if product["classification"] == "battery_childrens" and "battery" in product_text and "battery" in alert_text:
        score += 0.2
        reasons.append("battery hazard overlap")
    if product["classification"] == "childrens_toy" and "toy" in product_text and "toy" in alert_text:
        score += 0.15
        reasons.append("toy category overlap")
    score = min(score, 0.98)

    if score >= 0.8:
        confidence = "high"
    elif score >= 0.55:
        confidence = "medium"
    elif score >= 0.35:
        confidence = "low"
    else:
        confidence = "none"

    return {
        "score": round(score, 2),
        "confidence": confidence,
        "rationale": "; ".join(reasons) if reasons else "No practical overlap",
    }


def make_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10]}"
