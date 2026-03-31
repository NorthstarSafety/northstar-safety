# Northstar Safety

Northstar Safety is a Shopify-connected child-product safety workspace. It helps merchants keep SKU-level evidence organized, monitor official recall signals, review likely product-alert overlaps, and keep an internal action trail in one place.

This repository is the deployment-ready source of truth for:

- the public company website at `https://www.northstarsafetyapp.com`
- the Northstar app that will live at `https://app.northstarsafetyapp.com`
- the operator workspace, Shopify integration, and launch tooling
- the deployment, cutover, and launch docs needed to run the first paid pilot

The current build includes:

- a public marketing site and install flow
- a protected operator workspace
- Shopify catalog sync for one live store
- evidence tracking and reminder drafting
- CPSC and Health Canada alert ingestion
- alert review, triage, and case summaries
- named workspace users and attributable actions
- a private-pilot billing bridge while Shopify Billing API cutover is still pending

## Repository layout

- [`northstar_safety`](northstar_safety): the FastAPI app, templates, services, and data layer
- [`deploy`](deploy): the production service, Caddy, and environment templates used for cutover
- [`scripts`](scripts): smoke tests, launch checks, backup, proof, and PostgreSQL migration tooling
- [`docs`](docs): launch, deployment, operator, sales, and Shopify submission docs
- [`sample-data`](sample-data): demo evidence files used in the live product and rehearsals

## Run locally

Install dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the workspace locally:

```powershell
.\.venv\Scripts\python.exe run_safety.py
```

Open:

```text
http://127.0.0.1:8000
```

## Production-style run

Run the production entrypoint:

```powershell
.\.venv\Scripts\python.exe run_production.py
```

Or deploy with the Render Blueprint:

- [`render.northstar.yaml`](render.northstar.yaml)

## Launch and workflow checks

Smoke-test the public and workspace routes:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_smoke_test.py
```

Check launch blockers:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_launch_check.py
```

Generate a customer-zero proof packet:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_customer_zero_proof.py
```

Create a local backup archive:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_backup.py
```

Migrate the live SQLite workspace into PostgreSQL:

```powershell
.\.venv\Scripts\python.exe scripts\northstar_migrate_to_postgres.py --target-url "postgresql://..."
```

## Core routes

- Public site: `/`
- Install: `/install`
- Embedded handoff page: `/app`
- Workspace: `/workspace`
- Products: `/products`
- Evidence queue: `/evidence`
- Alerts: `/alerts`
- Cases: `/cases`
- Settings: `/settings`
- Billing: `/billing`
- Health check: `/healthz`

## Deploy and operate

Launch and cutover docs:

- [`northstar-launch-runbook.md`](docs/northstar-launch-runbook.md)
- [`northstar-deployment-guide.md`](docs/northstar-deployment-guide.md)
- [`northstar-render-cutover.md`](docs/northstar-render-cutover.md)
- [`northstar-secrets-map.md`](docs/northstar-secrets-map.md)
- [`northstar-shopify-submission-checklist.md`](docs/northstar-shopify-submission-checklist.md)

Customer-zero and proof materials:

- [`northstar-customer-zero-proof.md`](docs/northstar-customer-zero-proof.md)
- [`northstar-launch-hardening-memo.md`](docs/northstar-launch-hardening-memo.md)
- [`northstar-phase-fifteen-memo.md`](docs/northstar-phase-fifteen-memo.md)

## Key files

- Local runner: [run_safety.py](run_safety.py)
- Production runner: [run_production.py](run_production.py)
- Docker image: [Dockerfile](Dockerfile)
- App package: [northstar_safety](northstar_safety)
- Public site kit: [northstar-squarespace-site-kit.md](docs/northstar-squarespace-site-kit.md)
- Repo cutover memo: [northstar-repo-cutover-memo.md](docs/northstar-repo-cutover-memo.md)
