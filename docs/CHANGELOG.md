# Changelog

Newest first. The top entry must always match `manifest.json` and the root
`VERSION_v_x.x.x` marker file — `tests/versionConsistency.test.mjs` enforces it.

Version rules are in [VERSIONING.md](VERSIONING.md).

---

## Unreleased — 2026-09-09 (3) · scope: all 252 answered, and the real constraint

**Documents only. No code changed.**

- **All 252 features are answered: 239 yes, 13 no.** The missing ticks were never
  a formatting fault — the second half of the list was filled in on Google Docs,
  which converts `[ ]` into real checkbox objects. Those survive a **markdown**
  export and are dropped by .odt, .docx, .pdf and plain text, which is why three
  exports in a row looked blank from D-121 on. Read straight from the Doc, every
  mark was there. *If it happens again: ask for the Doc, not an export.*
- **The interface question is settled, not compromised.** D-173 ("one screen, one
  job, no dashboard") and D-174 ("plain sentences, not tables") were the only two
  rules in that section declined — and they were exactly the two that ruled out
  the dashboard. Everything else was accepted. The position is now: **a
  dashboard, with tables, that is completely still.** U-01 and U-02 are retired in
  `INTERFACE_PRINCIPLES.md`; Q37 is closed.
- **The real constraint is 3–6 items listed a day.** Against a buying rate of
  about 4.6 a day and a backlog of roughly 3,000 unlisted items, the backlog does
  not clear on its own — it holds steady or grows. Written up as
  `EXPLAINED_six-generations_Extension.md` §2A.9, with the eleven features that
  actually buy minutes back. **Every feature should now be judged on whether it
  puts more items up in a day**, which demotes the analytics sections however
  interesting they are.
- The 13 declined features are recorded in `FEATURE_six-generations_creep.md`
  Part E with reasons, so the same ideas do not come round again.
- Q36, Q37 and Q41 answered.

Version deliberately **not** bumped — no new number was given.

---

## Unreleased — 2026-09-09 (2) · scope: the real books, and the Table

**Documents only. No code changed.**

- **The existing ledger arrived and was analysed** — `six_generations_2.xlsx`,
  63 monthly sheets, **2,864 sales, £11,010.77 since October 2021**, and 8,196
  items bought for £2,234.35. Written up as **`docs/EXISTING_LEDGER.md`**. Three
  findings change the design:
  - **Job lots are the normal case** (£0.27 an item), so per-item cost is always
    apportioned.
  - **Petrol is already in the profit formula** — `trips × 0.959 × price per
    litre`, and profit = sold − (stock + petrol). D-149 was sitting unanswered in
    the feature list when it is in fact existing behaviour.
  - **No SKU anywhere in the ledger.** Sales are free-text names, so nothing can
    be joined to a listing. Putting the SKU on the sale record is what unlocks
    profit-per-item, time-to-sell and per-platform comparison (L-14).
  - Also visible: roughly **3,000 items bought and never listed**, and tracking
    numbers recorded on **1%** of sales.
- **"The Table" defined** — not a workflow stage but the item grid: one search
  box across every field, filters, in-place editing, at 100,000 rows. Specified
  as `docs/INTERFACE_LAYOUT.md §4` and it is the most-used screen in the system.
  The left menu was corrected to match.
- **The re-sent PDF carries the same 118 ticks as the .odt.** The problem was not
  the export: D-121 onwards have no checkbox in the source at all. The open items
  in `doyouwantfeatures.md` now use `( )` boxes, which survive the conversion.
- Q21, Q34 and Q35 answered; Q38–Q41 added (the two side sheets, whether to
  import five years of history, the petrol constants, and the unlisted backlog).

Version deliberately **not** bumped — no new number was given.

---

## Unreleased — 2026-09-09 · scope: 118 features accepted, and the dashboard

**Documents only. No code changed.** `doyouwantfeatures.md` came back marked up,
with notes that change several design decisions.

- **118 of 252 features accepted** (D-001 to D-120, less D-084 and D-106).
  Sections 11–24 came back with no checkboxes at all and are still open — Q36.
- **The SKU and the storage code are the same thing.** `7-4 21` = column 7, box 4,
  item 21, and the business calls it the SKU. Screens should use that word.
- **eBay is settled: the Sell API, from the container.**
- **Vinted is settled for now: private account, browser session**, and not a
  business account for at least 8 months — so the Pro API is a later migration,
  and the connector should be shaped for it.
- **Sold → delist everywhere → reversible holding area** (X-06), Kurzon's own
  design and better than what the paid tools do. A simultaneous sale on two
  platforms is the one alert allowed to be loud (X-07).
- **Tailscale** answers remote access without exposing anything (S-12).
  **pCloud** is the offsite backup (S-11). **LibreOffice Calc**, not Excel, is
  what exports must open in (S-13). The **Google Sheet is two-way** (S-14).
- New: **`docs/INTERFACE_LAYOUT.md`** — the dashboard and left menu exactly as
  asked for, with two problems stated plainly: it contradicts the
  one-screen-one-job rule written for the daily user (Q37), and Vinted, eBay and
  Shopify will almost certainly refuse to be loaded inside another page, so the
  site links open tabs instead.
- `EXPLAINED` gained §2A, the operator's own setup and workflow in his words.
- `OPEN_QUESTIONS.md`: Q15, Q19, Q22, Q25, Q26, Q28 and Q31 answered; Q34–Q37
  added.

Version deliberately **not** bumped — no new number was given.

---

## Unreleased — 2026-09-08 · scope: the system grows a server

**Documents only. No code changed.** The project turned from a browser extension
into a system: Vinted as the primary platform, a Docker container on the home
server holding the data, and a full order/postage/archive lifecycle.

New, in the repo root because they are read constantly:

- **`EXPLAINED_six-generations_Extension.md`** — the project's memory. Every file
  documented with the lines that matter, the conventions, the traps already
  learned the hard way, and a **parking lot** of things found but not yet used
  that is never deleted from. **To be updated in the same commit as every code
  change and every investigation.**
- **`FEATURE_six-generations_creep.md`** — 43 features that work today with the
  file and line that implements each, plus what is half-built, what deliberately
  refuses, what is planned, and what is only an idea.
- **`doyouwantfeatures.md`** — 252 possible features in 24 groups, awaiting a
  yes or no.

New in `docs/`:

- **`SYSTEM_ARCHITECTURE.md`** — the answer to "should this be a Docker
  container?": yes for everything except Vinted, which has no API and sits behind
  bot protection and so must stay in the browser session. Recommends SQLite as
  the store with the four CSVs as exports, and explains why "cut a row from one
  file into another" is the one part of the plan not to build literally.
- **`DATA_MODEL.md`** — items with several sizes, colours and categories at once;
  full-resolution images numbered in original order; orders, messages, shipments
  and the 5-year archive; the exact columns of all four CSVs.
- **`CLAUDE_BROWSER_TASKS.md`** — ten ready-to-paste prompts for gathering facts
  from Vinted, eBay, Shopify and Crosslist with the Claude browser extension.

Changed:

- `OPEN_QUESTIONS.md` gained Q26–Q33 (database vs CSV, hand-over method,
  automatic vs approved, photo retention, buyer-data retention, remote access,
  the extension's future, where messages go).
- `CLAUDE.md`, `README.md`, `FILE_STRUCTURE.md` updated, including a standing
  rule that the EXPLAINED and FEATURE files are updated with every change.

Version deliberately **not** bumped — no new number was given.

---

## Unreleased — 2026-09-08 · scope: eBay, the ledger, and the interface

**Documents only. No code changed.** The project grew from a two-platform sync
into a three-platform bridge with a ledger, and the planning had to be written
down before anything could be built.

New:

- **`docs/FEATURE_SPECIFICATION.md`** — what the product is meant to do across
  Vinted, eBay and Shopify plus the purchases/sales ledger, with a proposed build
  order from v_0.1.x to v_1.0.0.
- **`docs/CROSS_LISTING_TOOLS_RESEARCH.md`** — Vendoo, List Perfectly, Crosslist,
  PrimeLister and the rest. The finding that matters: **none of them reliably
  handles Vinted**, which is why this exists. Also what to copy (dry run,
  one-item-many-listings, delist-when-sold) and what to avoid (busy dashboards,
  half-filled listings, subscriptions).
- **`docs/INTERFACE_PRINCIPLES.md`** — the screen rules, written because the
  daily user has autism, ADHD and sensory sensitivities. These override normal UI
  convention and they are requirements, not polish.
- **`docs/LEDGER_DESIGN.md`** — the purchases and sales spreadsheet: proposed
  columns, the three options for where it lives, what each platform can actually
  tell us about fees, and job-lot cost apportionment.

Changed:

- **`PROJECT_INFO.md` gained §3, eBay** — OAuth and why the client secret is a
  real problem for an extension, which Sell APIs matter, daily call limits, the
  inventory/offer model, and the fact that eBay's mandatory unique SKU is a
  better pairing key than a code parsed off a description. **Written from
  secondary sources — `developer.ebay.com` was unreachable from the session, so
  it is flagged unverified throughout.** Old §3 and §4 became §4 and §5.
- **`FUTURE_FEATURES.md`** now uses ID prefixes: `F-` Vinted/Shopify, `E-` eBay,
  `L-` ledger, `U-` interface, `X-` cross-platform. F-13 and F-21 moved to U-06
  and U-07.
- **`OPEN_QUESTIONS.md`** gained Q14–Q25. Q15 (eBay API or tab-driven) and Q19
  (where the spreadsheet lives) block the most work; Q22 asks whether the Vinted
  account is a business account, which would unlock Vinted's own documented API
  and replace the fragile tab-driven read entirely.
- `CLAUDE.md`, `README.md`, `FILE_STRUCTURE.md` updated to match.

Version deliberately **not** bumped — no new number was given.

---

## Unreleased — earlier

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
