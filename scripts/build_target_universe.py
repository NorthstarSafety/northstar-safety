from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover
    Workbook = None


ROOT = Path(__file__).resolve().parents[1]
SPREADSHEET_DIR = ROOT / "output" / "spreadsheet"
SCRAPE_DIR = ROOT / "output" / "scrapes"
DOCS_DIR = ROOT / "docs"


BRAND_FIELDS = [
    "segment",
    "tier",
    "fit_score",
    "company",
    "website",
    "category",
    "likely_platform",
    "geography",
    "contact_paths",
    "best_channel",
    "source_pools",
    "source_note",
    "trigger_reason",
    "reachability",
    "outreach_status",
    "last_touch_date",
    "next_step",
]

PARTNER_FIELDS = [
    "segment",
    "tier",
    "fit_score",
    "company",
    "website",
    "category",
    "likely_platform",
    "geography",
    "contact_paths",
    "best_channel",
    "source_pools",
    "source_note",
    "trigger_reason",
    "reachability",
    "outreach_status",
    "last_touch_date",
    "next_step",
]

ACTIVITY_FIELDS = [
    "date",
    "lane",
    "priority_rank",
    "company",
    "channel",
    "contact_route",
    "touch_type",
    "status",
    "owner",
    "notes",
]

NEXT25_FIELDS = [
    "priority_rank",
    "segment",
    "tier",
    "fit_score",
    "company",
    "category",
    "website",
    "contact_paths",
    "best_channel",
    "trigger_reason",
    "outreach_status",
    "next_step",
]


NEW_ACTIVITY_ROWS = [
    {
        "date": "2026-04-08 16:42 MT",
        "lane": "Partner outreach",
        "priority_rank": "",
        "company": "Swanky Agency",
        "channel": "Email",
        "contact_route": "humans@swankyagency.com",
        "touch_type": "touch_1",
        "status": "sent",
        "owner": "Founder",
        "notes": "Workspace founder-domain partner note sent with a simple shared-client / forwardable-blurb ask.",
    },
    {
        "date": "2026-04-08 16:45 MT",
        "lane": "Partner outreach",
        "priority_rank": "",
        "company": "1Digital Agency",
        "channel": "Email",
        "contact_route": "info@1digitalagency.com",
        "touch_type": "touch_1",
        "status": "sent",
        "owner": "Founder",
        "notes": "Workspace founder-domain partner note sent with a concise intro-call / one-forwardable-blurb ask.",
    },
    {
        "date": "2026-04-08 16:48 MT",
        "lane": "Partner outreach",
        "priority_rank": "",
        "company": "Modern Testing Services",
        "channel": "Email",
        "contact_route": "mike.hassler@mtsus.com",
        "touch_type": "touch_1",
        "status": "sent",
        "owner": "Founder",
        "notes": "Founder-domain partner outreach sent positioning Northstar as the operational layer after testing and compliance work.",
    },
    {
        "date": "2026-04-08 16:51 MT",
        "lane": "Partner outreach",
        "priority_rank": "",
        "company": "DECA",
        "channel": "Email",
        "contact_route": "j.blankenship@deca-inc.net",
        "touch_type": "touch_1",
        "status": "sent",
        "owner": "Founder",
        "notes": "Founder-domain compliance-adjacent outreach sent with a shared-client pilot / intro-call ask.",
    },
    {
        "date": "2026-04-08 16:54 MT",
        "lane": "Partner outreach",
        "priority_rank": "",
        "company": "Baby Safety Alliance",
        "channel": "Email",
        "contact_route": "info@babysafetyalliance.org",
        "touch_type": "touch_1",
        "status": "sent",
        "owner": "Founder",
        "notes": "Founder-domain association note sent asking for the right member-services or service-provider contact for a short forwardable blurb.",
    },
    {
        "date": "2026-04-08 16:58 MT",
        "lane": "Brand outreach",
        "priority_rank": "",
        "company": "Snuggle Me Organic",
        "channel": "Email",
        "contact_route": "care@snugglemeorganic.com",
        "touch_type": "touch_1",
        "status": "sent",
        "owner": "Founder",
        "notes": "Founder-domain direct brand note sent with a short SKU-evidence angle and a 15-minute ask.",
    },
    {
        "date": "2026-04-08 17:02 MT",
        "lane": "Brand outreach",
        "priority_rank": "",
        "company": "Stokke",
        "channel": "Email",
        "contact_route": "partnerships@stokke.com",
        "touch_type": "routed_followup",
        "status": "sent",
        "owner": "Founder",
        "notes": "Founder-domain routed follow-up sent after the Stokke site chat pointed Northstar to partnerships@stokke.com.",
    },
    {
        "date": "2026-04-08 17:08 MT",
        "lane": "Brand outreach",
        "priority_rank": "",
        "company": "Cradlewise",
        "channel": "Email",
        "contact_route": "support@cradlewise.com",
        "touch_type": "touch_2",
        "status": "sent",
        "owner": "Founder",
        "notes": "Founder-domain email follow-up sent after the Intercom touch, tied to bassinet-category documentation and alert-review burden.",
    },
    {
        "date": "2026-04-08 17:36 MT",
        "lane": "Partner outreach",
        "priority_rank": "",
        "company": "Eastside Co",
        "channel": "Email",
        "contact_route": "info@eastsideco.com",
        "touch_type": "touch_1",
        "status": "sent",
        "owner": "Founder",
        "notes": "Founder-domain partner outreach sent directly to the routed team inbox instead of stopping at the contact page.",
    },
]


EXCLUDED_NAME_PATTERNS = [
    r"tiktok",
    r"walmart marketplace",
    r"new product showcase",
    r"supply chain",
    r"fulfillment",
    r"payments",
    r"registry",
    r"destination sitters",
    r"showcase",
    r"sitters",
]

PARTNER_NAME_PATTERNS = [
    r"testing",
    r"compliance",
    r"safety alliance",
    r"agency",
    r"solutions",
    r"fulfillment",
    r"payments",
    r"deca",
    r"qima",
    r"bureau veritas",
    r"intertek",
    r"eurofins",
    r"tuv",
    r"ul solutions",
]

HIGH_FIT_KEYWORDS = {
    "car seat": ("Car seats / travel safety", 26),
    "stroller": ("Strollers / travel systems", 24),
    "juvenile": ("Juvenile gear", 24),
    "crib": ("Cribs / bassinets / nursery furniture", 22),
    "bassinet": ("Cribs / bassinets / nursery furniture", 22),
    "carrier": ("Carriers / on-body gear", 22),
    "feeding": ("Feeding / bottles / mealtime", 20),
    "baby monitor": ("Monitoring / smart nursery", 20),
    "furniture": ("Nursery furniture", 18),
    "sleep": ("Sleep / swaddle / nursery textiles", 18),
    "bath": ("Bath / care", 16),
    "monitor": ("Monitoring / smart nursery", 18),
}


def normalize(name: str) -> str:
    lowered = name.lower()
    lowered = lowered.replace("&", "and")
    lowered = re.sub(r"[^a-z0-9]+", "", lowered)
    return lowered


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def category_from_text(text: str) -> tuple[str, int]:
    lowered = text.lower()
    best_category = "General baby / juvenile products"
    bonus = 8
    for keyword, (category, score_bonus) in HIGH_FIT_KEYWORDS.items():
        if keyword in lowered:
            return category, score_bonus
    if any(token in lowered for token in ("baby", "juvenile", "nursery", "infant", "kids", "child")):
        best_category = "General baby / juvenile products"
        bonus = 10
    if any(token in lowered for token in ("apparel", "swaddle", "blanket", "textile", "softgoods")):
        best_category = "Soft goods / apparel / nursery textiles"
        bonus = max(bonus, 12)
    if any(token in lowered for token in ("toy", "play", "education")):
        best_category = "Toys / play / educational"
        bonus = max(bonus, 10)
    return best_category, bonus


def trigger_from_category(category: str) -> str:
    if "Car seats" in category or "Strollers" in category:
        return "High SKU-evidence and alert-review burden in a high-scrutiny juvenile category."
    if "Cribs" in category or "Nursery" in category:
        return "Retailer documentation, evidence retrieval, and renewal tracking are likely spread across many nursery SKUs."
    if "Carriers" in category:
        return "Carrier and softgoods lines need reusable supplier/testing evidence and cleaner case tracking."
    if "Feeding" in category:
        return "Feeding products create repeat document retrieval, materials evidence, and official alert-review work."
    if "Monitoring" in category:
        return "Connected or electronics-adjacent products add support, documentation, and issue-review complexity."
    if "Soft goods" in category:
        return "Softgoods still create recurring materials, testing, and retailer-readiness document pressure."
    return "Child-product trust and evidence workflow burden are likely still spread across files, inboxes, and follow-up notes."


def likely_platform(website: str, company: str) -> str:
    if website:
        if any(host in website for host in ("shopify", "myshopify")):
            return "confirmed_shopify"
        return "likely_shopify_or_dtc"
    if any(token in company.lower() for token in ("baby", "kids", "juvenile", "nursery")):
        return "likely_dtc"
    return "unknown"


def best_channel(contact_paths: str) -> str:
    if not contact_paths:
        return "research"
    if "@" in contact_paths:
        return "team_email"
    if "zendesk" in contact_paths.lower():
        return "zendesk_form"
    if "gorgias" in contact_paths.lower():
        return "gorgias_form"
    if "hubspot" in contact_paths.lower():
        return "hubspot_form"
    if "sendhark" in contact_paths.lower():
        return "sendhark_form"
    if "intercom" in contact_paths.lower() or "chat" in contact_paths.lower():
        return "chat_widget"
    if contact_paths.startswith("http"):
        return "contact_form"
    return "research"


def reachability(contact_paths: str) -> str:
    return "reachable_now" if contact_paths else "route_research_needed"


def should_exclude_brand(name: str) -> bool:
    lowered = name.lower()
    return any(re.search(pattern, lowered) for pattern in EXCLUDED_NAME_PATTERNS)


def looks_like_partner(name: str) -> bool:
    lowered = name.lower()
    return any(re.search(pattern, lowered) for pattern in PARTNER_NAME_PATTERNS)


def build_existing_indexes() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    brands = read_csv(SPREADSHEET_DIR / "northstar_phase21_brands.csv")
    partners = read_csv(SPREADSHEET_DIR / "northstar_phase21_partners.csv")
    return (
        {normalize(row["company"]): row for row in brands},
        {normalize(row["company"]): row for row in partners},
    )


def merged_activity() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name in (
        "northstar_phase21_activity.csv",
        "northstar_phase22_activity.csv",
        "northstar_phase23_activity.csv",
    ):
        rows.extend(read_csv(SPREADSHEET_DIR / name))
    rows.extend(NEW_ACTIVITY_ROWS)
    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[dict[str, str]] = []
    for row in rows:
        key = (
            row.get("date", ""),
            normalize(row.get("company", "")),
            row.get("contact_route", ""),
            row.get("touch_type", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    deduped.sort(key=lambda row: (row.get("date", ""), row.get("company", "")))
    return deduped


def build_last_touch_index(activity_rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    last_touch: dict[str, dict[str, str]] = {}
    for row in activity_rows:
        last_touch[normalize(row["company"])] = row
    return last_touch


def infer_fit_score(company: str, category: str, source_pools: str, contact_paths: str, status: str) -> int:
    score = 45
    category_bonus = category_from_text(f"{company} {category}")[1]
    score += category_bonus
    if "ABC Kids Expo" in source_pools:
        score += 8
    if contact_paths:
        score += 10
    if status in {"sent", "verification_pending", "routed_to_team_email"}:
        score += 8
    if "Testing / compliance" in category or "Shopify agency" in category or "Industry association" in category:
        score = min(score, 86)
    return min(score, 99)


def tier_from_score(score: int, segment: str) -> str:
    if segment == "partner_referral":
        return "Partner Tier"
    if score >= 82:
        return "Tier 1"
    if score >= 68:
        return "Tier 2"
    return "Tier 3"


def load_abc_brands() -> list[dict[str, str]]:
    with (SCRAPE_DIR / "abc_kids_expo_2026_exhibitors.json").open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def build_brand_universe(
    existing_brands: dict[str, dict[str, str]],
    last_touch: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    scraped = load_abc_brands()
    records: dict[str, dict[str, str]] = {}

    for row in scraped:
        company = row["name"].strip()
        key = normalize(company)
        if not company or should_exclude_brand(company) or looks_like_partner(company):
            continue
        category, _ = category_from_text(company)
        records[key] = {
            "segment": "direct_brand",
            "company": company,
            "website": "",
            "category": category,
            "likely_platform": likely_platform("", company),
            "geography": "",
            "contact_paths": "",
            "best_channel": "research",
            "source_pools": "ABC Kids Expo 2026 exhibitor list",
            "source_note": row["details_url"],
            "trigger_reason": trigger_from_category(category),
            "reachability": "route_research_needed",
            "outreach_status": "unworked",
            "last_touch_date": "",
            "next_step": "Research external site and best contact path before outreach.",
        }

    for key, row in existing_brands.items():
        company = row["company"]
        category, _ = category_from_text(f"{company} {row.get('fit_reason', '')}")
        existing_source = row.get("source_pool", "")
        source_note = row.get("source_note", "")
        trigger = row.get("fit_reason", "").strip() or trigger_from_category(category)
        next_step = row.get("next_step", "").strip() or "Prepare next controlled wave."
        status = row.get("status", "unworked")
        combined = records.get(
            key,
            {
                "segment": "direct_brand",
                "company": company,
                "website": "",
                "category": category,
                "likely_platform": likely_platform(row.get("website", ""), company),
                "geography": "",
                "contact_paths": "",
                "best_channel": "research",
                "source_pools": existing_source,
                "source_note": source_note,
                "trigger_reason": trigger,
                "reachability": "route_research_needed",
                "outreach_status": status,
                "last_touch_date": "",
                "next_step": next_step,
            },
        )
        combined["website"] = row.get("website", combined["website"])
        combined["category"] = category
        combined["likely_platform"] = likely_platform(combined["website"], company)
        combined["contact_paths"] = row.get("contact_route", combined["contact_paths"])
        combined["best_channel"] = best_channel(combined["contact_paths"])
        source_parts = [part for part in {combined["source_pools"], existing_source} if part]
        combined["source_pools"] = "; ".join(sorted(source_parts))
        note_parts = [part for part in {combined["source_note"], source_note} if part]
        combined["source_note"] = " | ".join(sorted(note_parts))
        combined["trigger_reason"] = trigger
        combined["reachability"] = reachability(combined["contact_paths"])
        combined["outreach_status"] = status
        combined["next_step"] = next_step
        records[key] = combined

    rows: list[dict[str, str]] = []
    for key, row in records.items():
        touch = last_touch.get(key)
        if touch:
            row["outreach_status"] = touch["status"]
            row["last_touch_date"] = touch["date"]
            if row["next_step"].lower().startswith("prepare first-wave"):
                row["next_step"] = "Wait for reply or send a tighter follow-up after a reasonable delay."
        score = infer_fit_score(
            row["company"],
            row["category"],
            row["source_pools"],
            row["contact_paths"],
            row["outreach_status"],
        )
        row["fit_score"] = str(score)
        row["tier"] = tier_from_score(score, row["segment"])
        rows.append(row)

    rows.sort(
        key=lambda row: (
            {"Tier 1": 0, "Tier 2": 1, "Tier 3": 2}.get(row["tier"], 3),
            -int(row["fit_score"]),
            row["company"].lower(),
        )
    )
    return rows


def build_partner_universe(
    existing_partners: dict[str, dict[str, str]],
    last_touch: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for key, row in existing_partners.items():
        company = row["company"]
        touch = last_touch.get(key)
        status = touch["status"] if touch else row.get("status", "unworked")
        last_touch_date = touch["date"] if touch else ""
        source_pools = row.get("source_pool", "")
        trigger_reason = row.get("fit_reason", "").strip() or "Already trusted by merchants who may need a cleaner evidence, alert-review, and case workflow."
        contact_paths = row.get("contact_route", "")
        score = infer_fit_score(company, row.get("category", ""), source_pools, contact_paths, status)
        next_step = row.get("next_step", "").strip() or "Prepare first partner touch."
        if touch and next_step.lower().startswith("prepare"):
            next_step = "Wait for reply or send a tighter partner follow-up in the next wave."
        rows.append(
            {
                "segment": "partner_referral",
                "tier": "Partner Tier",
                "fit_score": str(score),
                "company": company,
                "website": row.get("website", ""),
                "category": row.get("category", ""),
                "likely_platform": "partner_channel",
                "geography": "",
                "contact_paths": contact_paths,
                "best_channel": best_channel(contact_paths),
                "source_pools": source_pools,
                "source_note": row.get("source_pool", ""),
                "trigger_reason": trigger_reason,
                "reachability": reachability(contact_paths),
                "outreach_status": status,
                "last_touch_date": last_touch_date,
                "next_step": next_step,
            }
        )
    rows.sort(key=lambda row: (-int(row["fit_score"]), row["company"].lower()))
    return rows


def build_next25(brands: list[dict[str, str]], partners: list[dict[str, str]]) -> list[dict[str, str]]:
    combined = []
    for row in brands + partners:
        if row["reachability"] != "reachable_now":
            continue
        if row["outreach_status"] in {"sent", "verification_pending", "routed_to_team_email", "contacted"}:
            continue
        combined.append(row)
    combined.sort(
        key=lambda row: (
            {"Tier 1": 0, "Partner Tier": 1, "Tier 2": 2, "Tier 3": 3}.get(row["tier"], 4),
            -int(row["fit_score"]),
            row["company"].lower(),
        )
    )
    next_rows: list[dict[str, str]] = []
    for rank, row in enumerate(combined[:25], start=1):
        next_rows.append(
            {
                "priority_rank": str(rank),
                "segment": row["segment"],
                "tier": row["tier"],
                "fit_score": row["fit_score"],
                "company": row["company"],
                "category": row["category"],
                "website": row["website"],
                "contact_paths": row["contact_paths"],
                "best_channel": row["best_channel"],
                "trigger_reason": row["trigger_reason"],
                "outreach_status": row["outreach_status"],
                "next_step": row["next_step"],
            }
        )
    return next_rows


def build_workbook(
    brands: list[dict[str, str]],
    partners: list[dict[str, str]],
    activity: list[dict[str, str]],
    next25: list[dict[str, str]],
) -> None:
    if Workbook is None:
        return
    workbook = Workbook()
    default_sheet = workbook.active
    workbook.remove(default_sheet)

    def append_sheet(name: str, rows: list[dict[str, str]], fields: list[str]) -> None:
        sheet = workbook.create_sheet(title=name)
        sheet.append(fields)
        for row in rows:
            sheet.append([row.get(field, "") for field in fields])

    append_sheet("brands", brands, BRAND_FIELDS)
    append_sheet("partners", partners, PARTNER_FIELDS)
    append_sheet("activity", activity, ACTIVITY_FIELDS)
    append_sheet("next25", next25, NEXT25_FIELDS)
    workbook.save(SPREADSHEET_DIR / "northstar_target_universe.xlsx")


def write_memo(
    brands: list[dict[str, str]],
    partners: list[dict[str, str]],
    activity: list[dict[str, str]],
    next25: list[dict[str, str]],
) -> None:
    total_brands = len(brands)
    reachable_brands = sum(1 for row in brands if row["reachability"] == "reachable_now")
    contacted_brands = sum(1 for row in brands if row["outreach_status"] not in {"unworked", "new"})
    total_partners = len(partners)
    reachable_partners = sum(1 for row in partners if row["reachability"] == "reachable_now")
    contacted_partners = sum(1 for row in partners if row["outreach_status"] not in {"unworked", "new"})
    routed_addresses = sorted(
        {
            row["contact_route"]
            for row in activity
            if "@" in row.get("contact_route", "")
        }
    )
    sent_count = sum(1 for row in activity if row["status"] == "sent")
    replies = [row for row in activity if "reply" in row["status"]]
    memo = f"""# Northstar Target Universe Memo

Date: 2026-04-08

## Scope

This pass builds the broadest practical reachable Northstar universe from:

- ABC Kids Expo 2026 exhibitor list
- prior Northstar phase 21/22/23 brand and partner sheets
- prior activity logs
- live Workspace outreach completed on April 8, 2026

It does **not** claim every baby seller in existence. It is the broadest practical, deduplicated, founder-usable universe assembled from current source pools and current contactability.

## Totals

- Direct brand universe: {total_brands}
- Direct brands reachable now: {reachable_brands}
- Direct brands already contacted/logged: {contacted_brands}
- Partner/referral universe: {total_partners}
- Partners reachable now: {reachable_partners}
- Partners already contacted/logged: {contacted_partners}
- Logged outreach/activity rows in the merged file: {len(activity)}
- Logged sends in the merged file: {sent_count}

## Best source pools

- ABC Kids Expo 2026 is the strongest raw prospect universe.
- Existing Northstar phase 21 brand sheet is the strongest already-routed direct-contact subset.
- Existing Northstar phase 21 partner sheet is still the cleanest partner/referral lane.

## Best channels so far

- Routed team email from live chat or support systems is still the highest-signal path.
- Direct Workspace founder-domain team email is stronger than generic contact-form copy when a real address exists.
- Structured contact forms remain useful, but they should serve the ranked reachable set instead of being the whole strategy.

## Replies and demos

- Human replies logged from this master-universe pass: {len(replies)}
- Booked demos from this pass: 0

## Routed addresses already surfaced

{chr(10).join(f"- {address}" for address in routed_addresses[:20])}

## Next push

- Work the ranked next-25 file from the top rather than reopening broad weak-fit blasting.
- Prioritize Tier 1 brands with real contact paths and Partner Tier accounts with real team emails first.
- Keep using the Workspace sender only.
- Continue controlled waves instead of one generic blast.
"""
    (DOCS_DIR / "northstar-target-universe-memo-2026-04-08.md").write_text(memo, encoding="utf-8")


def main() -> None:
    existing_brands, existing_partners = build_existing_indexes()
    activity = merged_activity()
    last_touch = build_last_touch_index(activity)
    brands = build_brand_universe(existing_brands, last_touch)
    partners = build_partner_universe(existing_partners, last_touch)
    next25 = build_next25(brands, partners)

    write_csv(SPREADSHEET_DIR / "northstar_target_universe_master.csv", BRAND_FIELDS, brands)
    write_csv(SPREADSHEET_DIR / "northstar_target_universe_partners.csv", PARTNER_FIELDS, partners)
    write_csv(SPREADSHEET_DIR / "northstar_target_universe_activity.csv", ACTIVITY_FIELDS, activity)
    write_csv(SPREADSHEET_DIR / "northstar_target_universe_next25.csv", NEXT25_FIELDS, next25)
    build_workbook(brands, partners, activity, next25)
    write_memo(brands, partners, activity, next25)

    print(f"brands={len(brands)} partners={len(partners)} activity={len(activity)} next25={len(next25)}")


if __name__ == "__main__":
    main()
