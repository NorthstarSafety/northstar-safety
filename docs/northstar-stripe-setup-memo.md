# Northstar Stripe Setup Memo

Date: 2026-03-31

## What was configured

Stripe live activation is complete for the Northstar account, and Northstar now has both the one-time founding-pilot checkout path and the recurring continuation checkout path in place.

Configured in Stripe live:

- legal business path: `Unregistered business`
- payout account connected successfully
- business display name: `Northstar Safety`
- representative email aligned to `founder@northstarsafetyapp.com`
- product: `Northstar Safety Founding Pilot`
- price: `$300 USD` one-time
- offer scope: one Shopify store, first 10 priority SKUs, 30-day pilot
- hosted payment link created successfully
- custom confirmation message added to the hosted checkout flow
- Affirm and Klarna tuned with custom minimum-amount rules so BNPL does not appear on the `$300` pilot checkout
- product: `Northstar Safety Founding Continuation`
- price: `$149 USD` per month
- continuation scope: one Shopify store and up to 25 priority SKUs after explicit pilot signoff
- recurring hosted payment link created successfully
- continuation checkout narrowed to standard card and bank options after Klarna, Amazon Pay, and Cash App Pay were removed from the displayed flow

Configured in Stripe sandbox as rehearsal proof:

- product: `Northstar Safety Founding Pilot`
- price: `$300 USD` one-time
- offer scope: one Shopify store, first 10 priority SKUs, 30-day pilot
- hosted payment link created successfully
- hosted invoice rehearsal created successfully

Sandbox proof is saved in:

- [stripe-sandbox-setup.json](C:/Users/onkha/OneDrive/Documents/New%20project/output/stripe/stripe-sandbox-setup.json)

The live payment-link details are saved locally in a non-repo ops note:

- `C:\Users\onkha\OneDrive\Documents\New project\output\stripe\live-founding-pilot-payment-link.txt`
- `C:\Users\onkha\OneDrive\Documents\New project\output\stripe\live-continuation-payment-link.txt`

## What the founder should send

Use the live Stripe payment link after a qualified yes when the prospect is comfortable paying by card.

Use the Stripe invoice path when the prospect wants a formal invoice instead of a payment link.

Use the live recurring continuation link only after the pilot has proved value and the merchant explicitly agrees to continue monthly. Do not move anyone into recurring billing automatically.

The active founder materials are now aligned to the `$300` one-time pilot:

- [northstar-paid-pilot-offer.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-paid-pilot-offer.md)
- [invoice-payment-link-template.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/invoice-payment-link-template.md)
- [northstar-one-page.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-one-page.md)
- [northstar-reply-templates.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-reply-templates.md)

## What is still blocked

There is no Stripe blocker left for taking the first one-time pilot payment by card.

What remains open is optional polish, not activation:

- adding richer Stripe branding assets if desired
- refining the invoice template if customers regularly ask for invoices first
- optionally narrowing the continuation checkout from card-plus-bank to card-only if the founder wants an even stricter B2B default later

## Exact next founder action

1. Open the local ops note with the live payment link.
2. Send that Stripe payment link from `founder@northstarsafetyapp.com` when a prospect says yes.
3. If the buyer asks for an invoice instead, create a Stripe invoice manually using the same `Northstar Safety Founding Pilot` product.
4. At pilot close, if the merchant explicitly wants to continue, send the recurring continuation link instead of reopening pricing from scratch.

## Recommended live Stripe shape

- product name: `Northstar Safety Founding Pilot`
- amount: `$300 USD`
- type: one-time
- continuation product: `Northstar Safety Founding Continuation`
- continuation amount: `$149 USD` per month
- support email: `support@northstarsafetyapp.com`
- founder/sales contact: `founder@northstarsafetyapp.com`
- checkout goal: simple card-or-bank payment for a small-business pilot and a straightforward recurring continuation without BNPL

## Business-profile recommendation

Use:

- business display name: `Northstar Safety`
- support email: `support@northstarsafetyapp.com`
- support URL: `https://www.northstarsafetyapp.com/support`
- website: `https://www.northstarsafetyapp.com`
- statement descriptor: `NORTHSTAR SAFETY` if Stripe accepts it

## Practical conclusion

Northstar can now take a real live `$300` pilot payment through Stripe and move a successful pilot customer into a real `$149/month` continuation without waiting on Shopify billing.

The customer-facing pricing and payment copy are aligned with the pilot and continuation offers, the live payment links exist, BNPL and consumer-style wallet clutter have been reduced on the recurring checkout, and the invoice fallback can be used without waiting for Shopify billing.
