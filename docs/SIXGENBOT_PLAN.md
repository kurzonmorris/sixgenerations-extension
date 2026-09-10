# sixgenbot — the build plan

The Python service that becomes the system. Named `sixgenbot`, modular by
design, built in stages, **Vinted only** until Vinted works properly.

Architecture background is in `docs/SYSTEM_ARCHITECTURE.md`; this is how it
actually gets built.

---

## 1. One correction to the stage order

You proposed: **web interface → database → import tool → manual Vinted update.**

Everything about that is right except the first two being that way round. A web
interface built over an empty database is a wireframe — you cannot tell whether
the Table's search is any good until it is searching 2,000 real garments, and you
cannot tell whether the dashboard is calm enough until it has real numbers on it.

The fix is small: **put a database and real data in before the screens that
display them**, while still having something you can open in a browser on day
one.

| | Yours | Suggested |
|---|---|---|
| 1 | Web interface | **Skeleton** ✅ built — it runs, it logs, one page says it is alive |
| 2 | Database | **Database** — the schema, empty |
| 3 | Import tool | **Import** — Crosslist export + your five-year ledger. ~2,000 real items |
| 4 | Manual Vinted update | **Web interface** — the Table and the dashboard, over real data |
| 5 | | **Vinted read** |
| 6 | | **Vinted update** |

You still see a browser page at the end of stage 1. You just do not build the
Table until there is something in it.

**If you would rather do it your way, say so and it happens your way** — it costs
a bit of rework on the screens, nothing more.

## 2. The stages

Each one ends with something that works on its own. Nothing later is needed to
make an earlier stage useful.

### Stage 1 — the skeleton *(v_0.1.0)* — **BUILT 2026-09-10**

The spine everything else plugs into. No features.

- `sixgenbot` runs as a container, and as `python -m sixgenbot` on a desktop.
- **Config** in one readable file (D-212), secrets separate and never in the repo.
- **Logging** you can actually read (D-207), to file and to the Console screen later.
- **The module loader** — the thing that makes all the rest possible (§3).
- **One page**: *"sixgenbot is running. 0 items. No modules loaded."*
- Health check, clean restart, survives a reboot (D-206).
- `docker-compose.yml`, one volume.

**Done when:** it starts on the server by itself and the page loads from your
phone over Tailscale.

**Built.** 23 tests, two example modules, a health check, and a `check` command.
What is in it, file by file: `EXPLAINED_six-generations_Extension.md` §3B.
**Still to confirm: that it actually starts on your server and reaches your
phone** — that is the half of "done" only you can test.

### Stage 2 — the database *(v_0.2.0)*

- SQLite, one file, in the volume (D-043, D-044).
- The schema from `docs/DATA_MODEL.md`: items, attributes, categories, listings,
  images, orders, messages, purchases, lots, events.
- **Migrations from the start.** Every schema change is a numbered file that runs
  once. Without this, changing the shape of the data later means hand-surgery on
  a live database.
- Nothing is ever deleted — status changes instead (D-050).
- Nightly backup: database + images, onsite, plus offsite to pCloud (D-048, S-11).

**Done when:** a backup can be restored into an empty container and the data is
all there (D-051). Not "when the tables exist" — when a restore has been *tried*.

### Stage 3 — import *(v_0.3.0)*

Real data, without touching Vinted at all.

- **Crosslist CSV** (D-220) — your own export, the fastest 2,000 items available.
- **The ledger** `six_generations_2.xlsx` (L-11) — 63 sheets, 2,864 sales, five
  years, with the traps listed in `docs/EXISTING_LEDGER.md §5`.
- **CSV import generally** (D-059), so a hand-edited file can be read back.
- Every import is a **dry run first**: what it would create, change and skip,
  before anything is written (D-093, D-195).
- An import can be run twice without doubling anything.

**Done when:** the database holds your real inventory and five years of sales,
and a second run of the same file changes nothing.

### Stage 4 — the web interface *(v_0.4.0)*

Now there is something to look at.

- **The Table** first (U-13, `docs/INTERFACE_LAYOUT.md §5`) — one search box across
  every field, filters, in-place editing. The most-used screen, and the one that
  answers *"do you have anything with velvet in it?"*
- **The dashboard** (U-09, §2-3) — "needs fixing" above "needs you" above the
  counts and the money.
- The left menu, settings, and the Console viewer (U-10).
- Server-rendered HTML. **No JavaScript framework, no build step** — which is
  most of how the "nothing moves" requirement gets met for free.

**Done when:** she can find any garment in one search, and the dashboard is calm
enough to use daily. Show her stage 4 before stage 5 exists.

### Stage 5 — reading Vinted *(v_0.5.0)*

- The extension reads the wardrobe and posts it to sixgenbot (S-06, Q27).
- **Match on the SKU**, port `storageCode.js` to Python — including the
  five-digit item numbers (§7.7 of the EXPLAINED file).
- New / changed / missing detection, with everything recorded.
- Photos downloaded at full resolution, numbered in original order, deduplicated
  by content hash (D-031, D-032, D-033).
- The "needs review" queue starts to fill.

**Done when:** a read of the live wardrobe produces a sensible plan and no
surprises, in dry run, twice.

### Stage 6 — updating Vinted *(v_0.6.0)*

- Write a price. Hide or delete a sold listing. Update a description **without
  losing the SKU**.
- Detect a sale, and the reversible holding area (X-06).
- Then, and only then, eBay and Shopify.

**Done when:** parity runs both ways on Vinted alone. That is what earns
`v_1.0.0` later, once the other two platforms join.

## 3. How the modules work

You want features that cannot break each other. Three rules do almost all of
that work, and they are the same rules that already keep the extension's tests
runnable without a browser.

### 3.1 The layout

```
sixgenbot/
├── __main__.py              python -m sixgenbot serve | import | backup | check
├── core/                    everything a module is allowed to depend on
│   ├── config.py            one readable settings file, secrets separate
│   ├── database.py          connection, session, migrations
│   ├── models.py            the shared tables from DATA_MODEL.md
│   ├── events.py            the notice board (§3.3)
│   ├── logging.py
│   ├── moduleLoader.py      finds, validates and registers modules
│   └── webApp.py            the app, the base template, the menu
│
├── modules/                 one folder per feature. Drop-in, like ikabot's
│   ├── inventoryTable/
│   │   ├── module.py        NAME, VERSION, register()
│   │   ├── routes.py        its own pages
│   │   ├── queries.py       its own database reads
│   │   ├── templates/
│   │   └── tests/
│   ├── dashboard/
│   ├── importer/
│   ├── vintedReader/
│   ├── backups/
│   └── console/
│
└── tests/                   whole-system tests
```

### 3.2 The three rules

1. **A module never imports another module.** Not once, not "just this time".
2. **`core/` never imports a module.** The loader finds them by looking, not by
   naming them.
3. **Modules talk through the database and the event bus, never directly.**

Break rule 1 and you have the thing you are trying to avoid: changing the
importer breaks the dashboard. Keep it, and a module can be deleted from the
folder and everything else still starts.

**A test enforces rule 1**, so it cannot rot quietly.

### 3.3 What a module registers

```python
NAME = "inventoryTable"
VERSION = "v_0.1.0"
REQUIRES = []              # core features, never other modules

def register(bot):
    bot.addRoutes(routes.router)          # its own pages
    bot.addMenuItem("The Table", "/table", group="ITEMS")
    bot.addJob(refreshCounts, minutes=30) # its own scheduled work
    bot.onEvent("item.changed", recount)  # reacts to things
    bot.addMigrations("migrations/")      # its own tables, if it needs any
```

That is the whole contract. A new feature is a new folder with a `module.py` in
it — nothing in `core/` changes, and nothing else needs to know it arrived.

### 3.4 The event bus, in one paragraph

When something happens — an item changes, a sale is detected, an import
finishes — the module that noticed publishes a named event. Any module that
cares subscribes. The publisher does not know who is listening, so adding a
listener (a notification, a log line, a counter) never touches the code that
published it. This is how the notification module will later hear about sales
without the Vinted module knowing notifications exist.

## 4. The stack

**Recommended: FastAPI + Jinja templates + SQLite (SQLAlchemy) + APScheduler,
served by uvicorn, in one container.**

| Choice | Why this one |
|---|---|
| **FastAPI** | Routers are per-module by design, which is exactly the modularity you want. It also validates what the extension posts, which will be a large untrusted payload |
| **Jinja templates** | Server-rendered HTML. No React, no build step, no bundler. A page that is drawn on the server and then sits still is most of the calm-interface requirement met by construction |
| **SQLite** | One file. Copy it, back it up, move it to HexOS. Handles millions of rows. Postgres later changes one line if it is ever needed |
| **SQLAlchemy** | Lets the models be defined once and swapped to Postgres without rewriting queries |
| **APScheduler** | In-process scheduling. No cron, no second container |
| **pytest** | One test folder per module |

Endpoints stay **synchronous** (`def`, not `async def`) — FastAPI runs them in a
thread pool, and it keeps SQLite and the scheduler simple. Async buys nothing
for one user.

**The alternative is Flask**, which is a little simpler to read and has no
validation layer. If you would rather have that, it is a fair trade and the
module design above is unchanged.

**No JavaScript framework either way.** A little vanilla JS for the search box
and in-place editing, and nothing else.

## 5. Where it lives

Proposal: **this repo, in a new top-level `sixgenbot/` folder**, beside the
existing extension.

- The extension and the bot have to stay in step — the extension posts to the
  bot — and one repo means one commit changes both.
- All the documentation is already here.
- The repo name becomes wrong (`sixgenerations-extension` for something mostly
  not an extension). Renaming a GitHub repo is painless and redirects old links,
  so it can happen whenever.

→ **Q42** if you would rather sixgenbot had its own repo.

## 6. Conventions

Following `docs/Explained-user_kurzon.md` and what is already here:

- **camelCase filenames** — `moduleLoader.py`, `vintedReader/`. Not Python's
  usual style, but it matches your ikabot modules and this repo.
- **Version in `module.py` as `VERSION`, not in the filename.** Python cannot
  import `vintedReader.py_v1.0.0` — the dots break it. Each module carries its
  own version; `sixgenbot` carries the overall one. → **Q43**
- **Every module gets a row in `docs/FILE_STRUCTURE.md`.**
- `EXPLAINED_six-generations_Extension.md` and
  `FEATURE_six-generations_creep.md` updated in the same commit, every time.
- Dry run stays the default everywhere it can write.

## 7. What I would build first

Stage 1, in one go: the container, the config, the logging, the module loader,
the one page, the compose file, and two example modules so the loader is proven
rather than assumed. Roughly a day's work, and it ends with something running on
your server that you can open from your phone.

Then stop, and you look at it before stage 2.

## 8. Answered

- **Q42** one repo. **Q43** `v_0.1.0`. **Q44** FastAPI. **Q45** corrected order.

All settled 2026-09-10, and stage 1 is built against them.
