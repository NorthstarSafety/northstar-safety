from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "spreadsheet"
DOCS_DIR = ROOT / "docs"

ACTIVITY_FIELDS = [
    "date",
    "company",
    "segment",
    "channel",
    "contact_route",
    "message_variant",
    "action_type",
    "status",
    "notes",
]

WORKED_FIELDS = [
    "priority_rank",
    "company",
    "segment",
    "category",
    "phase25_action",
    "best_live_route",
    "message_variant",
    "status",
    "notes",
]

VARIANTS = {
    "A_partner_intro": "Partner intro ask: short shared-client / forwardable-blurb ask.",
    "B_trigger_brand": "Trigger-based brand ask: category-specific evidence / alert-review pain with a 15-minute CTA.",
    "C_routed_team_followup": "Routed-team follow-up ask: assumes the inbox may be the right team and asks for routing only if needed.",
}


ACTIVITY_ROWS = [
    {
        "date": "2026-04-08 18:06 MT",
        "company": "UPPAbaby",
        "segment": "direct_brand",
        "channel": "Email",
        "contact_route": "support@uppababy.com",
        "message_variant": "C_routed_team_followup",
        "action_type": "touch_1",
        "status": "sent",
        "notes": "Used the routed-team follow-up variant on the best live support-team inbox surfaced from the site.",
    },
    {
        "date": "2026-04-08 18:08 MT",
        "company": "WAYB",
        "segment": "direct_brand",
        "channel": "Email",
        "contact_route": "help@wayb.com",
        "message_variant": "B_trigger_brand",
        "action_type": "touch_1",
        "status": "sent",
        "notes": "Used the trigger-based brand variant on the public help inbox surfaced from the live site.",
    },
    {
        "date": "2026-04-08 18:11 MT",
        "company": "BabyBjorn",
        "segment": "direct_brand",
        "channel": "Email",
        "contact_route": "care@babybjorn.com",
        "message_variant": "B_trigger_brand",
        "action_type": "touch_1",
        "status": "sent",
        "notes": "Used the trigger-based brand variant on the real care inbox surfaced from the live site.",
    },
    {
        "date": "2026-04-08 18:14 MT",
        "company": "Electric Eye",
        "segment": "partner_referral",
        "channel": "Email",
        "contact_route": "newbiz@electriceye.io",
        "message_variant": "A_partner_intro",
        "action_type": "touch_1",
        "status": "sent",
        "notes": "Used the partner intro variant on the agency's live new business inbox.",
    },
    {
        "date": "2026-04-08 18:16 MT",
        "company": "Eurofins Consumer Product Testing",
        "segment": "partner_referral",
        "channel": "Email",
        "contact_route": "info@eurofins.com",
        "message_variant": "A_partner_intro",
        "action_type": "touch_1",
        "status": "sent",
        "notes": "Used the partner intro variant on the public info inbox because the generic contact form was weaker than the surfaced team address.",
    },
    {
        "date": "2026-04-08 18:19 MT",
        "company": "Munchkin",
        "segment": "direct_brand",
        "channel": "Email",
        "contact_route": "helpinfantformula@munchkin.com",
        "message_variant": "B_trigger_brand",
        "action_type": "touch_1",
        "status": "sent",
        "notes": "Used the trigger-based brand variant on the live feeding-category support inbox surfaced from the site.",
    },
    {
        "date": "2026-04-08 18:22 MT",
        "company": "ergoPouch",
        "segment": "direct_brand",
        "channel": "Email",
        "contact_route": "cs@ergopouch.com.au",
        "message_variant": "B_trigger_brand",
        "action_type": "touch_1",
        "status": "sent",
        "notes": "Used the trigger-based brand variant on the live support inbox surfaced from the site.",
    },
]


ROUTE_UPGRADES = {
    "Cybex": ("https://www.cybex-online.com/en/us/contact_us.html", "", "Live site exposed a better contact page than the older sheet."),
    "Dream on Me": ("https://dreamonme.com/contact/", "", "Live site exposed a working contact page after the older route 404ed."),
    "Silver Cross": ("https://www.silvercrossbaby.com/pages/contact", "", "Homepage exposed a better contact page than the older route 404ed."),
    "Bugaboo": ("https://service.bugaboo.com/s/consumer-contact", "", "Homepage exposed a consumer support route stronger than the stale 404 link."),
    "Nuna": ("https://usasupport.nunababy.com/hc/en-us/requests/new", "", "Homepage routed to the live helpdesk request flow."),
    "Doona": ("https://doona.shop/pages/contact-1", "", "Homepage exposed a better contact page than the older route 404ed."),
    "Electric Eye": ("newbiz@electriceye.io", "A_partner_intro", "Public site exposed a live new business inbox better than the generic page route."),
    "UPPAbaby": ("support@uppababy.com", "C_routed_team_followup", "Public site exposed support and mail inboxes; support was used."),
    "WAYB": ("help@wayb.com", "B_trigger_brand", "Public site exposed a live help inbox."),
    "BabyBjorn": ("care@babybjorn.com", "B_trigger_brand", "Public site exposed a live care inbox."),
    "Munchkin": ("helpinfantformula@munchkin.com", "B_trigger_brand", "Homepage exposed a real feeding-category support inbox."),
    "ergoPouch": ("cs@ergopouch.com.au", "B_trigger_brand", "Homepage exposed a live support inbox."),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_worked_rows() -> list[dict[str, str]]:
    next25 = read_csv(OUTPUT_DIR / "northstar_target_universe_next25.csv")
    sent_lookup = {row["company"]: row for row in ACTIVITY_ROWS}
    worked_rows: list[dict[str, str]] = []
    for row in next25:
        company = row["company"]
        if company in sent_lookup:
            sent = sent_lookup[company]
            worked_rows.append(
                {
                    "priority_rank": row["priority_rank"],
                    "company": company,
                    "segment": row["segment"],
                    "category": row["category"],
                    "phase25_action": "live_send",
                    "best_live_route": sent["contact_route"],
                    "message_variant": sent["message_variant"],
                    "status": sent["status"],
                    "notes": sent["notes"],
                }
            )
            continue
        if company in ROUTE_UPGRADES:
            route, variant, note = ROUTE_UPGRADES[company]
            worked_rows.append(
                {
                    "priority_rank": row["priority_rank"],
                    "company": company,
                    "segment": row["segment"],
                    "category": row["category"],
                    "phase25_action": "route_upgraded",
                    "best_live_route": route,
                    "message_variant": variant,
                    "status": "ready_for_send",
                    "notes": note,
                }
            )
            continue
        if row["outreach_status"] == "externally_blocked":
            worked_rows.append(
                {
                    "priority_rank": row["priority_rank"],
                    "company": company,
                    "segment": row["segment"],
                    "category": row["category"],
                    "phase25_action": "carry_forward_blocker",
                    "best_live_route": row["contact_paths"],
                    "message_variant": "",
                    "status": "externally_blocked",
                    "notes": "Left blocked exactly as-is because the Guava Family Zendesk verification email still needs the inbox click.",
                }
            )
            continue
        worked_rows.append(
            {
                "priority_rank": row["priority_rank"],
                "company": company,
                "segment": row["segment"],
                "category": row["category"],
                "phase25_action": "queued_next",
                "best_live_route": row["contact_paths"],
                "message_variant": "",
                "status": row["outreach_status"],
                "notes": "Still queued in ranked order after the stronger upgraded routes were worked first.",
            }
        )
    return worked_rows


def write_memo(worked_rows: list[dict[str, str]]) -> None:
    sends = [row for row in worked_rows if row["phase25_action"] == "live_send"]
    upgraded = [row for row in worked_rows if row["phase25_action"] == "route_upgraded"]
    body = f"""# Northstar Phase 25 Memo

Date: 2026-04-08

## Goal

Turn the ranked next 25 into the first real reply by upgrading weak routes, using stronger channels, and testing three short variants instead of repeating one generic note.

## Variants used

- `A_partner_intro`: {VARIANTS['A_partner_intro']}
- `B_trigger_brand`: {VARIANTS['B_trigger_brand']}
- `C_routed_team_followup`: {VARIANTS['C_routed_team_followup']}

## What happened

- Next-25 entries reviewed/worked: {len(worked_rows)}
- Live sends from this phase: {len(sends)}
- Routes upgraded from weak/dead links to stronger live paths: {len(upgraded)}
- Real replies: 0
- Booked demos: 0

## Variant placement

- `A_partner_intro`: Electric Eye, Eurofins Consumer Product Testing
- `B_trigger_brand`: WAYB, BabyBjorn, Munchkin, ergoPouch
- `C_routed_team_followup`: UPPAbaby

## What looked strongest

- Public team inboxes found on live sites were stronger than stale generic contact-page URLs.
- Partner/team email remains a better lane than generic brand form blasting.
- Broken/404 contact routes were a real hidden problem inside the ranked sheet, so route rescue mattered.

## What to push next

- Keep doubling down on surfaced team inboxes and routed support/help addresses.
- Use the upgraded live routes for Cybex, Dream on Me, Silver Cross, Bugaboo, Nuna, and Doona next.
- Keep partner intro asks active because they still have the best odds of creating the first human reply.
"""
    (DOCS_DIR / "northstar-phase-twenty-five-memo.md").write_text(body, encoding="utf-8")


def main() -> None:
    worked_rows = build_worked_rows()
    write_csv(OUTPUT_DIR / "northstar_phase25_activity.csv", ACTIVITY_FIELDS, ACTIVITY_ROWS)
    write_csv(OUTPUT_DIR / "northstar_phase25_next25_worked.csv", WORKED_FIELDS, worked_rows)
    write_memo(worked_rows)
    print(f"phase25_activity={len(ACTIVITY_ROWS)} phase25_worked={len(worked_rows)}")


if __name__ == "__main__":
    main()
