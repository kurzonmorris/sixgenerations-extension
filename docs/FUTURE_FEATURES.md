# Future Features

The backlog. Each item has a stable ID so it can be referred to in commits and
in the changelog (`Implements F-03`).

Status: **`todo`** · **`next`** — agreed for the next version · **`done`** — move
the line to CHANGELOG.md and delete it here · **`blocked`** — cannot start until
an open question is answered.

| Prefix | Area |
|---|---|
| **F-** | Vinted and Shopify — the original two-platform work |
| **E-** | eBay |
| **L-** | The ledger (purchases and sales) |
| **U-** | The interface |
| **X-** | Cross-platform — behaviour that only exists once all three are connected |

What the product is meant to be, as a whole, is in
[FEATURE_SPECIFICATION.md](FEATURE_SPECIFICATION.md). This file is just the list.

---

## Phase E — eBay, the third platform

All blocked on **Q15** (API or tab-driven) and **Q16** (what the eBay listings
already contain). See `PROJECT_INFO.md §3`.

| ID | Status | Feature | Notes |
|---|---|---|---|
| **E-01** | blocked | **Read the eBay listings** | Active, sold and ended. Read-only, so it cannot damage anything — the right first step |
| **E-02** | blocked | **Write a price to eBay** | `bulkUpdatePriceQuantity` on the Inventory API, or the listing form in a tab |
| **E-03** | blocked | **End an eBay listing** | The eBay half of "sold elsewhere" |
| **E-04** | blocked | **Create an eBay listing from an existing garment** | Needs a leaf category, item specifics, a condition enum and three business policies. Much bigger than E-02 |
| **E-05** | blocked | **eBay credentials in the settings page** | Same handling as the Shopify token: `chrome.storage.local` only, redacted from exports, never in the repo |

## Phase X — what having three platforms is actually for

| ID | Status | Feature | Notes |
|---|---|---|---|
| **X-01** | blocked | **Three-way parity report** | One row per garment, one column per platform. Replaces the current two-column plan. Needs Q17 answered — which platform wins for which field |
| **X-02** | blocked | **Sold anywhere → removed everywhere** | The point of the whole product. Needs E-03 and F-03 |
| **X-03** | todo | **Storage code in the eBay SKU field** | eBay's SKU is mandatory and unique per seller — a better key than a string parsed off a description (`PROJECT_INFO.md §3.5`). Probably a one-time back-fill |

## Phase L — the ledger

Design in [LEDGER_DESIGN.md](LEDGER_DESIGN.md). All blocked on **Q19** (where the
sheet lives).

| ID | Status | Feature | Notes |
|---|---|---|---|
| **L-01** | blocked | **Record a purchase** | Typed by hand — no platform provides this. Q25 asks who types it and where |
| **L-02** | blocked | **Record a sale automatically** | Platform, date, price, postage, fees, net. Shopify data is clean; Vinted fees may never be available (`LEDGER_DESIGN.md §4`) |
| **L-03** | blocked | **Profit per garment** | Purchase cost through to net proceeds |
| **L-04** | blocked | **Choose where the sheet lives** | Google Sheets, a local file, or in-extension. This is Q19 |
| **L-05** | todo | **Unsold stock value** | What is still in the boxes, and what it cost |
| **L-06** | todo | **Period totals** | Month / quarter / year. A record, not a tax return |
| **L-07** | todo | **Job-lot cost apportionment** | Q21 — even split, weighted, or lot-level only |

## Phase U — the interface

Rules in [INTERFACE_PRINCIPLES.md](INTERFACE_PRINCIPLES.md). These are
requirements, not polish — the daily user has autism, ADHD and sensory
sensitivities.

| ID | Status | Feature | Notes |
|---|---|---|---|
| **U-01** | todo | **One screen, one job** | The popup shows state and one action. Everything else moves off it |
| **U-02** | todo | **Plain-language plan** | A sentence first, the table behind *Show me* |
| **U-03** | todo | **Nothing moves** | No animation, no toasts, no auto-refresh, no spinners |
| **U-04** | todo | **Predictable layout and actions** | Same button, same place, same words. Nothing happens on hover |
| **U-05** | todo | **Progressive disclosure** | Technical detail exists, folded away, and the choice is remembered |
| **U-06** | todo | **Per-item review before applying** | Was F-13 |
| **U-07** | todo | **Plan grouping and filtering** | Was F-21. 2000 garments produce thousands of rows |
| **U-08** | todo | **Interface review with the person who uses it** | Q20. The rules above are guidance; hers are the ones that count |

---

## Phase 2 — make it write to Vinted

The blocker for v_1.0.0. All of these need testing against the live site.

| ID | Status | Feature | Notes |
|---|---|---|---|
| **F-01** | next | **Verify the Vinted read path** against the real wardrobe | Hardened for 2000+ items (paging cap raised, requests paced, truncation now throws). Still needs a live run to confirm the field names in PROJECT_INFO.md §2.5 and that storage codes parse off real descriptions |
| **F-02** | next | **Write a price to Vinted** | Needs driving Vinted's own edit form in the tab, plus the `X-CSRF-Token` header (PROJECT_INFO.md §2.3) |
| **F-03** | todo | **Hide or delete a sold Vinted listing** | The other half of "archive when sold" |
| **F-04** | todo | **Write title / description to Vinted** | Must preserve the trailing storage code — that is the pairing key. `withStorageCode()` in core/storageCode.js exists for exactly this |
| **F-05** | todo | **Create a Vinted listing from a Shopify product** | Includes uploading photos. The hardest item here |
| **F-06** | todo | **Create a Shopify product from a Vinted listing** | Easier — `productSet` does it in one mutation (PROJECT_INFO.md §1.4) |

## Phase 3 — make it robust

| ID | Status | Feature | Notes |
|---|---|---|---|
| **F-07** | todo | **Storage-code audit and repair** | Was "bulk SKU assignment", now narrower: the codes already exist. Report items whose code is missing, malformed, or duplicated across two garments, and items paired only by title. At 2000 items this is the difference between a usable plan and a wall of one-sided rows |
| **F-08** | todo | **Conflict handling** | When both sides changed since the last snapshot, ask rather than pick. The snapshot is already stored, unused |
| **F-09** | todo | **Undo the last run** | Every applied action already records before/after — enough to reverse it |
| **F-10** | partial | **Rate-limit backoff and resume** | Cost-aware waiting and one throttle retry are in. Still missing: resuming a part-finished run instead of restarting it |
| **F-11** | todo | **Size and colour writes on Shopify** | Currently skipped: they are variant *options*, so changing one may restructure the product |
| **F-12** | todo | **Image sync** | Compare and push photos. Needs a content hash so identical images are not re-uploaded |

## Phase 4 — quality of life

| ID | Status | Feature | Notes |
|---|---|---|---|
| ~~F-13~~ | moved | **Per-item review before applying** | Now **U-06** |
| **F-14** | todo | **Notifications when something sells** | Mirrors ikabot's `sendToBot` idea: Telegram / Discord / ntfy. Off by default, and never as a screen overlay — see U-03 |
| **F-15** | todo | **Price rules** | e.g. Vinted price = Shopify price − 10%, instead of a straight copy |
| **F-16** | todo | **Sold-elsewhere alert** | When a garment sold on two platforms before a check ran. Stated plainly on the screen, not shouted — see U-03. With three platforms this gets more likely, not less |
| **F-17** | todo | **Run history** | Keep the last N runs, not just the most recent |
| **F-18** | todo | **Export/import settings** | Move the setup to another machine without redoing it |
| **F-19** | todo | **Second Vinted account** | If more than one wardrobe ever feeds the same store |
| **F-20** | todo | **Packaged .crx / Web Store listing** | Only worth doing if it is ever used on more than one machine |
| ~~F-21~~ | moved | **Plan grouping and filtering** | Now **U-07** |
| **F-22** | todo | **Re-box helper** | Change a garment's storage code on every platform in one action, so a physical move cannot break the pairing |

---

## Deliberately not doing

- **A third-party server, an account, or a subscription.** Every commercial
  cross-listing tool works that way; this one does not
  (`CROSS_LISTING_TOOLS_RESEARCH.md`).
- **Anonymous scraping of other members' listings.** The extension acts only as
  the signed-in user, on that user's own wardrobe. This is what keeps the account
  risk low (PROJECT_INFO.md §2.4).
- **Impersonating the Vinted mobile app** to dodge DataDome. Same reason.
- **Storing the Shopify token anywhere but `chrome.storage.local`.** Never in the
  repo, never in an export, never in a log line.
