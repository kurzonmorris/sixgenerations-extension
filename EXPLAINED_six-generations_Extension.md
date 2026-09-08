# EXPLAINED — Six Generations system

**This is the project's memory. Read it first; update it last.**

Everything useful ever learned about this system lives here: how the code works,
which lines matter, what each platform does, what broke and why, and what was
found out but not used yet. The repo does not rely on chat history — if it is not
written here, the next session does not know it.

## The rule

> **After every code change and every investigation, update this file in the same
> commit.** New fact → §5 or §6. New code → §3. Something learned the hard way →
> §7. Something found but not needed yet → **§9 Parking lot**, never deleted.

## Update log

| Date | What changed |
|---|---|
| 2026-09-08 | File created. Documents v_0.1.0 as built, plus the research done for eBay, the ledger, the interface, and the new three-platform + Docker plan |

---

# 1. What the system is

Second-hand garments are sold in three places at once:

| Platform | Role | Status |
|---|---|---|
| **Vinted** (`vinted.co.uk`) | **Primary.** Items are created here first and mostly sell here | Read works |
| **Shopify** (`sixgenerations.co.uk`, `1kaa6a-ua.myshopify.com`) | Own store | Read and write work |
| **eBay** (`ebay.co.uk`) | Third channel | Not connected |

Roughly **2,000 garments today, expected to reach 100,000+**. Each garment is
one-of-a-kind: one physical item, up to three listings, and selling it anywhere
must remove it everywhere.

The long-term shape (planned, not built — see `docs/SYSTEM_ARCHITECTURE.md`):

```
Vinted  ──(browser extension, user's own session)──►  ┌────────────────────┐
                                                      │  Docker service    │
eBay    ◄──(eBay Sell API, server-to-server)────────► │  Python + database │
                                                      │  images on disk    │
Shopify ◄──(Admin GraphQL, server-to-server)────────► │  CSV export/import │
                                                      └────────────────────┘
```

---

# 2. What exists today — v_0.1.0

A Chrome extension (Manifest V3), no build step, no server, no account.
`npm test` runs 36 tests on Node's built-in runner with nothing installed.

**What it does:** reads the whole Vinted wardrobe and the whole Shopify
catalogue, pairs them on the storage code, lists every difference, and — if dry
run is turned off — writes the fixes to Shopify.

**What it does not do:** write to Vinted, touch eBay, record sales, handle
images, or store anything outside the browser.

## 2.1 Dependency direction

```
popupPanel / settingsPage        (UI — never calls a platform directly)
            ↓ messages only
backgroundServiceWorker.js       (the coordinator; the only place Shopify calls happen)
      ↓                ↓
   core/           connectors/
                        ↓
                 contentScripts/  (runs inside the Vinted tab)
```

`core/` never imports `connectors/` — except `syncRunner.js`, the one place the
two meet. That rule is what lets the matching logic be tested in Node with no
browser.

---

# 3. File by file, with the lines that matter

## 3.1 `manifest.json`

- MV3, `minimum_chrome_version: 114`.
- Permissions: `storage`, `alarms`, `scripting`, `tabs`.
- Host permissions: **only** `https://*.vinted.co.uk/*` and
  `https://*.myshopify.com/*` — the other Vinted country domains were removed to
  shorten Chrome's install warning. Adding eBay means adding a host here.
- Background is `"type": "module"`, so the worker can use ES imports. The content
  script cannot (see §7.3).
- The version appears as both `version` (`0.1.0`, digits only — Chrome rejects a
  `v_` prefix) and `version_name` (`v_0.1.0`).

## 3.2 `source/core/storageCode.js` — the pairing key

The single most important file. 63 lines.

```js
// storageCode.js:24
const TRAILING_CODE = /(\d{1,3})\s*[-–—]\s*(\d{1,3})\s*[-–—\s]\s*(\d{1,4})[\s.,;:]*$/;
```

- `13-8 24` means **column 13, box 8 high, item 24**. It sits at the **end of
  every listing description** on both platforms.
- The `$` anchor is the whole trick: it stops `fits 10-12` mid-description being
  read as a location.
- Tolerates `13-8 24`, `13-8-24`, `13 - 8 24`, en/em dashes, and a trailing full
  stop. All normalise to `13-8-24`.
- `parseStorageCode()` → the map key. `formatStorageCode()` → the written form.
  `describeStorageCode()` → "column 13, box 8, item 24" for the screen.
- `withStorageCode(description, code)` (line 55) replaces or appends the code —
  it exists so a future Vinted description write can never destroy the key.

## 3.3 `source/core/garmentItem.js` — the normalised garment

Every connector converts its platform's shape into this one, so the diff engine
never knows where a field came from.

- `makeItem()` (line 15) — the shape: `sku, storageCode, source, sourceId,
  variantId, url, title, description, price, currency, quantity, status, brand,
  size, colour, condition, category, material, images[], updatedAt, raw`.
- `toMinorUnits()` (line 48) — money is compared as integer pence. Never compare
  prices as floats.
- `normaliseSize()` (line 62) — strips `uk`, `size` and punctuation, lowercases.
  `UK 10`, `Size 10` and `10` therefore compare equal. **This is the single thing
  generic sync tools get wrong for clothing.**
- `hashItem()` (line 75) — FNV-1a over the chosen fields. Cheap "did the content
  change" check.
- `keyFor()` (line 102) — the key ladder: `loc:<storage code>` → SKU → 
  `title:<title>:<size>`.
- `keyConfidence()` (line 111) — `storage-code` | `sku` | `title-guess` | `none`.
  The plan shows this so a guess is never mistaken for a real pair.

**Known limitation, and the reason the data model is being redesigned:** every
attribute here is a *single string*. One size, one colour, one category. Real
garments have a UK size *and* an EU size *and* a letter size, and sit in several
categories at once. See `docs/DATA_MODEL.md`.

## 3.4 `source/contentScripts/vintedPageReader.js` — the Vinted reader

230 lines, runs inside the signed-in Vinted tab. This is the only code that
touches Vinted.

- `PER_PAGE = 96`, `MAX_PAGES = 80`, `PAGE_DELAY_MS = 900` (lines 19–24).
  2,000 items ≈ 22 requests ≈ 20 seconds.
- `json()` (line 45) — `credentials: 'include'`, `Accept: application/json`,
  `X-Requested-With: XMLHttpRequest`. Same-origin, so the user's own cookies go
  along and no credentials are ever handled by the extension.
- `currentUser()` (line 74) — three strategies in order: the `__NEXT_DATA__`
  hydration blob → `/api/v2/users/current` → the `/member/` link in the header.
  Whichever worked is reported as `via`, so a site change shows up in the log
  instead of silently returning nothing.
- `viaApi()` (line 124) — pages `/api/v2/users/{id}/items?page=&per_page=96`.
  **If it hits `MAX_PAGES` it throws** (line 135). Returning a truncated
  catalogue would read as "these garments no longer exist on Vinted" and, with
  `archiveSold` on, would propose archiving live Shopify products.
- `normaliseApiItem()` (line 144) — the Vinted field map. See §5.1.
- `extractStorageCode()` (line 186) — **a hand-copy of the regex in
  `storageCode.js`**, because content scripts cannot import ES modules.
  `tests/storageCode.test.mjs` fails if the two ever drift.
- `viaDom()` (line 196) — last-resort read of the rendered grid. It cannot see
  descriptions, so DOM-fallback items have **no storage code** and can only ever
  match on title + size.

## 3.5 `source/connectors/vintedWardrobeConnector.js`

The service worker's side of the Vinted conversation. 118 lines.

- `#tab()` (line 31) — finds an open Vinted tab, or opens
  `/member/general/settings` in a background tab and waits for it.
- `#ask()` (line 42) — 45 s timeout; turns Chrome's "Receiving end does not
  exist" into "reload the Vinted tab and retry".
- `waitForTabLoad()` (line 102) — waits for `status === 'complete'` **plus 1.5 s**
  because the SPA needs a beat after load before its data is queryable.
- `setPrice`, `setQuantity`, `updateContent`, `archive` (lines 78–92) all throw
  "not implemented yet (phase 2)". **Vinted writes do not exist.**

## 3.6 `source/connectors/shopifyStoreConnector.js`

288 lines. Admin GraphQL, called from the service worker where host permissions
exempt it from CORS.

- Auth is `X-Shopify-Access-Token` from a custom app. 401/403, 429 and
  `THROTTLED` are each turned into a plain-English error (lines 47–65).
- `this.throttle` caches `extensions.cost.throttleStatus` from every response —
  the budget is **read, never guessed** (line 59).
- `#waitForBudget()` (line 95) — arithmetic wait: deficit ÷ restore rate.
- `fetchItems()` (line 114) — **`pageSize = 25`, `variants(first: 10)`, and the
  reason is in the comment**: Shopify rejects any single query costing over 1000
  points, and nested connections multiply. `products(first: 50)` with
  `variants(first: 25)` ≈ 1300 points → rejected on every plan. 25 × 10 ≈ 275 is
  safe at any catalogue size. **Do not raise these numbers.**
- Also throws rather than truncating (line 155), for the same reason as Vinted.
- `#flatten()` (line 160) — one normalised item **per variant**; strips HTML from
  `descriptionHtml`; reads size from the `size / uk size / eu size / dress size`
  option names and colour from `colour / color` (lines 16–17).
- Writes: `productVariantsBulkUpdate` for price (line 206),
  `inventorySetQuantities` for stock (line 222), `productUpdate` for
  title/description/vendor (line 244), `productUpdate → ARCHIVED` for archive
  (line 267). Size and colour are deliberately **not** written: they are variant
  options and changing one can restructure the product.
- `assertNoUserErrors()` (line 283) — a GraphQL 200 with `userErrors` is still a
  failure. Always check.

## 3.7 `source/core/parityEngine.js` — the diff

187 lines of pure functions. No network, no storage. This is the testable heart.

- `index()` (line 22) — builds a key → item map; **first key wins**, duplicates
  fall through as unmatched.
- `isSold()` (line 50) — sold if the platform says so, or stock ≤ 0 and not a
  draft.
- `buildPlan()` (line 67) — walks the union of both key sets and emits actions:
  `update-price`, `update-inventory`, `update-content`, `create`, `archive`,
  `unmatched`, `review-match`.
- **Title-guess pairs emit `review-match` and nothing else** (line 104). A wrong
  pair would edit the wrong garment, so guesses are shown, never acted on.
- Direction is per field group via `targetOf()` / `sourceOf()` (lines 34–43).

## 3.8 `source/core/syncRunner.js` — the run

- `run()` (line 36) — fetch Shopify → fetch Vinted → diff → apply one action at a
  time, checking for cancellation between each.
- In dry run every action is recorded as `would-apply` and nothing is sent.
- After a run it stores the pairings (`upsertLink`) and a full snapshot of both
  catalogues (`setSnapshot`, line 108). **The snapshot is written but never read
  — it is there for conflict detection that has not been built.**
- `previewPlan()` (line 151) — read-only preview, used by the popup.

## 3.9 `source/backgroundServiceWorker.js`

- Transient run state in `current` (line 18); everything durable goes to storage,
  because MV3 kills the worker when idle.
- `chrome.alarms` drives the schedule; interval `0` means manual only, which is
  the default.
- Message handlers: `get-state`, `run-sync`, `cancel-sync`, `test-shopify`,
  `test-vinted`, `get-logs`, `clear-logs`, `export-report`.
- Every async handler `return true`s so the message channel stays open.
- `redact()` (line 151) — the Shopify token is replaced with `***redacted***`
  before any export. **The token must never appear in an export or a log line.**

## 3.10 `source/core/settingsStore.js` and `activityLog.js`

- Everything is in `chrome.storage.local`, never `sync`: the token must not leave
  the machine and the link table would outgrow the sync quota.
- `mergeDefaults()` (settingsStore line 133) — recursive merge so new default
  keys appear for anyone upgrading without wiping their settings.
- The log is a ring buffer capped at `maxLogEntries` (default 500), flushed on a
  250 ms debounce because a run emits hundreds of entries in seconds.

## 3.11 The UI

- **Popup:** connection status for both platforms with Test buttons, a dry-run
  toggle, Run / Cancel, last-run summary, activity log, Export report, Clear.
- **Settings page:** Shopify domain / token / API version / location, Vinted
  domain / username, per-field-group sync direction, archive-sold,
  create-missing, dry run, interval, log size, verbose.
- Both read the version from the manifest at runtime — nothing hardcodes it.
- **Neither screen yet follows `docs/INTERFACE_PRINCIPLES.md`.** They are
  conventional developer UI and will need reworking.

---

# 4. The tests

`npm test` — 36 tests, Node's built-in runner, nothing to install.

| File | Covers |
|---|---|
| `storageCode.test.mjs` | Parsing, tolerated spellings, false-match guards, **and that the duplicated regex in the content script still agrees with the module** |
| `parityEngine.test.mjs` | Matching and the diff rules |
| `extensionWiring.test.mjs` | Worker message handling, settings merge, token redaction |
| `versionConsistency.test.mjs` | Fails if the version drifts between its five homes |
| `chromeApiStub.mjs` | Fake `chrome.*` so extension code runs under Node |

---

# 5. Platform facts in use

Full reference is `docs/PROJECT_INFO.md`. The short version:

## 5.1 Vinted

No public API for private sellers. Everything is the site's own internal JSON
API — unversioned, undocumented, behind **DataDome** bot protection.

| Purpose | Path |
|---|---|
| Signed-in user | `/api/v2/users/current` |
| **The wardrobe** | `/api/v2/users/{id}/items?page=&per_page=96` |
| One item's detail | `/api/v2/items/{id}` |
| Conversations | `/api/v2/conversations` *(not used yet — see §9)* |

Field map (each read defensively, names vary by locale):

| Meaning | Field(s) |
|---|---|
| Price | `price.amount` + `price.currency_code`, sometimes a bare `price` |
| Brand | `brand_title` or `brand.title` |
| Size | `size_title` or `size` |
| **Condition** | **`status`** |
| Colour | `color1` |
| Category | `catalog_title` |
| Photos | `photos[].full_size_url` or `photos[].url` |
| Sold | `is_closed`, `is_sold`, `item_closing_action === 'sold'` |
| Hidden | `is_hidden` |

## 5.2 Shopify

Admin GraphQL, version pinned in settings (`2025-01`). Leaky-bucket rate limit
reported on every response. Query cost cap 1000 points per query — see §3.6.
Mutations in use: `productVariantsBulkUpdate`, `inventorySetQuantities`,
`productUpdate`.

## 5.3 eBay

Nothing built. `docs/PROJECT_INFO.md §3` has the briefing, written from secondary
sources because `developer.ebay.com` was unreachable. The one fact that shapes
everything: **refreshing an eBay token needs a client secret every 2 hours, and a
browser extension cannot keep a secret.** That is an argument for the server-side
container, not the extension.

---

# 6. The conventions that hold it together

1. **The storage code is identity.** `13-8 24`, at the end of the description, on
   every listing.
2. **Dry run is the default.** Nothing writes to a live listing until it is
   turned off deliberately.
3. **Never hand a truncated catalogue to the diff engine.** Throw instead.
4. **Never write from a guess.** Title matches are reported, never applied.
5. **Secrets live in `chrome.storage.local` only** — never the repo, an export or
   a log line.
6. **Filenames say what they do**, camelCase, and every new one gets a row in
   `docs/FILE_STRUCTURE.md`.
7. **Never bump a version without being given the number**
   (`docs/VERSIONING.md`).

---

# 7. Traps — things already learned the hard way

## 7.1 The Shopify nested-cost trap
`products(first: N) { variants(first: M) }` costs roughly `N + (N × M)`. At
50 × 25 that is ~1300 points, over the 1000 cap, rejected outright on **every**
plan. This bit the code once. Current 25 × 10 ≈ 275.

## 7.2 The `status` collision
On Vinted, `status` is the garment's **condition** ("Very good"). On Shopify it
is the **listing state** (ACTIVE / DRAFT / ARCHIVED). `garmentItem.js` keeps them
as `condition` and `status`. Never merge them.

## 7.3 Content scripts cannot import ES modules
Which is why the storage-code regex is duplicated in `vintedPageReader.js`. A
test enforces that the copies agree. Do not "fix" this with an import.

## 7.4 Truncation is worse than failure
Both readers throw when they hit their page cap. A short catalogue looks exactly
like "everything was deleted", and with archive-sold on that becomes a proposal
to archive live products.

## 7.5 DataDome pacing
22 requests in a burst is the shape bot protection looks for. 900 ms between
pages, from a real signed-in tab, is not. Do not remove the delay to make the
read faster.

## 7.6 The re-boxing hazard
The pairing key describes where a garment physically **is**. Move it and update
only one platform, and the pair silently breaks — both sides then report as
one-sided. Safe, but at 2,000 items it will happen regularly. This is
`OPEN_QUESTIONS.md` Q11 and is a strong argument for a **separate immutable
internal id** with the storage code as a mutable attribute.

## 7.7 GraphQL 200 ≠ success
Shopify returns HTTP 200 with a `userErrors` array. Always assert on it.

## 7.8 MV3 kills the worker
Nothing durable can live in module scope. It is also why an extension alone can
never be a 24/7 monitor — the browser has to be open.

---

# 8. What is deliberately not built

| Not built | Why |
|---|---|
| Vinted writes | Needs driving Vinted's own edit form against live markup |
| eBay, anything | Blocked on the API-or-tab decision (`OPEN_QUESTIONS.md` Q15) |
| Sales / purchases / ledger | Blocked on where the data lives (Q19) |
| Image handling | Image URLs are read; nothing is downloaded or compared |
| Conflict detection | The snapshot is stored but never read |
| Undo | Before/after values are recorded but nothing replays them |
| Multi-value attributes | The item shape holds one string per field |
| Anonymous scraping of other members | Deliberate. It is what keeps account risk low |
| Impersonating the Vinted mobile app | Same reason |

---

# 9. Parking lot — found but not used

Nothing here is in the code. It is kept because it will probably matter later.
**Never delete from this section; move things out of it when they get used.**

## 9.1 Vinted Pro Integrations API — potentially the biggest single find

Vinted publishes a real API for **business (Pro) accounts** at
`pro-docs.svc.vinted.com`, with three parts:

- **Items API** — create, update and delete items programmatically.
- **Webhooks API** — notifications when items change.
- **Orders API** — sales and shipment information.

Reported constraints: a Pro account is required, access is granted by **manual
allowlist approval from Vinted**, and new integrations start with a **500 active
item slot limit** (against a 2,000-item wardrobe).

**Why it matters:** it would replace the fragile DataDome-dodging tab reader with
a supported server-side integration, and the Webhooks + Orders APIs would deliver
the sold-item notifications and postage data the ledger needs, with no browser
open. This is `OPEN_QUESTIONS.md` Q22 and worth answering before much more is
built on the scraping route.

## 9.2 eBay OAuth mechanics

- Token endpoint `https://api.ebay.com/identity/v1/oauth2/token`.
- `redirect_uri` is eBay's **RuName**, not a URL.
- `Authorization: Basic base64(client_id:client_secret)` on the exchange **and on
  every refresh**.
- User access token **7,200 s (2 hours)**; refresh token **47,304,000 s (~18
  months)**.
- No PKCE / public-client flow found — hence the secret problem.

## 9.3 eBay daily call limits (application-level, not per user)

Trading (legacy XML) **5,000/day** · Inventory **2,000,000/day** · Account
**25,000/day** · Feed **100,000/day**. Headers `X-eBay-C-RateLimit-Limit`,
`-Remaining`, `-Reset`. Raised free via an "Application Growth Check". For one
seller the REST limits are effectively unlimited; the legacy one is not.

## 9.4 eBay's SKU is a better key than a description tail

In eBay's Inventory API the SKU is **mandatory and unique per seller** — an
exact-match indexed field. If the eBay listings can carry the storage code there,
eBay becomes the most reliable of the three to match on. (Q16.)

## 9.5 Crosslist — the tool currently being paid for

$29.99–$44.99/month. 11+ marketplaces including Vinted, eBay, Etsy, Depop,
Mercari, Poshmark, WooCommerce. Relevant capabilities: **bulk CSV import and
export**, bulk import of existing listings with photos and all listing details,
and **auto-delisting when an item sells**.

**The useful part: it can export.** That export is Kurzon's own data and is by far
the cheapest way to bootstrap the database — no scraping needed for the initial
load, and it reveals the field set a working cross-lister actually keeps.

## 9.6 The cross-listing tool landscape

Vendoo, List Perfectly, PrimeLister, Flyp, Voolist, Flipsail. Two architectures:
extension form-fillers (slow, browser must be open, fill only some fields) and
cloud API tools (fast, but need a public API, so no Vinted). Vendoo advertised
Vinted then quietly dropped it. Full notes in
`docs/CROSS_LISTING_TOOLS_RESEARCH.md`.

## 9.7 Google Sheets from an extension

`chrome.identity.getAuthToken` with an OAuth client ID in the manifest — **no
client secret needed**, Chrome handles the flow. Relevant only if the ledger ends
up in Sheets rather than the container (Q19).

## 9.8 Neurodivergent UX sources

Collected while writing `docs/INTERFACE_PRINCIPLES.md`. WCAG covers cognitive
needs only loosely; the useful material is neurodivergent-UX writing. Sources are
listed at the bottom of that file.

## 9.9 Vinted conversation endpoint

`/api/v2/conversations` is documented in public reverse-engineering write-ups as
the messages endpoint. **Unverified here.** It is the likely source for the
buyer/seller message copies the sold-items record needs.

## 9.10 Cookie-auth fragility

Public write-ups on Vinted's internal API report that cookie sessions expire
quickly and that scaling requests produces 403s. This is consistent with the
900 ms pacing already in the code, and is a reason the container should never
call Vinted directly without the browser.

---

# 10. Glossary

| Term | Meaning |
|---|---|
| **Storage code** | `13-8 24` = column 13, box 8 high, item 24. The pairing key |
| **Parity** | All platforms agreeing on stock, price and content |
| **Dry run** | Produce the plan, write nothing. The default |
| **Plan / action** | The list of changes a run would make |
| **review-match** | A pair found only by title + size. Shown, never written from |
| **Link table** | Stored map of key → platform ids |
| **Snapshot** | Full copy of both catalogues after a run. Stored, unused |
| **DataDome** | The bot protection in front of Vinted's web endpoints |
| **RuName** | eBay's redirect identifier, used instead of a redirect URL |
| **Pro / business account** | A Vinted seller account type that unlocks the official API |

---

# 11. How to update this file

1. **After a code change** — update the file's entry in §3 with the new function
   and line numbers, and add anything hard-won to §7.
2. **After an investigation** — put confirmed, in-use facts in §5; put anything
   found but not yet used in **§9**, with enough detail to act on later.
3. **When something in §9 gets used** — move it out of the parking lot into the
   relevant section.
4. **Always** add a row to the update log at the top.
5. Then the normal checks: `npm test`, `node --check` on any file Chrome loads.
