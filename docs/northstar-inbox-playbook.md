# Northstar Inbox Playbook

## Goal

Handle replies fast enough that interest turns into booked demos instead of cooling off.

## Reply classes

### `book_now`

Signal:

- asks for times
- says "yes", "interested", "happy to see it", or equivalent

Action:

- reply within 30 minutes when possible
- offer two specific time slots
- move pipeline to `replied`
- once a time is confirmed, move to `discovery_booked`

## `needs_detail`

Signal:

- asks what the product does
- asks pricing
- asks what setup is required

Action:

- send the detail-first reply from [northstar-reply-templates.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-reply-templates.md)
- include the pilot scope and pricing
- still offer a 15-minute walkthrough

## `redirect`

Signal:

- says someone else owns compliance, quality, ops, or product

Action:

- ask for the correct owner
- log the new contact
- keep the original contact in notes

## `soft_no`

Signal:

- "not now"
- "circle back later"
- timing issue without hard rejection

Action:

- ask for the right month or quarter
- set next touch date immediately
- keep the stage at `replied` or move to `closed_lost` only if they decline future contact

## `hard_no`

Signal:

- explicit no
- no fit
- no interest in future contact

Action:

- thank them
- log the reason
- move to `closed_lost`

## `objection`

Signal:

- folders/spreadsheets are enough
- already have a lab or consultant
- pilot price concern
- legal or liability concern

Action:

- use the matching response from [northstar-objections.md](C:/Users/onkha/OneDrive/Documents/New%20project/docs/northstar-objections.md)
- keep the reply short
- close with one next step

## Response timing

- `book_now`: same session if possible, otherwise within 30 minutes
- `needs_detail`: within 2 hours
- `redirect`: same day
- `soft_no`: same day
- `hard_no`: same day

## Booking rule

Never end a positive reply with "let me know what works."

Always offer two specific times in Eastern time.
