# Northstar Stripe Setup Memo

Date: 2026-03-31

## What was configured

Stripe access is available for the Northstar account, but only the sandbox side is fully usable right now because the live account is still in Stripe activation.

Configured in Stripe sandbox:

- product: `Northstar Safety Founding Pilot`
- price: `$300 USD` one-time
- offer scope: one Shopify store, first 10 priority SKUs, 30-day pilot
- hosted payment link created successfully
- hosted invoice rehearsal created successfully

Sandbox proof is saved in:

- [stripe-sandbox-setup.json](C:/Users/onkha/OneDrive/Documents/New%20project/output/stripe/stripe-sandbox-setup.json)

## What the founder should send

Once the live Stripe account is activated, use the Stripe payment link after a qualified yes when the prospect is comfortable paying by card.

Use the Stripe invoice path when the prospect wants a formal invoice instead of a payment link.

The active founder materials are now aligned to the `$300` one-time pilot:

- [northstar-paid-pilot-offer.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-paid-pilot-offer.md)
- [invoice-payment-link-template.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/invoice-payment-link-template.md)
- [northstar-one-page.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-one-page.md)
- [northstar-reply-templates.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-reply-templates.md)

## What is still blocked

The live Stripe account is not fully activated yet.

The exact live blocker is the Stripe activation flow at:

- `https://dashboard.stripe.com/acct_1TH7YrKxSLtfZtok/account/onboarding/business-structure`

Stripe is asking for the real legal-business onboarding details before it will allow live customer payments.

The first missing decision is the correct legal business type.

## Exact next founder action

1. In the live Stripe activation flow, choose the correct business location and legal business type.
2. Complete the remaining Stripe business verification steps accurately.
3. After the live account is activated, recreate the same one-time product and payment link on the live side, or reopen this task and the remaining setup can be completed quickly.

If Northstar is currently a sole proprietor and not formally registered, choose the matching Stripe option for an unregistered business.

If Northstar is already an LLC or corporation, choose the registered business path instead.

## Recommended live Stripe shape

- product name: `Northstar Safety Founding Pilot`
- amount: `$300 USD`
- type: one-time
- support email: `support@northstarsafetyapp.com`
- founder/sales contact: `founder@northstarsafetyapp.com`
- checkout goal: simple card payment for a small-business pilot, not subscriptions or financing

## Business-profile recommendation

When the live account is activated, use:

- business display name: `Northstar Safety`
- support email: `support@northstarsafetyapp.com`
- support URL: `https://www.northstarsafetyapp.com/support`
- website: `https://www.northstarsafetyapp.com`
- statement descriptor: `NORTHSTAR SAFETY` if Stripe accepts it

## Practical conclusion

Northstar is one Stripe activation step away from a real live `$300` payment link.

The customer-facing pricing and payment copy are now aligned with that offer, and the sandbox rehearsal proves the one-time card-checkout and invoice path.
