# Northstar Safety Operator Guide

## Daily workflow

1. Open the dashboard.
2. Run Shopify sync if product data may have changed.
3. Run CPSC ingest.
4. Review the open case queue.
5. Open products with missing evidence.
6. Attach or update documents.
7. Review new alert matches.
8. Confirm true overlaps and dismiss false positives with a reason.
9. Update case decisions and action notes.

## What the operator should see in a healthy pilot

- each live product has a clear classification
- the product profile fills the fields Shopify does not provide
- evidence gaps are obvious
- reviewed matches have written reasoning
- confirmed overlaps have an owner and an action summary

## Current example workflow in this workspace

### Bicystar Convertible High Chair

- live SKU: `BIC-HC-001`
- one confirmed Bicystar recall overlap
- CPC summary attached
- case under review with supplier follow-up note

### SnackSprout Silicone Feeding Set

- live SKU: `SNS-FEED-001`
- no current recall overlap
- food-contact declaration attached

## Match review standard

Confirm when:

- the brand aligns
- the product family aligns
- the live SKU is plausibly inside the affected recall scope

Dismiss when:

- the brand is wrong
- the model family is different
- the alert is only a broad category lookalike

Always leave a written reason for dismissals.
