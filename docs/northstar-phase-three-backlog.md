# Northstar Safety Phase 3 Backlog

## Highest-value next steps after the pilot

1. Add richer Shopify import fields such as images, product descriptions, and collections.
2. Expand official signal coverage beyond CPSC to Health Canada and Safety Gate.
3. Add stronger match-learning loops from operator dismiss and confirm decisions.
4. Add outbound workflows for quarantine, supplier outreach, and merchant-facing action tasks.
5. Introduce auth, customer workspaces, and role-aware audit history.
6. Add notification rules for new critical alerts, stale evidence, and reopened cases.
7. Move Shopify token storage behind a safer secret-management path.

## Product validation tasks

1. Run design-partner demos with child-product brands and observe whether the evidence checklist feels complete.
2. Compare the seeded evidence model against real CPC, lab report, and registration-card workflows.
3. Backtest alert matching on a real merchant catalog and log precision / false positives.
4. Test whether teams want cases opened automatically at `medium` confidence or only at `high`.

## Technical cleanup

1. Add automated tests for seeding, evidence refresh, matching, and case-preservation rules.
2. Add migration management instead of relying on bootstrap schema creation.
3. Introduce a proper file-storage abstraction before moving beyond local uploads.
4. Add pagination and background jobs for larger alert-ingestion runs.
