# Northstar Named-Lead GTM Memo

Date: 2026-04-25

## Goal

Move Northstar from generic inbox outreach to named-person outreach using Apollo and Hunter, with a small verified first wave instead of a broad blast.

## Source Base

This sprint started from the existing Northstar target universe:

- `output/spreadsheet/northstar_target_universe_master.csv`
- `output/spreadsheet/northstar_target_universe_partners.csv`
- `output/spreadsheet/northstar_target_universe_next25.csv`
- prior phase activity logs and memos

No new broad list expansion was done. The active enrichment set was the highest-fit, domain-ready subset from the existing universe.

## Enrichment Method

Apollo was used as the named-person search and role cross-check layer. The strongest confirmed Apollo match in this pass was:

- Phil Przybylo, Vice President of Child Safety, CYBEX

Hunter was used for domain search, email reveal, and email confidence. Hunter produced the usable first-send emails and also exposed several low-confidence or wrong-function contacts that were intentionally excluded.

## Output Files

- `output/spreadsheet/northstar_named_lead_seed_top100.csv`
- `output/spreadsheet/hunter_reveal_attempts_2026_04_25.csv`
- `output/spreadsheet/hunter_partner_reveal_attempts_2026_04_25.csv`
- `output/spreadsheet/northstar_named_leads_apollo_hunter_2026_04_25.csv`
- `output/spreadsheet/northstar_named_leads_first_send_queue_2026_04_25.csv`
- `output/spreadsheet/northstar_named_leads_low_confidence_2026_04_25.csv`
- `output/spreadsheet/northstar_named_leads_activity_2026_04_25.csv`
- `output/spreadsheet/northstar_named_leads_sequence_2026_04_25.csv`
- `output/named_lead_send_proof/`

## Enrichment Counts

- Companies actively enriched in this pass: 25
- Direct-brand domains checked in Hunter: 15 including the prior CYBEX reveal
- Partner/referral domains checked in Hunter: 10
- Active named leads approved for first send: 15
- Low-confidence or wrong-function contacts held back: 6
- Apollo-confirmed role matches: 1

## First Send Wave

The first controlled wave was sent through the live Google Workspace Gmail session on 2026-04-25.

Direct-brand contacts sent:

- Phil Przybylo, Vice President of Child Safety, CYBEX
- Bradley Mattarocci, Vice President, Baby Trend
- Melissa Esposito, Director of Operations, UPPAbaby
- Tio Jung, Chief Executive Officer, WAYB
- Nick Paxton, Chief Executive Officer, Silver Cross
- Charles Plittman, Chief Financial Officer, Dream on Me
- Radhika Patil, CEO, Cradlewise
- Tom Jeffers, Chief Operating Officer, Snuggle Me Organic

Partner/referral contacts sent:

- Dan Partridge, CEO, Swanky Agency
- Laura D, Chief Operating Officer, Eastside Co
- Chase Clymer, Co-Founder, Electric Eye
- Dan Kogan, CEO, 1Digital Agency
- Paul Marchand, VP Business Development, Modern Testing Services
- Sebastien Breteau, CEO, QIMA
- Benjamin Crudo, Chief Executive Officer, Diff Agency

All 15 sends were logged in `northstar_named_leads_activity_2026_04_25.csv`. Proof screenshots show Gmail accepted the sends with `Message sent`.

## Message Variants

Direct-brand variant:

- Subject: `product evidence workflow`
- CTA: asks whether the recipient owns product documentation / recall-review workflows, or who does.

Partner/referral variant:

- Subject: `client product evidence workflow`
- CTA: asks whether a 15-minute look is worthwhile or whether there is one product-heavy merchant they would be comfortable pointing Northstar toward.

## Held-Back Contacts

The following were excluded from the first active queue:

- Ergobaby: initials-style email needed stronger role/email confirmation.
- BabyBjorn: Hunter showed weaker verification.
- ergoPouch: unknown person and weaker verification.
- Nuna: wrong function for this motion.
- Munchkin: wrong function for this motion.
- DECA: Hunter showed weaker verification.

This is important because the goal of the named-lead system is better signal quality, not just more sends.

## Early Signal

As of the immediate post-send check:

- Replies: 0
- Bounces observed: 0
- Demos booked: 0
- Payment links sent: 0
- Payments collected: 0

This is too early to evaluate conversion. The first useful read will be whether replies or bounces appear over the next 24-72 hours.

## Next Sequence Steps

Touch 2 should run on 2026-04-30 for non-responders. It should be a short 5-line summary, not a deck.

Touch 3 should run on 2026-05-07 for non-responders. It should be a polite close-out asking whether the workflow belongs to someone else.

Any real reply should be handled the same day with two concrete times for a 15-minute walkthrough.

## Current Read

The named-lead system is now live. Northstar has moved from generic inboxes to named humans at relevant companies and partner organizations.

The strongest segment on paper is still partner/referral targets, because agencies and testing/compliance providers can route Northstar to multiple relevant merchants. The strongest single direct-buyer target from this pass is CYBEX because the contact is explicitly tied to child safety.
