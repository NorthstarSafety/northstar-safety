# Northstar Repository Cutover Memo

Date: 2026-03-30

## Included in this repository

- the live Northstar application under [`northstar_safety`](../northstar_safety)
- the production entrypoints and deployment files
- environment templates and Shopify app config templates
- the launch, deployment, operations, and submission docs needed to run Northstar
- the Northstar smoke test, launch check, backup, PostgreSQL migration, and customer-zero proof scripts
- the two Northstar demo evidence files used in the product and rehearsals

## Intentionally excluded

- local runtime data, backups, uploads, and generated output under `northstar_safety_data` and `output`
- the older unrelated `app` directory and other mixed legacy workspace material
- temporary logs, tunnel logs, and one-off launch artifacts
- non-Northstar scripts and sample files that would make the repo look like a mixed project instead of a clean product codebase

## Render note

This repository is shaped so Render can read it directly once the host account is connected. The main files for that cutover are:

- [`render.northstar.yaml`](../render.northstar.yaml)
- [`Dockerfile`](../Dockerfile)
- [`run_production.py`](../run_production.py)
- [`northstar-launch-runbook.md`](northstar-launch-runbook.md)
- [`northstar-secrets-map.md`](northstar-secrets-map.md)

## Founder note

If a needed historical file is still in the local workspace but not in git, that was intentional. The repo is meant to be the clean operating source of truth for Northstar going forward, not a dump of every exploratory artifact in the folder.
