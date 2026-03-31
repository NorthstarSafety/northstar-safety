# Northstar Launch Hardening Memo

Date: 2026-03-30

## Resolved

### 1. Customer-zero launch hardening

- Replaced the root production entrypoint with the real Northstar FastAPI app.
- Replaced the root Docker image so it now builds `northstar_safety` instead of the legacy product.
- Replaced the root `.env.example` with Northstar production variables, including:
  - `APP_SECRET_KEY`
  - `NORTHSTAR_DATABASE_URL`
  - SMTP settings
  - Health Canada settings
- Removed the reverse-proxy `X-Frame-Options DENY` header that would break Shopify embedding on `/app`.
- Expanded the launch checker so it now flags the real production blockers:
  - public base URL
  - PostgreSQL
  - secret key
  - SMTP
  - named users
  - uploads and backups

### 2. First real customer workflow proof

- Added [northstar_customer_zero_proof.py](C:/Users/onkha/OneDrive/Documents/New%20project/scripts/northstar_customer_zero_proof.py).
- Ran it successfully and generated a durable proof packet at:
  - [customer-zero-report.md](C:/Users/onkha/OneDrive/Documents/New%20project/output/customer-zero-proof/20260331-015050/customer-zero-report.md)
  - [customer-zero-report.json](C:/Users/onkha/OneDrive/Documents/New%20project/output/customer-zero-proof/20260331-015050/customer-zero-report.json)
  - [northstar-case-summary.txt](C:/Users/onkha/OneDrive/Documents/New%20project/output/customer-zero-proof/20260331-015050/northstar-case-summary.txt)
  - [northstar-evidence-reminder.txt](C:/Users/onkha/OneDrive/Documents/New%20project/output/customer-zero-proof/20260331-015050/northstar-evidence-reminder.txt)
- The rehearsal completed the core path:
  - seeded a realistic catalog
  - created a named workspace user
  - attached a document to a missing evidence item
  - confirmed a candidate match
  - updated the case
  - exported a case summary
  - exported an evidence reminder
  - pulled live CPSC and Health Canada alerts

### 3. Legacy naming and credibility cleanup

- Rewrote the root [README.md](C:/Users/onkha/OneDrive/Documents/New%20project/README.md) for Northstar.
- Rewrote [deploy/customer-one.env.template](C:/Users/onkha/OneDrive/Documents/New%20project/deploy/customer-one.env.template) for Northstar.
- Updated [package.json](C:/Users/onkha/OneDrive/Documents/New%20project/package.json) description to match Northstar.
- Cleaned the highest-value launch surfaces so they no longer carry EPR naming.

### 4. Health Canada ingestion

- Added first-version live Health Canada ingestion into the existing alert flow.
- Verified it in the customer-zero rehearsal:
  - 6 Health Canada alerts processed
  - 6 Health Canada alerts created
- Current posture is still review-first, not auto-action.

### 5. Lightweight user accounts

- Added named workspace users with password hashing and signed session cookies.
- Added login and logout routes.
- Defaulted match review, case ownership, and case-event actors to the signed-in user.

### 6. Production-grade storage and secrets handling

- Kept SMTP secrets env-only instead of storing them in workspace settings.
- Added backup-path awareness to launch readiness.
- Added [northstar_backup.py](C:/Users/onkha/OneDrive/Documents/New%20project/scripts/northstar_backup.py).
- Ran a real backup artifact:
  - [northstar-backup-20260331-015050-launch-hardening.zip](C:/Users/onkha/OneDrive/Documents/New%20project/northstar_safety_data/backups/northstar-backup-20260331-015050-launch-hardening.zip)

## Partially resolved

### Permanent launch state

- The codebase is now ready for a production host, but the live app is still not on a permanent host.
- The launch checker still correctly blocks on `PUBLIC_BASE_URL` when it points to localhost.

### Billing path

- Northstar still has the direct-invoice bridge for private pilots.
- Shopify Billing API remains blocked until the app is moved into Shopify Partners.

### PostgreSQL cutover

- The app now supports PostgreSQL in code and configuration.
- The live workspace is still on SQLite until `NORTHSTAR_DATABASE_URL` is provided.

## Externally blocked

- Permanent production host and DNS access
- PostgreSQL credentials
- SMTP credentials
- Shopify Partner-managed production app
- Final Shopify billing approval flow
- Founder-chosen first named user password for the live workspace

## Exact founder actions still required

1. Set a strong `APP_SECRET_KEY` in the real production environment.
2. Set `NORTHSTAR_DATABASE_URL` and migrate the live workspace to PostgreSQL.
3. Set SMTP credentials and run `POST /settings/test-email` or [northstar_launch_check.py](C:/Users/onkha/OneDrive/Documents/New%20project/scripts/northstar_launch_check.py) again.
4. Create the first live workspace user from [settings.html](C:/Users/onkha/OneDrive/Documents/New%20project/northstar_safety/templates/settings.html).
5. Deploy the current code on the permanent host using [Dockerfile](C:/Users/onkha/OneDrive/Documents/New%20project/Dockerfile) and [run_production.py](C:/Users/onkha/OneDrive/Documents/New%20project/run_production.py).
6. Move the Shopify app into Shopify Partners and rerun install plus billing.

## Bottom line

Northstar is safer for the first paid pilot than it was before this pass.

The remaining important gaps are now mostly external access gaps rather than internal product ambiguity:

- host
- database
- SMTP
- Shopify Partner billing

The customer-zero rehearsal, Health Canada ingestion, named users, backup script, and root deployment cleanup all reduce first-customer risk immediately.
