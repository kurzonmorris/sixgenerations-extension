# FEATURE CREEP — everything this system does, and everything it might

**Two jobs:**

1. **Part A** is what the system can do **today**. Check here before asking for
   something — it may already exist.
2. **Parts B–E** are everything agreed, planned or floated. Nothing gets
   forgotten, and nothing gets built twice.

**Kept up to date in the same commit as any change.** A feature that ships moves
from Part D to Part A on the day it works.

| Status | Meaning |
|---|---|
| ✅ **works** | Built, tested, usable now |
| ◐ **partial** | Half there — the row says which half |
| ⛔ **stub** | The code exists and deliberately refuses |
| 📋 **agreed** | Decided, not yet built |
| ❓ **blocked** | Cannot start until a question in `docs/OPEN_QUESTIONS.md` is answered |
| 💭 **idea** | Not agreed. Waiting on `doyouwantfeatures.md` |

Feature IDs: `F-` Vinted/Shopify · `E-` eBay · `L-` ledger · `U-` interface ·
`X-` cross-platform · `S-` server/container · `D-` awaiting a yes/no in
`doyouwantfeatures.md`.

---

# Part A — what works today (v_0.1.0)

Everything here is a Chrome extension feature. There is no server yet.

## A.1 Reading

| ID | Status | Feature | Where |
|---|---|---|---|
| A-01 | ✅ | **Read the entire Vinted wardrobe** — title, description, price, brand, size, colour, condition, category, material, photo URLs, sold/hidden state | `contentScripts/vintedPageReader.js:124` |
| A-02 | ✅ | Reads through the user's own signed-in tab; no credentials handled | `connectors/vintedWardrobeConnector.js:31` |
| A-03 | ✅ | Paced at 900 ms per page so bot protection is not triggered | `vintedPageReader.js:24` |
| A-04 | ✅ | Three ways to identify the signed-in user, whichever works reported in the log | `vintedPageReader.js:74` |
| A-05 | ✅ | Falls back to reading the on-screen grid if the JSON endpoint moves | `vintedPageReader.js:196` |
| A-06 | ✅ | Refuses to return a half-read wardrobe — throws instead | `vintedPageReader.js:135` |
| A-07 | ✅ | **Read the whole Shopify catalogue**, one row per variant | `connectors/shopifyStoreConnector.js:114` |
| A-08 | ✅ | Respects Shopify's cost budget; waits the exact time the bucket needs | `shopifyStoreConnector.js:95` |
| A-09 | ✅ | Retries once after a throttle | `shopifyStoreConnector.js:193` |

## A.2 Matching

| ID | Status | Feature | Where |
|---|---|---|---|
| A-10 | ✅ | **Pair items on the storage code** `13-8 24` at the end of the description | `core/storageCode.js:24` |
| A-11 | ✅ | Tolerates spellings: `13-8-24`, `13 - 8 24`, en-dashes, trailing full stop | `core/storageCode.js:27` |
| A-12 | ✅ | Anchored to the end, so `fits 10-12` is never mistaken for a location | `core/storageCode.js:24` |
| A-13 | ✅ | Falls back to SKU, then title+size | `core/garmentItem.js:102` |
| A-14 | ✅ | **Never writes from a title guess** — reports it for review instead | `core/parityEngine.js:104` |
| A-15 | ✅ | Shows how confident each pairing is | `core/garmentItem.js:111` |
| A-16 | ✅ | **Size normalisation** — `UK 10`, `Size 10` and `10` compare equal | `core/garmentItem.js:62` |
| A-17 | ✅ | Prices compared in pence, never as floats | `core/garmentItem.js:48` |
| A-18 | ✅ | Remembers pairings between runs in a link table | `core/settingsStore.js:164` |

## A.3 Comparing and planning

| ID | Status | Feature | Where |
|---|---|---|---|
| A-19 | ✅ | **Full difference report** across price, stock, title, description, brand, size, colour, condition | `core/parityEngine.js:67` |
| A-20 | ✅ | Direction set per field group — stock one way, price and content the other | `core/messageTypes.js:53` |
| A-21 | ✅ | Detects sold-on-one-side and proposes archiving the other | `core/parityEngine.js:122` |
| A-22 | ✅ | Flags items present on only one platform | `core/parityEngine.js:88` |
| A-23 | ✅ | Counts matched / one-sided / guessed | `core/parityEngine.js:183` |

## A.4 Writing (Shopify only)

| ID | Status | Feature | Where |
|---|---|---|---|
| A-24 | ✅ | Write a price to Shopify | `shopifyStoreConnector.js:206` |
| A-25 | ✅ | Write stock to Shopify | `shopifyStoreConnector.js:222` |
| A-26 | ✅ | Write title / description / brand to Shopify | `shopifyStoreConnector.js:244` |
| A-27 | ✅ | Archive a sold Shopify product | `shopifyStoreConnector.js:267` |
| A-28 | ✅ | Turns Shopify's own error messages into readable ones | `shopifyStoreConnector.js:283` |

## A.5 Safety

| ID | Status | Feature | Where |
|---|---|---|---|
| A-29 | ✅ | **Dry run on by default** — see the whole plan, write nothing | `core/messageTypes.js:54` |
| A-30 | ✅ | Cancel mid-run, between actions | `core/syncRunner.js:23` |
| A-31 | ✅ | Every action logged with before/after values | `core/syncRunner.js:65` |
| A-32 | ✅ | Ring-buffer activity log, size configurable | `core/activityLog.js` |
| A-33 | ✅ | **Shopify token redacted from every export** | `backgroundServiceWorker.js:151` |
| A-34 | ✅ | Token stored only in `chrome.storage.local`, never synced | `core/settingsStore.js` |
| A-35 | ✅ | Export the whole run as JSON | `backgroundServiceWorker.js:122` |
| A-36 | ✅ | Snapshot of both catalogues stored after each run | `core/syncRunner.js:108` |

## A.6 Running it

| ID | Status | Feature | Where |
|---|---|---|---|
| A-37 | ✅ | Run by hand from the popup | `popupPanel/` |
| A-38 | ✅ | Optional schedule, minimum 15 minutes, **off by default** | `backgroundServiceWorker.js:41` |
| A-39 | ✅ | Test-connection buttons for both platforms | `backgroundServiceWorker.js:95` |
| A-40 | ✅ | Shopify location picked automatically on first connect | `backgroundServiceWorker.js:99` |
| A-41 | ✅ | Settings page for domains, token, directions, interval, logging | `settingsPage/` |
| A-42 | ✅ | Version shown in the UI, read from the manifest, enforced by a test | `core/extensionVersion.js` |
| A-43 | ✅ | 36 tests, no dependencies to install | `tests/` |

---

# Part B — half built

| ID | Status | Feature | What is missing |
|---|---|---|---|
| B-01 | ◐ | Rate-limit handling | Backoff works; resuming a part-finished run does not |
| B-02 | ◐ | Conflict data | The snapshot is stored but never read, so a two-sided change is not detected |
| B-03 | ◐ | Undo data | Before/after values are recorded but nothing replays them |
| B-04 | ◐ | Images | URLs are read; nothing is downloaded, compared or uploaded |

---

# Part C — stubs that deliberately refuse

| ID | Status | Feature | Where |
|---|---|---|---|
| C-01 | ⛔ | Write a price to Vinted | `vintedWardrobeConnector.js:78` |
| C-02 | ⛔ | Write stock to Vinted | `vintedWardrobeConnector.js:82` |
| C-03 | ⛔ | Write content to Vinted | `vintedWardrobeConnector.js:86` |
| C-04 | ⛔ | Hide or delete a Vinted listing | `vintedWardrobeConnector.js:90` |
| C-05 | ⛔ | Create a listing from scratch | `core/syncRunner.js:142` |

---

# Part D — planned

## D.0 — accepted 2026-09-09

**118 features said yes to**, from `doyouwantfeatures.md` (D-001 to D-120, less
D-084 and D-106 which came back unmarked). They are not repeated line by line
here — that file is the record — but they land in the areas below, and these are
the ones that changed the plan:

| From | What it settled |
|---|---|
| D-014 | Vinted stays browser-based: the account is private, and will not be a business account for at least 8 months |
| D-029 | **The SKU and the storage code are the same thing.** `7-4 21` = column 7, box 4, item 21. Call it "the SKU" on screen — that is what the business calls it |
| D-034 | Photo filenames carry the order they appear online **and the SKU** |
| D-044 | Backups matter: nightly, onsite to the server, **offsite to pCloud** |
| D-055 | `orders.csv` is the profit-and-loss working file, not a thin index. **An orders file already exists and needs remaking** |
| D-060 | Exports must open cleanly in **LibreOffice Calc**, not Excel |
| D-061 + D-063 | The Google Sheet is **two-way** — purchases are typed there on a phone and read back |
| D-075 | A simultaneous sale on two platforms is an **urgent** alert |
| D-097 | Preload the next items in the review queue so moving on is instant |
| D-209 | **Tailscale** — nothing needs exposing to the internet |
| D-233 | Generated descriptions must be trivially editable or replaceable |
| D-239 | Box QR codes: not needed now, but the design should be ready for them |

New features that came out of those answers:

| ID | Status | Feature |
|---|---|---|
| **X-06** | 📋 | **Reversible holding area.** When something sells it is delisted everywhere immediately, but the delisted listings are held — not destroyed — until the sale is confirmed, and one press puts them back. Kurzon's design, and better than what the paid tools do |
| **X-07** | 📋 | **Urgent double-sale alert** — the one event allowed to be loud |
| **S-11** | 📋 | **Offsite backup to pCloud**, alongside the onsite copy |
| **S-12** | 📋 | **Reachable over Tailscale**, with nothing exposed publicly |
| **S-13** | 📋 | **LibreOffice Calc compatibility** as an export requirement, tested |
| **S-14** | 📋 | **Two-way Google Sheet** for purchases entered on a phone |
| **U-09** | 📋 | **Dashboard with a left menu** — specified in `docs/INTERFACE_LAYOUT.md`. Overrides U-01 for the home screen only |
| **U-10** | 📋 | **Console viewer**, frozen by default, never live-tailing |
| **U-11** | 📋 | **Phone-first entry screens, desk-first packing screens** — two shapes, not one compromise |
| **U-12** | ❓ | **Links out to Vinted / eBay / the shop.** Embedding them in the page will almost certainly be refused by those sites — see `INTERFACE_LAYOUT.md §4` |
| **F-28** | 📋 | Read views, likes, offers and listing age from Vinted |
| **F-29** | 📋 | Read the Vinted category tree once and keep it |
| **L-11** | 📋 | **Import the existing ledger** — 63 monthly sheets, 2,864 sales, five years. `docs/EXISTING_LEDGER.md` |
| **L-12** | 📋 | **Petrol and posting trips in the profit calculation**, exactly as the sheet already does it: `trips × 0.959 × price per litre`, and profit = sold − (stock + petrol). This is existing behaviour, not a new feature |
| **L-13** | 📋 | **Recreate the monthly sheet as an export**, with the same totals, so nothing is lost by moving off it |
| **L-14** | 📋 | **The SKU on every sale record** — the missing link that makes profit-per-item, time-to-sell and per-platform comparison possible at all |
| **U-13** | 📋 | **The Table** — every item, one search box across every field, filters, in-place editing, at 100,000 rows. `docs/INTERFACE_LAYOUT.md §4`. The most-used screen in the system |
| **X-08** | 📋 | **Clear the unlisted backlog** — roughly 3,000 items bought and never listed. Stock already paid for |

**Still unanswered:** sections 11–24 of `doyouwantfeatures.md` (D-121 to D-252)
came back with no checkboxes at all — notifications, money, analytics,
automation, interface detail, bulk editing, safety, the server, privacy, the
Crosslist migration, other platforms and the physical workflow. Notes were
written in that range, so it was read; nothing was ticked.


Ordered roughly as `docs/SYSTEM_ARCHITECTURE.md` suggests building them.

## D.1 The server (new — this is where the system is going)

| ID | Status | Feature |
|---|---|---|
| S-01 | 📋 | **Docker container**, Python, one volume, runs on Unraid and HexOS alike |
| S-02 | ❓ | **Database** rather than a pile of CSVs — SQLite first (Q26) |
| S-03 | 📋 | **CSV export** of `onsale_inventory`, `sold_items`, `orders`, `archive` |
| S-04 | 📋 | **CSV import**, so a hand-edited file can be read back |
| S-05 | 📋 | **Image store** — full resolution, numbered in original order, deduplicated by hash |
| S-06 | ❓ | **Extension → container hand-over** (Q27) |
| S-07 | 📋 | Scheduler for polling, chasing and backups |
| S-08 | 📋 | Nightly backup of database and images |
| S-09 | 📋 | Web interface, following `INTERFACE_PRINCIPLES.md` |
| S-10 | 📋 | One button: **read my Vinted wardrobe** |

## D.2 Vinted

| ID | Status | Feature |
|---|---|---|
| F-01 | 📋 | Verify the read against the real 2,000-item wardrobe |
| F-02 | 📋 | Write a price to Vinted |
| F-03 | 📋 | Hide or delete a sold Vinted listing |
| F-04 | 📋 | Write title / description, preserving the storage code |
| F-05 | 📋 | Create a Vinted listing, photos included |
| F-24 | 📋 | **Read every extra field** — measurements, all size systems, all colours, full category path, upload date |
| F-25 | 📋 | **Read sold items and orders** |
| F-26 | 📋 | **Read buyer/seller messages** |
| F-27 | ❓ | Use the official **Vinted Pro API** instead of the tab, if the account qualifies (Q22) |

## D.3 eBay

| ID | Status | Feature |
|---|---|---|
| E-01 | ❓ | Read eBay listings (Q15) |
| E-02 | ❓ | Write a price to eBay |
| E-03 | ❓ | End an eBay listing |
| E-04 | ❓ | Create an eBay listing from an item |
| E-05 | ❓ | eBay credentials handled like the Shopify token |
| E-06 | 📋 | Read eBay orders and fees for the ledger |

## D.4 Cross-platform

| ID | Status | Feature |
|---|---|---|
| X-01 | ❓ | Three-way parity report (Q17) |
| X-02 | ❓ | **Sold anywhere → removed everywhere.** The point of the whole thing |
| X-03 | 📋 | Storage code into the eBay SKU field |
| X-04 | 📋 | **"Needs extra info" queue** — one screen, one item, only the fields the target platform demands |
| X-05 | 📋 | Per-platform required-field rules, so the queue knows what to ask for |

## D.5 Orders, postage and money

| ID | Status | Feature |
|---|---|---|
| L-01 | ❓ | Record a purchase (Q19, Q25) |
| L-02 | ❓ | Record a sale automatically |
| L-03 | 📋 | Profit per garment |
| L-05 | 📋 | Unsold stock value |
| L-06 | 📋 | Period totals |
| L-07 | ❓ | Job-lot cost apportionment (Q21) |
| L-08 | 📋 | **"Posted" button** with a photo of the parcel in its bag |
| L-09 | 📋 | Tracking numbers and delivery status |
| L-10 | 📋 | **Archive after completion, kept 5 years** |

## D.6 Notifications

| ID | Status | Feature |
|---|---|---|
| N-01 | 📋 | Something sold |
| N-02 | 📋 | Something delivered |
| N-03 | 📋 | **Delivery overdue** |
| N-04 | 📋 | Something is broken — a read failed, a token expired, a platform changed |
| N-05 | 📋 | Sold on two platforms before a check ran |

## D.7 Interface

| ID | Status | Feature |
|---|---|---|
| U-01 | 📋 | One screen, one job |
| U-02 | 📋 | Plain language, not data |
| U-03 | 📋 | Nothing moves — no animation, no toasts, no auto-refresh |
| U-04 | 📋 | Predictable placement; nothing happens on hover |
| U-05 | 📋 | Detail folded away |
| U-06 | 📋 | Per-item review before applying |
| U-07 | 📋 | Grouping and filtering at scale |
| U-08 | ❓ | Interface review with the person who uses it (Q20) |

---

# Part E — ideas, not yet agreed

Everything in `doyouwantfeatures.md` starts here. When a feature is marked **x**
in that file, it moves into Part D with a real ID; when it is built, it moves to
Part A. Nothing is deleted — a "no" stays here marked as declined, so the same
idea does not come round again in six months.

| ID | Status | Idea |
|---|---|---|
| 💭 | idea | **The whole of `doyouwantfeatures.md`** — 200+ items awaiting a yes or no |

---

# Deliberately not doing

Decided, and not up for revisiting without a reason:

- **Anonymous scraping of other members' listings.** The system acts only as the
  signed-in user, on that user's own items. This is what keeps account risk low.
- **Impersonating the Vinted mobile app** to dodge bot protection. Same reason.
- **A third-party server, account or subscription.** The whole point is not
  paying $30–45 a month for Crosslist.
- **Copying another tool's code.** Understanding what fields a platform needs is
  fine and necessary; lifting someone's source is not.
- **Credentials anywhere but the machine that runs it.** Not in the repo, not in
  an export, not in a log line, not in a CSV.
