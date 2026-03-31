# Northstar Business Email Cutover Memo

Date: 2026-03-29

## What is now live

- `founder@northstarsafetyapp.com` is configured as a Gmail send-as identity and is the default sender for new outbound mail.
- `support@northstarsafetyapp.com` is configured as a Gmail send-as identity for support and operational replies.
- `hello@northstarsafetyapp.com` is configured as a Gmail send-as identity and remains available as a softer general inbound alias.
- Gmail is set to reply from the same address the message was sent to.
- Gmail signatures are configured:
  - `Founder` for `founder@northstarsafetyapp.com`
  - `Support` for `support@northstarsafetyapp.com`

## Default role split

- Sales, outreach, demos, and founder communication: `founder@northstarsafetyapp.com`
- Support, contact, onboarding, and operational replies: `support@northstarsafetyapp.com`
- Optional softer website-facing inbound: `hello@northstarsafetyapp.com`

## Product and materials updated

- Northstar app public defaults now use:
  - `support@northstarsafetyapp.com` for support
  - `founder@northstarsafetyapp.com` for sales and demo mailto links
- Sales and onboarding docs now point to the business-domain addresses.
- Historical outreach materials were updated to remove visible dependence on the personal Gmail.
- The phase 8 activity export was regenerated so the founder mailbox is the visible sender reference.

## What still points to personal Gmail

- No remaining `onkhatib@gmail.com` references were found in the active Northstar docs, scripts, public defaults, or sales exports after the cutover sweep.

## Notes

- No live `.env` override file was present, so the updated code defaults are now the effective fallback behavior.
- The Squarespace account dashboard is accessible, but this pass focused on the email identity cutover itself rather than deeper site-form editing.

## Exact next founder action

- Start using `founder@northstarsafetyapp.com` for all new outreach and demos.
- Use `support@northstarsafetyapp.com` for support replies, kickoff, and customer operations.
