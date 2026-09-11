# Changelog

Newest first. The top entry must always match `manifest.json` and the root
`VERSION_v_x.x.x` marker file — `tests/versionConsistency.test.mjs` enforces it.

Version rules are in [VERSIONING.md](VERSIONING.md).

---

## sixgenbot v_0.2.0 — 2026-09-11 · stage 2, the database

The database, and the backup that has actually been restored. 50 pytest tests,
37 extension tests.

- **The full schema** from `docs/DATA_MODEL.md` in one numbered migration:
  items, multi-value attributes, categories, listings, images, orders, messages,
  lots, purchases, posting trips and events. Money in integer pence, dates in
  ISO-8601, statuses `CHECK`-constrained so a typo is refused rather than stored.
- **Migrations run on every start**, each atomically. A deliberately broken
  migration is used in the tests to prove a failure leaves no trace.
- **Full-text search across everything** — title, description, brand, SKU,
  private notes, every attribute and every category, in one query. Whatever
  someone types is quoted first, so a stray `"` or `*` cannot become FTS syntax.
- **Nightly backup at 02:30**, taken with SQLite's own online backup rather than
  a file copy, then verified by opening it. Newest 14 kept.
- **Restore is a command, not a button**, and keeps whatever it replaced as
  `.beforeRestore`. **The round trip runs on every test:** fill, back up, delete,
  restore, check every row came back.
- **Scheduler** — `bot.addJob(name, when, run)`. A job that throws is logged and
  the rest carry on.
- **`docs/INSTALL_GUIDE.md`** — copy-and-paste from clone to running container,
  with and without Compose, plus backup, restore, update and troubleshooting.

**Changed from the approved plan: plain `sqlite3`, not SQLAlchemy.** The
migrations then describe the schema and nothing can drift from them, and FTS5 is
native. Reversible — see `OPEN_QUESTIONS.md` Q46.

**Two bugs the tests found before they could matter:**

- `sqlite3.executescript()` commits any open transaction before it runs, so
  wrapping a migration in `BEGIN`/`COMMIT` did not work — and a migration failing
  halfway would have left a half-built schema. `BEGIN` and `COMMIT` now live
  inside the script.
- Backups were named to the minute, so pressing "Back up now" twice in one minute
  silently overwrote the first.

**Left for later on purpose:** images are not in the backup yet (immutable and
deduplicated, so they want copying rather than snapshotting), and the offsite
copy is a folder for pCloud to sync rather than code holding a password.

---

## Unreleased — 2026-09-10 · sixgenbot v_0.1.0, stage 1

**First Python code.** `sixgenbot/` — the server that will own the database, the
images, the orders and the platform writes. Stage 1 is the skeleton: it runs, it
logs, it loads modules, and it serves two pages. **No database, no Vinted, no
scheduler.**

Answers that shaped it: one repo, `v_0.1.0`, FastAPI, corrected stage order.

**The module system, which is the point of stage 1:**

- A feature is a folder under `sixgenbot/modules/` with a `module.py` declaring
  `NAME`, `VERSION` and `register(bot)`. Core names none of them.
- `register()` can add routes, a menu item, an event handler and a template
  directory. **`addJob` and `addMigrations` deliberately do not exist yet** —
  they arrive with the scheduler and database, and a function that silently does
  nothing is worse than one that is absent.
- **A broken module is reported and skipped; everything else still starts.**
  Proved against three deliberately broken fixtures, not trusted.
- Two `ast` tests enforce the rules that make it work: **a module never imports
  another module**, and **core never imports a module**.
- Switching a module off is a line in `config.toml`.

**Also in:** settings in `config.toml` with secrets in a separate `secrets.toml`
(environment wins, so Docker can inject, and secrets never pass through the
settings dict); logging to console, rotating file and an in-memory ring buffer
the Console page reads; a health check that returns 503 when a module failed;
`python -m sixgenbot check` to load everything and report without opening a port;
Dockerfile and compose file, one volume.

**The stylesheet is enforced, not just written.** A test strips the CSS comments
and then fails on any `transition`, `animation`, `:hover` rule, pure white or
pure black — `INTERFACE_PRINCIPLES.md` U-03 and U-04 as a test rather than a
promise.

Verified: 23 pytest tests, 37 extension tests, and the service was run — pages
served, health returned ok, a deliberate port clash reported itself clearly.
**Not verified: that it starts on the Unraid server and reaches a phone over
Tailscale.** That half of "done" needs Kurzon.

---

## Unreleased — 2026-09-10 · sixgenbot planned

**Documents only. No code changed.**

- **`docs/SIXGENBOT_PLAN.md`** — how the Python service gets built. Six stages,
  each ending in something that works on its own: skeleton → database → import →
  web interface → Vinted read → Vinted write. Vinted only; eBay and Shopify wait.
- **One correction to the proposed order**: database and import before the web
  interface, because the Table's search cannot be judged over an empty table and
  the dashboard cannot be judged without real numbers. A browser page still
  exists at the end of stage 1.
- **The module contract**: one folder per feature with a `module.py` exposing
  `NAME`, `VERSION` and `register(bot)`. Three rules do the work — modules never
  import each other, `core/` never imports a module, and they communicate through
  the database and an event bus. A test enforces the first, so it cannot rot.
- **Stack recommended**: FastAPI + Jinja + SQLite/SQLAlchemy + APScheduler,
  synchronous endpoints, one container. Server-rendered HTML, no JavaScript
  framework, no build step — which is most of the "nothing moves" requirement met
  by construction. Flask offered as the plainer alternative.
- Q42–Q45 added: one repo or two, sixgenbot's starting version, FastAPI or Flask,
  and whether to correct the stage order.

Version deliberately **not** bumped — no new number was given.

---

## Unreleased — 2026-09-09 (4) · the SKU is permanent, and a bug that found

**One code fix**, and it matters: `source/core/storageCode.js` and the
hand-copied regex in `source/contentScripts/vintedPageReader.js` accepted only
**four digits** for the item number. Kurzon's own example, `5-6 17735`, would
have parsed as **no code at all** — the garment would have shown as unmatched,
silently, with nothing in the log to say why. Now five digits (99,999 per box),
with a test covering `5-6 17735` and `13-8 99999`. 37 tests pass.

Why it was wrong: the limit was sized against *how many items a box holds*
(20-40) when it needed to be sized against *how many have ever been in it*.

- **The SKU is permanent and never recycled.** A returned garment keeps its
  number, goes back in the same box, and its listing is re-published unchanged —
  recycling the number would make it a different item. So the SKU is identity and
  the internal UUID is only a surrogate; the re-boxing hazard drops from routine
  to rare, and Q11 is largely closed.
- **The dashboard's job is settled**: fixing what broke in the copying comes
  first, seeing how things are going comes second, everything else is "useful,
  not essential". The home page was reordered so problems sit above counts, and
  it now shows items listed today — the number that decides whether the backlog
  clears.

Version deliberately **not** bumped — no new number was given.

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
