# Northstar Phase Fifteen Memo

Date: 2026-03-30

## What is now live

- The public marketing site remains live on the root domain:
  - `https://northstarsafetyapp.com`
  - `https://www.northstarsafetyapp.com`
- The permanent app domain plan is now standardized across launch artifacts:
  - `https://app.northstarsafetyapp.com`

## What was completed in this phase

### Permanent-host cutover pack

- Updated the production Docker image:
  - [Dockerfile](C:/Users/onkha/OneDrive/Documents/New%20project/Dockerfile)
- Updated the local compose path to use the real production Dockerfile:
  - [docker-compose.northstar.yml](C:/Users/onkha/OneDrive/Documents/New%20project/docker-compose.northstar.yml)
- Tightened Docker build context hygiene:
  - [.dockerignore](C:/Users/onkha/OneDrive/Documents/New%20project/.dockerignore)
- Kept the alternate Docker file aligned so older references do not drift:
  - [Dockerfile.northstar](C:/Users/onkha/OneDrive/Documents/New%20project/Dockerfile.northstar)
- Created a clean deployment bundle for repo or host handoff:
  - [northstar-deploy-source-20260330.zip](C:/Users/onkha/OneDrive/Documents/New%20project/output/deploy-bundle/northstar-deploy-source-20260330.zip)

### Production environment preparation

- Updated the root environment template with the real Northstar production variables:
  - [.env.example](C:/Users/onkha/OneDrive/Documents/New%20project/.env.example)
- Updated the customer-one environment template:
  - [customer-one.env.template](C:/Users/onkha/OneDrive/Documents/New%20project/deploy/customer-one.env.template)
- Expanded the secrets map for:
  - `APP_SECRET_KEY`
  - `NORTHSTAR_DATABASE_URL`
  - SMTP
  - Health Canada
  - [northstar-secrets-map.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-secrets-map.md)

### PostgreSQL cutover readiness

- Upgraded the Render Blueprint so it now provisions:
  - the web service
  - a managed PostgreSQL database
  - automatic `NORTHSTAR_DATABASE_URL` wiring
  - [render.northstar.yaml](C:/Users/onkha/OneDrive/Documents/New%20project/render.northstar.yaml)
- Added a Northstar-specific SQLite to PostgreSQL migration utility:
  - [northstar_migrate_to_postgres.py](C:/Users/onkha/OneDrive/Documents/New%20project/scripts/northstar_migrate_to_postgres.py)

### Runtime and operator validation

- Verified the fresh production entrypoint with a clean smoke run.
- Verified the named-user login flow in an isolated workspace rehearsal.
- Verified the customer-zero proof workflow remains repeatable.

## What is partially resolved

### Hosted app cutover

- The code, Docker image, env templates, Blueprint, and migration script are ready.
- The app is not yet deployed on a permanent provider because provider access is still missing.

### First live named user

- The feature is implemented and validated in rehearsal.
- The first real user has not been created in the live workspace because the permanent host is not up yet and no founder-chosen live password was provided.

### SMTP

- The app is SMTP-ready in config and settings validation.
- Real SMTP credentials are still missing.

## What is externally blocked

- Render or other permanent host account access
- a deployable remote source path for the host if required by the provider
- DNS access for `app.northstarsafetyapp.com`
- PostgreSQL service credentials if not using the Blueprint-managed database
- SMTP credentials
- Shopify Partner-managed production app access

## Exact state of DNS

- `northstarsafetyapp.com` resolves to Squarespace
- `www.northstarsafetyapp.com` resolves to Squarespace
- `app.northstarsafetyapp.com` does not currently resolve

## Exact next founder action

1. Open the permanent host account and create the service from [render.northstar.yaml](C:/Users/onkha/OneDrive/Documents/New%20project/render.northstar.yaml).
2. If Render is the host, connect or push the code to a Git repo that Render can read.
3. Fill in the remaining secrets from [northstar-secrets-map.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-secrets-map.md).
4. Add the custom domain `app.northstarsafetyapp.com` to the host.
5. Add the matching DNS record for `app` once the provider gives the target hostname.
6. Run [northstar_launch_check.py](C:/Users/onkha/OneDrive/Documents/New%20project/scripts/northstar_launch_check.py) against the hosted URL.
7. If the workspace starts from SQLite data, run [northstar_migrate_to_postgres.py](C:/Users/onkha/OneDrive/Documents/New%20project/scripts/northstar_migrate_to_postgres.py).
8. Create the first live workspace user in Settings.
9. Complete Shopify Partner billing if access is available; otherwise keep using direct invoice for the first pilot.

## Bottom line

Phase Fifteen is not fully complete because the permanent host and provider-side credentials are still external.

However, the remaining uncertainty is now operational, not architectural:

- the app host is prepared
- the database cutover path is prepared
- the first-user flow is implemented
- the billing bridge remains usable

Northstar is closer to a real customer-ready environment than before this phase, but the final go-live still depends on provider access and DNS.
