# Project Info — API and Web Code Reference

**Purpose:** the researched facts this project depends on, written down once so
they never have to be looked up again. If something here turns out to be wrong
when tested against the live sites, **correct it here in the same commit as the
code fix** — this file is the memory, not the chat.

Last verified: **2026-08-02**. Sources are linked at the bottom.

---

## 1. Shopify — Admin GraphQL API

### 1.1 Connection details

| Thing | Value |
|---|---|
| Endpoint | `https://{shop}.myshopify.com/admin/api/{version}/graphql.json` |
| Method | Always `POST`, body `{"query": "...", "variables": {...}}` |
| Auth header | `X-Shopify-Access-Token: shpat_…` |
| Content type | `application/json` |
| API version in use | `2025-01` (set in settings, changeable without a code edit) |

The token comes from a **custom app** in the store admin:
`Settings → Apps and sales channels → Develop apps → Create an app`.

Scopes this extension needs:
`read_products`, `write_products`, `read_inventory`, `write_inventory`.

### 1.2 API versions and the release cycle

Shopify ships a new version every quarter (Jan/Apr/Jul/Oct), each supported for
at least 12 months. As of 2026: **2026-01 and 2026-04 are stable, 2025-10 is
still supported, 2025-07 is sunset**, and 2026-07 exists.

We pin `2025-01` because that is what the current code was written against.
**Before bumping the version setting, re-check §1.4 — the inventory mutation
changed in 2026-01.**

### 1.3 CORS — why this works from an extension at all

Shopify's Admin API sends no CORS headers, so a normal web page cannot call it.
An MV3 **service worker** with a matching `host_permissions` entry is exempt from
CORS, so the calls succeed there. They would fail from a content script or from
the popup page. **All Shopify traffic must stay in `backgroundServiceWorker.js`
and the connector it calls.**

### 1.4 Mutations used, and the deprecation traps

| Job | Mutation | Notes |
|---|---|---|
| Read catalogue | `products(first:, after:)` connection | Paginated, `nodes { … variants(first: 25) { nodes … } }` |
| Update price | `productVariantsBulkUpdate(productId:, variants:)` | **`productVariantUpdate` is deprecated/removed — do not use it.** Takes an array even for one variant. |
| Set stock | `inventorySetQuantities(input:)` | `name: "available"`, `reason: "correction"`, `ignoreCompareQuantity: true`. **Changed in 2026-01 — re-verify if the API version is raised.** |
| Title / description / vendor | `productUpdate(input: ProductInput)` | `descriptionHtml`, not `description` |
| Mark as gone | `productUpdate` with `status: ARCHIVED` | |
| Create with variants (phase 2) | `productSet` | Replaces `productCreate` + `productVariantsBulkUpdate` for most cases |

Every mutation returns `userErrors { field message }`. A 200 response with
`userErrors` populated **is a failure** — the connector treats it as one.

### 1.5 Rate limits

GraphQL Admin uses a **calculated-cost leaky bucket**, not a request count:

| Plan | Bucket | Restore rate |
|---|---|---|
| Standard | 1,000 points | 50 points/sec |
| Advanced | ~2,000 points | 100 points/sec |
| Plus | 2,000 points | 100–500 points/sec |

- A single query may never cost more than **1,000 points**, on any plan.
- Every response carries `extensions.cost.throttleStatus` with
  `currentlyAvailable` and `restoreRate` — read it rather than guessing.
- Over-budget requests return a `THROTTLED` error (and/or HTTP 429).

**Practical effect here:** a wardrobe of a few hundred garments is nowhere near
these limits at 50 products per page. Backoff is still a phase-3 item (F-10)
because a first full sync of a large store could hit it.

### 1.6 Identifiers

Everything is a GID string, not a number: `gid://shopify/Product/123`,
`gid://shopify/ProductVariant/456`, `gid://shopify/Location/789`,
`gid://shopify/InventoryItem/…`. Never parse or construct these — store and
return them whole.

Inventory writes need **both** an `inventoryItemId` and a `locationId`. The
location is picked once on first connect and saved in settings.

---

## 2. Vinted — internal web API

### 2.1 The situation

Vinted has **no public partner API** for private sellers. There is a
`pro-docs.svc.vinted.com` API, but it is for Vinted Pro business accounts.
Everything below is the site's own internal JSON API — unversioned, undocumented,
and free to change without notice.

**This is why the reader records which path produced the data (`via`), and why
the DOM fallback exists.** When Vinted changes something, the activity log will
say so instead of quietly returning an empty wardrobe.

### 2.2 Endpoints (confirmed against public references)

Base: `https://www.vinted.co.uk` (domain is a setting — `.fr`, `.de`, etc. all
expose the same paths).

| Purpose | Path | Parameters |
|---|---|---|
| Signed-in user | `/api/v2/users/current` | — |
| A member's profile | `/api/v2/users/{id}` | — |
| **A member's items (the wardrobe)** | `/api/v2/users/{id}/items` | `page`, `per_page`, `order` |
| One item's detail | `/api/v2/items/{id}` | `localize` |
| Catalogue search | `/api/v2/catalog/items` | `search_text`, `catalog_ids`, `size_ids`, `price_from`, `price_to`, `page`, `per_page`, `order` |

The wardrobe endpoint is the one this extension reads. `per_page=96` is used;
paging stops when a page returns fewer rows than requested.

### 2.3 Headers and session

- **Cookies** — the signed-in session. Obtained by the user logging in normally;
  the extension never handles credentials. Requests from the content script are
  same-origin, so `credentials: 'include'` is enough.
- **`X-CSRF-Token`** — read from the page's meta tag. Required for **write**
  requests, not for the reads currently implemented.
- **`X-Anon-Id`** — read from cookies. Some endpoints expect it.
- **`User-Agent`** — left as the real browser's. Do not spoof it; the whole point
  of running inside the user's own tab is that the traffic is genuine.

### 2.4 Bot protection — the main risk

Vinted's web endpoints sit behind **DataDome**. Volume from one IP gets blocked.
The mobile app endpoints are reportedly less protected, but using them would mean
impersonating the app, which is exactly the kind of thing that gets an account
banned.

**Design consequences, all already in the code:**
- Reads run only in a tab the user is already signed into.
- One request per page of results, not per item.
- Scheduled sync defaults to **off**; the shortest selectable interval is 15 min.
- Nothing runs without a session.

### 2.5 Item JSON fields

Field names vary by locale and change over time, so `vintedPageReader.js` reads
each defensively with fallbacks. Known names:

| Meaning | Field(s) |
|---|---|
| Id | `id` |
| Title | `title` |
| Description | `description` |
| Price | `price.amount` + `price.currency_code` (sometimes a bare `price`) |
| Brand | `brand_title`, or `brand.title` |
| Size | `size_title`, or `size` |
| Condition | `status` (⚠ *not* a listing state — it means wear/condition) |
| Colour | `color1` |
| Category | `catalog_title` |
| Photos | `photos[].full_size_url` or `photos[].url` |
| Sold | `is_closed`, `is_sold`, `item_closing_action === 'sold'` |
| Hidden | `is_hidden` |

⚠ **The `status` trap:** on Vinted `status` is the garment's *condition*
("Very good"), while on Shopify `status` is the *listing state*
(ACTIVE/DRAFT/ARCHIVED). `garmentItem.js` keeps them apart: `condition` vs
`status`. Do not merge them.

### 2.6 No SKU field

Vinted listings have nowhere to put a SKU. The convention this project uses is a
code in the **description**: `SKU: ABC-123` or `[ABC-123]`, parsed by
`extractSku()` in `vintedPageReader.js`. Without it, pairing falls back to
title + size, which is reported but never used to drive a write.

---

## 3. Chrome extension platform (MV3)

| Constraint | Consequence for this project |
|---|---|
| The service worker is killed when idle | No durable state in module scope. Settings, links and logs all live in `chrome.storage.local`. Run state is deliberately transient. |
| Content scripts cannot use ES modules | `vintedPageReader.js` is standalone — it duplicates the few message-name constants rather than importing them. |
| `chrome.alarms` minimum period | 1 minute; anything shorter is silently clamped. Our shortest option is 15 minutes anyway. |
| Message channel closes on return | Every async `onMessage` handler returns `true` and calls `sendResponse` later. |
| CSP forbids inline script | All HTML pages load their JS from a file. No `onclick=` attributes. |
| `chrome.storage.sync` quota | Too small for the link table, and the Shopify token must never leave the machine — everything uses `local`. |

---

## 4. Where each fact is used in the code

| Fact | File |
|---|---|
| Shopify endpoint, headers, mutations, error handling | `source/connectors/shopifyStoreConnector.js` |
| Vinted endpoints, headers, field mapping, SKU parsing | `source/contentScripts/vintedPageReader.js` |
| Tab lifecycle, "is there a signed-in tab" | `source/connectors/vintedWardrobeConnector.js` |
| CORS-sensitive traffic | `source/backgroundServiceWorker.js` only |
| Size/price normalisation rules | `source/core/garmentItem.js` |

---

## Sources

- [Shopify API versioning](https://shopify.dev/docs/api/usage/versioning)
- [Shopify API limits](https://shopify.dev/docs/api/usage/limits)
- [productVariantsBulkUpdate](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productvariantsbulkupdate)
- [productUpdate](https://shopify.dev/docs/api/admin-graphql/latest/mutations/productUpdate)
- [productVariantUpdate deprecation thread](https://community.shopify.dev/t/productvariantupdate-mutation-deprecated/9400)
- [inventorySetQuantities 2026-01 change thread](https://community.shopify.dev/t/inventorysetquantities-mutation-broken/27396)
- [Shopify GraphQL rate limits (2026)](https://www.letstalkshop.com/blog/shopify-admin-graphql-rate-limits-2026)
- [Vinted API endpoint reference (hipsuc/Vinted-API)](https://github.com/hipsuc/Vinted-API/blob/main/VintedApi.py)
- [Vinted API guide — endpoints, headers, DataDome](https://www.lobstr.io/blog/vinted-api)
- [Vinted Pro API docs (business accounts only)](https://pro-docs.svc.vinted.com/)
