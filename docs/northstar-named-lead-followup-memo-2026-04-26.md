# Northstar Named-Lead Follow-Up Memo

Date: 2026-04-26

## Goal

Keep the Apollo/Hunter named-lead motion moving without hurting sender reputation. Do not send early follow-ups, do not use low-confidence emails, and do not return to generic inboxes as the main channel.

## First-Wave Monitoring

The first controlled named-lead wave from 2026-04-25 remains in sequence.

Current first-wave status:

- Touch 1 sent: 15
- Immediate bounces found: 0
- Human replies found: 0
- Touch 2 scheduled: 2026-04-30
- Touch 3 scheduled: 2026-05-07

Monitoring artifact:

- `output/spreadsheet/northstar_named_leads_monitoring_2026_04_26.csv`

Touch 2 was not sent early. The sequence should breathe until 2026-04-30 unless a recipient replies or bounces before then.

## Next-25 Enrichment

The next enrichment seed was built from the existing Northstar target universe, excluding first-wave contacts and previously held-back weak contacts.

Seed artifact:

- `output/spreadsheet/northstar_named_leads_next25_enrichment_seed_2026_04_26.csv`

The seed included 22 domain-ready direct-brand targets and 3 partner/referral targets. That was the maximum clean next-25 set available without reaching into missing-domain or poor-fit records.

Hunter artifacts:

- `output/spreadsheet/hunter_next25_reveal_attempts_2026_04_26.csv`
- `output/spreadsheet/hunter_extra_partner_reveal_attempts_2026_04_26.csv`

Hunter found usable email data on many of the domains, but several results were intentionally held back because they were generic, customer-service-only, weak verification, or wrong-function contacts.

## Wave 2 Send

A second controlled named-person wave was sent on 2026-04-26.

Wave 2 counts:

- Companies/partners enriched in this pass: 35
- Wave 2 contacts approved for send: 15
- Wave 2 sends confirmed by Gmail: 15
- Held-back contacts/domains from this pass: 20
- Immediate bounces found after send: 0
- Immediate replies found after send: 0

Wave 2 activity artifacts:

- `output/spreadsheet/northstar_named_leads_wave2_send_queue_2026_04_26.csv`
- `output/spreadsheet/northstar_named_leads_wave2_activity_2026_04_26.csv`
- `output/spreadsheet/northstar_named_leads_wave2_sequence_2026_04_26.csv`
- `output/spreadsheet/northstar_named_leads_wave2_held_back_2026_04_26.csv`
- `output/named_lead_wave2_send_proof/`

Wave 2 direct-brand contacts:

- Shy Mindel, CEO, babyark
- Lauren Levy, Co-Founder, MagneticMe
- Rob Webster, Chief Executive Officer, Stokke
- Gill Moore, Chief Commercial Officer, Bugaboo
- Heather Neglerio, Chief Customer Officer, Guava Family
- Sean Smith, CEO, Zoe
- Michael Rothbard, CEO, Newton Baby
- Asaf Kehat, CEO, nanobebe
- Jill Gruys, CEO, Nurture&
- Roderick Morris, President, Lovevery
- Ritchie Powles, Director of Operations, MORI

Wave 2 partner/referral contacts:

- Lisa Trofe, Executive Director, JPMA
- John Fowler, Senior Vice President, Intertek
- Ken Wilson, Regional Director, UL Solutions
- Carson McComas, Chief Executive Officer, Fuel Made

## Wave 2 Sequence

Wave 2 follow-up timing:

- Touch 1: sent on 2026-04-26
- Touch 2: send on 2026-05-01 if no reply, no bounce, and no opt-out
- Touch 3: send on 2026-05-08 if still no reply, no bounce, and no opt-out

## Deliverability Guardrails Used

- No generic inboxes were used as the main route.
- No payment links were included.
- Low-confidence and wrong-function contacts were held back.
- The send volume stayed at 15 messages for the second wave.
- The first wave was not followed up early.
- All messages included a clear relevance opt-out line.

## Early Segment Read

It is too early to judge reply performance. The useful signal so far is operational:

- Named-person sourcing is now working.
- Hunter found more usable direct-brand founder/CEO contacts than the old generic inbox motion did.
- Partner/referral names remain useful, but very large labs can expose broad executive contacts that may not be close enough to the child-product workflow.

The strongest near-term segment to keep testing is founder/CEO and operations leadership at small-to-mid child-product brands.

## Next Actions

- Check replies and bounces daily.
- Send first-wave Touch 2 on 2026-04-30 only to eligible non-responders.
- Send second-wave Touch 2 on 2026-05-01 only to eligible non-responders.
- Respond same day to any human reply with two concrete 15-minute walkthrough times.
- Hold additional enrichment until bounce/reply data from wave 1 and wave 2 is clearer.
