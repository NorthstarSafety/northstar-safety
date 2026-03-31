# Northstar Customer-Zero Proof

Date: 2026-03-31

Northstar completed a rehearsal of the first-customer workflow in an isolated workspace before permanent cutover.

## Workflow proved

- seeded a realistic child-product catalog
- created a named admin user
- attached a real evidence document to a missing requirement
- confirmed a likely official alert match
- reopened or created the linked case
- added case activity and updated the case summary
- exported a case summary and evidence reminder draft
- refreshed official alerts from CPSC and Health Canada

## Result counts

Before live ingest:

- products: 8
- missing evidence items: 6
- alerts: 5

After rehearsal:

- products: 8
- open cases: 5
- alerts: 17
- missing evidence items: 5
- stale evidence items: 3

## Proof sources

- script: [`scripts/northstar_customer_zero_proof.py`](../scripts/northstar_customer_zero_proof.py)
- summary memo: [`northstar-launch-hardening-memo.md`](northstar-launch-hardening-memo.md)
- phase memo: [`northstar-phase-fifteen-memo.md`](northstar-phase-fifteen-memo.md)

## Practical meaning

Northstar can already support the first paid pilot with the founder operating the workflow directly. The remaining gaps for a live customer are infrastructure and credential cutover, not proof that the product workflow itself works.
