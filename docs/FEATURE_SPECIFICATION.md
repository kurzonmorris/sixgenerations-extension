# Feature Specification — the whole product

The master list of what this extension is meant to do, across **all three
platforms and the ledger**. `FUTURE_FEATURES.md` is the backlog with statuses;
this file is the description of the thing being built.

> **Nothing in here is agreed yet** beyond what is already shipped in v_0.1.0.
> Every item marked **?** needs an answer — they are collected in
> `OPEN_QUESTIONS.md` so they can be answered in one pass.

---

## 1. What it is

One Chrome extension (Manifest V3) that acts as a **bridge** between three
places the same garments are sold:

| Platform | Role today | How the extension reaches it |
|---|---|---|
| **Vinted** (`vinted.co.uk`) | Wardrobe. Most items sell here first | Content script inside the signed-in tab. No public API — see `PROJECT_INFO.md §2` |
| **Shopify** (`sixgenerations.co.uk`) | Own store, the catalogue of record | Admin GraphQL from the service worker. Writes already work — `PROJECT_INFO.md §1` |
| **eBay** (`ebay.co.uk`) | **New.** Not yet connected | Undecided — API or tab-driven. See `PROJECT_INFO.md §3` and Q15 |

Plus a fourth thing that is not a platform:

| **The ledger** | A running record of **purchases and sales** — what each garment cost, what it sold for, where, and what was left after fees | Spreadsheet. Format undecided — see `LEDGER_DESIGN.md` and Q19 |

The products are clothes. Everything is built around garments — size, brand,
colour, condition — not generic products.

## 2. The two things that hold it together

### 2.1 The pairing key

The storage code at the end of every listing description — `13-8 24` = column 13,
box 8, item 24. It is how one garment is recognised across platforms. Already
implemented in `source/core/storageCode.js`, already the basis of matching
between Vinted and Shopify.

**Adding eBay means the same code must be at the end of every eBay description
too.** If it is not there on existing eBay listings, they cannot pair, and the
first eBay job is a back-fill, not a sync. → **Q16**

### 2.2 One garment, three listings, one truth

With two platforms, "which side wins" is a single choice per field group. With
three, it is a matrix, and it is the main new design problem:

|  | Stock | Price | Title / description | Photos |
|---|---|---|---|---|
| Source of truth | ? | ? | ? | ? |

Current v_0.1.0 behaviour for two platforms: stock Vinted → Shopify, price and
content Shopify → Vinted. That does not extend to three by itself. → **Q17**

## 3. Features

Status: `done` · `partial` · `next` — agreed for the next version · `todo` ·
**`?`** — cannot be started until a question is answered.

### 3.1 Reading — see everything in one place

| ID | Status | Feature |
|---|---|---|
| F-01 | next | Verify the Vinted read path against the real 2000+ item wardrobe |
| **E-01** | ? | **Read the eBay listings** — active, sold, and ended. Blocked on Q15 (API or tab) |
| — | done | Read the Shopify catalogue |
| **X-01** | ? | **Three-way parity report** — one row per garment, one column per platform, differences highlighted. The replacement for the current two-column plan |
| F-07 | todo | Storage-code audit: missing, malformed, or duplicated codes; items paired by title only |

### 3.2 Writing — keep the three in step

| ID | Status | Feature |
|---|---|---|
| — | done | Write price / stock / content to Shopify |
| F-02 | next | Write a price to Vinted |
| F-03 | todo | Hide or delete a sold Vinted listing |
| F-04 | todo | Write title / description to Vinted, preserving the storage code |
| **E-02** | ? | **Write a price to eBay** |
| **E-03** | ? | **End an eBay listing when the garment sells elsewhere** |
| **X-02** | ? | **Sold-anywhere → remove everywhere.** The single most valuable behaviour in the whole product: a garment sells on Vinted, and within one run it is gone from eBay and out of stock on Shopify. Needs E-03 + F-03 |
| F-05 | todo | Create a Vinted listing from an existing garment (includes photos — hardest item here) |
| F-06 | todo | Create a Shopify product from an existing garment |
| **E-04** | ? | **Create an eBay listing from an existing garment.** eBay needs business policies and a category — more required fields than either other platform |

### 3.3 The ledger — purchases and sales

Full design in `LEDGER_DESIGN.md`. Summary:

| ID | Status | Feature |
|---|---|---|
| **L-01** | ? | **Record a purchase** — what a garment cost, where it came from, when |
| **L-02** | ? | **Record a sale automatically** — platform, date, price, fees, postage, net |
| **L-03** | ? | **Profit per garment**, from purchase cost to net proceeds |
| **L-04** | ? | **Where the sheet lives** — Google Sheets, a local file, or inside the extension. Q19 decides this |
| **L-05** | ? | **Unsold stock value** — what is still in the boxes and what it cost |
| **L-06** | ? | Period totals for bookkeeping / tax |

### 3.4 The interface

Rules in `INTERFACE_PRINCIPLES.md`. The interface is a requirement, not
decoration: the person using this daily has autism, ADHD and sensory
sensitivities, and a busy screen makes the tool unusable.

| ID | Status | Feature |
|---|---|---|
| **U-01** | ? | **One screen, one job.** No dashboard of everything at once |
| **U-02** | ? | **Plain-language plan.** "3 items sold on Vinted — remove from eBay?" not a diff table |
| **U-03** | ? | **Nothing moves.** No spinners that pulse, no toasts, no animation, no colour used alone to carry meaning |
| **U-04** | ? | **Predictable.** The same action is always in the same place; nothing happens without being pressed |
| **U-05** | ? | **Progressive disclosure.** Detail exists but is folded away — the technical view is opt-in |
| U-06 | todo | Per-item review before applying (was F-13) |
| U-07 | todo | Plan grouping and filtering at 2000 items (was F-21) |

### 3.5 Safety — unchanged and non-negotiable

| Status | Rule |
|---|---|
| done | **Dry run is the default.** Nothing writes to a live listing until it is turned off |
| done | Shopify token never leaves `chrome.storage.local`, redacted from every export |
| done | Every action logged with before/after values |
| todo | F-08 conflict handling — when two sides both changed, ask |
| todo | F-09 undo the last run |
| ? | The same three rules applied to the eBay credentials and to the ledger |

## 4. Proposed build order

Small steps, each one usable on its own. **This ordering is a proposal, not a
decision** — Q14 asks whether it is right.

| Version | Contains | Why this order |
|---|---|---|
| **v_0.1.x** (now) | Confirm the Vinted read against the real wardrobe (F-01) | Nothing else is trustworthy until the read is |
| **v_0.2.0** | eBay **read only** (E-01) + three-way report (X-01) | Read-only cannot damage anything. It also answers Q16 with real data instead of a guess |
| **v_0.3.0** | The ledger, sales only (L-02, L-04) | Sales already exist on all three platforms — this is reading, not writing, and it is immediately useful on its own |
| **v_0.4.0** | The calm interface (U-01…U-05) applied to what exists | Do it before there is more surface to redo |
| **v_0.5.0** | Purchases and profit (L-01, L-03, L-05) | Needs the sale side working first |
| **v_0.6.0** | Vinted writes (F-02, F-03) | The existing v_1.0.0 blocker |
| **v_0.7.0** | eBay writes (E-02, E-03) → **sold-anywhere-removes-everywhere (X-02)** | The payoff |
| **v_1.0.0** | Parity runs both ways across all three | Reserved meaning, unchanged |

Creating listings (F-05, F-06, E-04) sits after v_1.0.0. It is a different and
much larger job than keeping existing listings in step.

## 5. Deliberately not doing

Carried over from `FUTURE_FEATURES.md`, and still true with eBay added:

- **No anonymous scraping.** The extension acts only as the signed-in user, on
  that user's own listings.
- **No pretending to be a mobile app** to get around bot protection.
- **No third-party server.** No account, no cloud, no telemetry. Everything runs
  on the one machine. This is the main difference from every commercial tool in
  `CROSS_LISTING_TOOLS_RESEARCH.md`, and it is deliberate.
- **No credentials in the repo**, in an export, or in a log line — Shopify token,
  eBay keys, Google account, any of them.
