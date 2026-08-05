# Future Features

The backlog. Each item has a stable ID so it can be referred to in commits and
in the changelog (`Implements F-03`).

Status: **`todo`** · **`next`** — agreed for the next version · **`done`** — move
the line to CHANGELOG.md and delete it here.

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
| **F-13** | todo | **Per-item review before applying** | Tick which proposed changes to apply instead of all-or-nothing. More pressing at 2000 items than it looked at 100 |
| **F-14** | todo | **Notifications when something sells** | Mirrors ikabot's `sendToBot` idea: Telegram / Discord / ntfy |
| **F-15** | todo | **Price rules** | e.g. Vinted price = Shopify price − 10%, instead of a straight copy |
| **F-16** | todo | **Sold-elsewhere alert** | Loud warning when an item sells on both sites before a sync ran |
| **F-17** | todo | **Run history** | Keep the last N runs, not just the most recent |
| **F-18** | todo | **Export/import settings** | Move the setup to another machine without redoing it |
| **F-19** | todo | **Second Vinted account** | If more than one wardrobe ever feeds the same store |
| **F-20** | todo | **Packaged .crx / Web Store listing** | Only worth doing if it is ever used on more than one machine |
| **F-21** | todo | **Plan grouping and filtering** | 2000 garments can produce thousands of rows. Group by action type, filter to one kind, collapse the rest |
| **F-22** | todo | **Re-box helper** | Change a garment's storage code on both platforms in one action, so a physical move cannot break the pairing |

---

## Deliberately not doing

- **Anonymous scraping of other members' listings.** The extension acts only as
  the signed-in user, on that user's own wardrobe. This is what keeps the account
  risk low (PROJECT_INFO.md §2.4).
- **Impersonating the Vinted mobile app** to dodge DataDome. Same reason.
- **Storing the Shopify token anywhere but `chrome.storage.local`.** Never in the
  repo, never in an export, never in a log line.
