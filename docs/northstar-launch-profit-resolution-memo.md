# Northstar Launch And Profit Resolution Memo

Date: 2026-03-29

## What was fixed

### 1. First paid pilot readiness

Resolved:

- Simplified the offer to a founding pilot that is easier for a small business owner to approve.
- Rewrote the core founder-facing materials so they all describe Northstar instead of the older EPR product.
- Updated the invoice, kickoff, welcome, outreach, demo, close-path, and onboarding templates.

### 2. Pricing competitiveness

Resolved:

- Replaced the old `$1,000 onboarding + $349/month` structure with:
  - `$750` for the first 45 days
  - `$249/month` if the merchant continues
- Reduced the active rollout scope from 30 to 25 priority SKUs.
- Updated pricing across public templates, environment defaults, and deployment config.

### 3. Sales and onboarding movement

Resolved in-system:

- Founder materials now match the actual product and current offer.
- The close path is lower-friction and easier to explain.
- Pilot onboarding requirements are clearer and narrower.

Still external:

- Live pipeline movement still depends on prospect replies.

### 4. Permanent app hosting readiness

Resolved in code:

- Fixed `run_production.py` so it launches Northstar instead of the legacy Flask app.
- Fixed `Dockerfile` so it builds the Northstar FastAPI app instead of the old product.
- Verified `run_production.py` serves `/healthz` successfully.

Still external:

- Permanent hosting, DNS, and host credentials are still required.

### 5. Shopify Partner and billing path

Partially resolved:

- Billing config now reflects the ongoing Northstar founding plan instead of the old pilot pricing.
- The direct-invoice bridge remains clearly documented for private pilots.

Still external:

- Shopify Billing API charges still require a Partner-managed production app.
- Final production billing approval still depends on Shopify Partner access and the permanent host.

### 6. Full install and billing proof

Partially resolved:

- The real install/auth path already exists in code.
- The commercial path is now clearer: direct invoice first, Shopify billing after Partner cutover.

Still external:

- Permanent install, billing approval, uninstall, and reinstall proof still need the production Partner app and permanent host.

### 7. Highest-leverage operational gaps

Resolved:

- Added configurable automatic catalog refresh settings.
- Added configurable automatic official-alert refresh settings.
- Added a lightweight background automation loop for enabled jobs.
- Added a manual “run enabled refreshes now” control.
- Added exportable case summaries.
- Added evidence reminder drafting and reminder queue views.

Still open:

- Health Canada live ingestion
- lightweight named user accounts beyond basic auth
- production-grade object storage and secret rotation

### 8. App Store fit

Partially resolved:

- Existing public site, install flow, trust layer, and embedded `/app` surface still support the Shopify path.

Still open:

- Deeper embedded-admin polish is likely still needed if Shopify review becomes the main channel instead of direct private pilots.

## What is now ready for revenue

Northstar is now in a better state to win the first paid pilot because:

- the offer is simpler
- the price is easier to say yes to
- the founder materials match the actual product
- the production runtime no longer points at the wrong app
- the pilot workspace now supports reminders, exports, and scheduled refreshes

## What still blocks broader launch

External blockers:

- permanent host and DNS access
- Shopify Partner production app access
- final production billing approval

Product blockers still worth doing later:

- Health Canada live ingest
- stronger user/account model
- more production-grade storage and secret handling

## Exact next founder actions

1. Use the updated founding pilot pricing in every live conversation.
2. Send the next founding-pilot invoice using [invoice-payment-link-template.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/invoice-payment-link-template.md).
3. In a live pilot workspace, turn on automatic refreshes in [settings.html](C:/Users/onkha/OneDrive/Documents/New%20project/northstar_safety/templates/settings.html) once the store connection is stable.
4. Get permanent host credentials and deploy with [Dockerfile](C:/Users/onkha/OneDrive/Documents/New%20project/Dockerfile) plus [run_production.py](C:/Users/onkha/OneDrive/Documents/New%20project/run_production.py).
5. Move the Shopify app into Shopify Partners and rerun the permanent install and billing round-trip.

## Best money-first path

The fastest path to revenue is still:

- sell the founding pilot directly
- invoice manually
- onboard one store and 25 priority SKUs
- use the live workspace, reminder draft, and case export to prove recurring value

That path no longer depends on App Store approval or permanent Shopify billing to start learning and collecting revenue.
