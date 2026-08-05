# Changelog

Newest first. The top entry must always match `manifest.json` and the root
`VERSION_v_x.x.x` marker file — `tests/versionConsistency.test.mjs` enforces it.

Version rules are in [VERSIONING.md](VERSIONING.md).

---

## Unreleased

Version deliberately **not** bumped — no new number was given. These changes sit
on top of v_0.1.0 until one is.

**The pairing key changed, and this matters more than anything else here.**
Matching was built around a `SKU: ABC-123` convention that does not exist in this
wardrobe. The real key is the physical storage code at the end of every
description on both platforms — `13-8 24`, meaning column 13, box 8 high, item
24. As written, the old code would have found no keys at all and reported all
2000+ garments as unmatched.

- Added `source/core/storageCode.js`: parsing, formatting, and a safe rewrite
  helper for the Vinted write path. Anchored to the end of the description so a
  size range like "fits 10-12" cannot be read as a location.
- Key order is now storage code → SKU field → title + size.
- **Title + size matches are now genuinely never written from.** They were
  previously documented as review-only but still produced update actions; they
  now produce a single `review-match` entry instead.

**Fixed two limits that only break at scale** (found after learning the wardrobe
is 2000+ items — both were fine for a small one):

- Shopify reads asked for 50 products × 25 variants a page, costing ~1300 points
  against a **1000-point hard cap per query** — Shopify would have rejected every
  read outright. Now 25 × 10 (~275).
- Vinted reads stopped at 20 pages = 1920 items, silently truncating a 2000+ item
  wardrobe. A truncated read looks to the parity engine like "these garments are
  gone from Vinted", which with `archiveSold` on would propose archiving live
  Shopify products. Cap raised, and hitting it now throws instead of returning
  partial data.

**Also:**
- Shopify requests now read `extensions.cost.throttleStatus` and wait exactly as
  long as the leaky bucket needs, with one retry on `THROTTLED`.
- Vinted page requests paced 900 ms apart — ~22 requests in a burst is the shape
  DataDome looks for.
- Permissions narrowed to `vinted.co.uk` only, shortening Chrome's install
  warning. The settings dropdown matches.
- Store domain recorded: `1kaa6a-ua.myshopify.com` (storefront
  `sixgenerations.co.uk`).

**Tests:** 36 passing, up from 21.

---

## v_0.1.0 — 2026-08-02

First version in this repository. Carried over from the prototype built in
`kurzonmorris/ikabot-modules` (branch `claude/vinted-shopify-sync-extension-r8av6l`)
and renamed throughout so every file says what it is.

**Working**
- Loads in Chrome as an unpacked MV3 extension, no build step.
- Shopify connection over the Admin GraphQL API: reads every product/variant,
  writes price, stock, title/description/vendor, and archives products.
- Vinted connection through a signed-in Vinted tab: reads the wardrobe via the
  site's own JSON endpoint, falling back to reading the rendered grid.
- Parity engine pairs both catalogues by SKU and reports every difference.
- Sync direction configurable per field group (stock / price / content).
- Dry run on by default — no writes until it is switched off.
- Activity log with a redacted JSON report export.
- Version shown in the popup and settings pages, and in the file structure.

**Not working yet**
- All Vinted writes (price, hide, description) — see
  [FUTURE_FEATURES.md](FUTURE_FEATURES.md) F-01 to F-04.
- Creating a listing that exists on only one side.

**Tests:** 21 passing (`npm test`).
