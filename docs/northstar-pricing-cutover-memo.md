# Northstar Pricing Cutover Memo

Date: 2026-03-31

## What was updated

Northstar's active commercial materials now align to the live founding-pilot offer and the live continuation path:

- `$300 USD` one-time
- one Shopify store
- first 10 priority SKUs in active rollout scope
- 30-day founding pilot
- secure Stripe checkout link as the default payment path
- Stripe invoice only as the fallback for buyers who ask for invoicing
- `$149 USD` per month only after explicit pilot signoff
- one Shopify store and up to 25 priority SKUs in active monthly scope for the continuation plan

The live Stripe payment links now appear in the main founder-facing close surfaces:

- [invoice-payment-link-template.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/invoice-payment-link-template.md)
- [northstar-close-path.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-close-path.md)
- [northstar-reply-templates.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-reply-templates.md)
- [northstar-paid-pilot-offer.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-paid-pilot-offer.md)

The public product and pricing surfaces were also aligned:

- [public_home.html](C:/Users/onkha/OneDrive/Documents/New%20project/northstar_safety/templates/public_home.html)
- [public_pricing.html](C:/Users/onkha/OneDrive/Documents/New%20project/northstar_safety/templates/public_pricing.html)
- [billing.html](C:/Users/onkha/OneDrive/Documents/New%20project/northstar_safety/templates/billing.html)

The Stripe link is now available as an app setting default through:

- [config.py](C:/Users/onkha/OneDrive/Documents/New%20project/northstar_safety/config.py)
- [.env.example](C:/Users/onkha/OneDrive/Documents/New%20project/.env.example)
- [northstar_safety/.env.example](C:/Users/onkha/OneDrive/Documents/New%20project/northstar_safety/.env.example)

## Historical references left in place

The only old pilot pricing references intentionally left in the active docs tree are in clearly marked historical memos:

- [northstar-launch-profit-resolution-memo.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-launch-profit-resolution-memo.md)
- [northstar-phase-seven-memo.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-phase-seven-memo.md)

They now carry a historical note at the top so they do not act as current operating guidance.

Older pricing also still exists inside archived deployment artifacts under `output/deploy-bundle/`. Those files are retained as historical snapshots, not active sales material.

## Copy decisions made

To keep the `$300` price believable and commercially sane, the offer is now described consistently as:

- intentionally narrow
- founder-led
- one store only
- first 10 priority SKUs only
- one clear proof cycle over 30 days

The close path is now:

`demo -> yes -> send live Stripe payment link -> hold kickoff`

and then, if the pilot earns the next step:

`pilot proves value -> explicit yes to continue -> send live recurring continuation link`

That removes the old invoice-first feel and makes both founder actions obvious.

## Final status

The founder can now move from conversation to pilot payment, then from pilot success to recurring continuation, without contradictory pricing in the active Northstar sales system.
