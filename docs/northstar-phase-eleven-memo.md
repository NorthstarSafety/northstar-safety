# Northstar Phase 11 Memo

Date: 2026-03-23

## What moved forward

Northstar is now closer to permanent launch readiness, even though the final permanent-host and Partner-account actions are still external.

This phase added:

- uninstall verification
- reinstall-state recovery verification
- a scripted launch check
- auto-OAuth start when Shopify provides the shop domain
- a clearer interim paid-pilot path while Shopify billing is blocked
- a full submission/checklist package for the founder

## What was verified

- the app uninstall webhook marks the install as uninstalled
- a live Shopify metadata refresh restores the shop to an active install state
- the public install page generates the correct Shopify authorization URL
- the install route now starts OAuth immediately when the store arrives from Shopify
- the billing path returns the real Shopify blocker message
- the public routes still load correctly

## What remains external

- a permanent production host and domain
- a Partner-managed Shopify app
- a final billing approval round-trip on that Partner-managed app

## Best interim commercial path

Use the existing public site and private pilot install flow for design partners.

If billing is still blocked by app ownership:

- invoice pilots directly
- keep the public pricing honest
- switch to Shopify-native billing after the Partner-managed production app is live

## Exact next button

The next founder action is not more code.

It is:

1. log into Shopify Partners
2. create or link the production app there
3. put the permanent host URL into the app settings
4. click through one real install from the permanent `/install` page
