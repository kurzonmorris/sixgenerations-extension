# CLAUDE.md — read this first

Project memory for the Six Generations extension. **This repo does not rely on
chat history.** Everything needed is in `docs/`.

## What this is

A Chrome extension (Manifest V3) that bridges the three places the same
second-hand garments are sold — **Vinted**, **eBay** and the **Shopify** store —
keeping stock, price and listing content in step, and recording purchases and
sales in a spreadsheet. The products are clothes, and the code is built around
garments (size, brand, colour, condition) rather than generic products.

**Vinted is the primary platform** — items are created there and mostly sell
there. eBay and Shopify are fed from it.

Current version: **v_0.1.0** — Vinted and Shopify are read and compared, and
Shopify writes work. **Vinted writes do not exist yet. eBay is not connected at
all. The ledger is not built. There is no server yet.**

**Where it is going:** a small Chrome extension that reads Vinted in the user's
own signed-in session, handing everything to a **Python Docker container** on the
home server that owns the database, the images, the orders, the notifications and
the eBay/Shopify writes. `docs/SYSTEM_ARCHITECTURE.md` explains why it is split
that way and why Vinted cannot move to the server.
`docs/OPEN_QUESTIONS.md` Q14–Q33 are what block it.

**The interface is a hard requirement, not styling.** The person who uses this
daily has autism, ADHD and sensory sensitivities: a busy screen makes the tool
unusable. `docs/INTERFACE_PRINCIPLES.md` overrides normal UI convention.

**The pairing key is the storage code** (`13-8 24` = column 13, box 8, item 24)
at the end of every listing description. Not the SKU field — that is only on some
items. Confirmed on Vinted and Shopify; **whether eBay carries it is Q16**, and
on eBay it may belong in the SKU field instead (`docs/PROJECT_INFO.md §3.5`).
See `docs/PROJECT_INFO.md §2A`.

## The two files that must never go stale

| File | Rule |
|---|---|
| **`EXPLAINED_six-generations_Extension.md`** | The project's memory: how the code works, which lines matter, platform facts, traps, and a parking lot of things found but not used. **Update it in the same commit as every code change and every investigation.** Never delete from the parking lot |
| **`FEATURE_six-generations_creep.md`** | Everything the system does today, plus everything planned or floated. **Check Part A before building anything** — it may already exist. Move a feature from Part D to Part A on the day it works |

`doyouwantfeatures.md` is the pick-list awaiting yes/no answers. A ticked item
moves into the creep file's Part D; a declined one stays recorded so the same
idea does not come round again.

## Read these before working

| File | When |
|---|---|
| `EXPLAINED_six-generations_Extension.md` | **First, every session.** What is known and how it works |
| `FEATURE_six-generations_creep.md` | **Before building anything.** It may already exist |
| `docs/SYSTEM_ARCHITECTURE.md` | Before any structural work. Extension vs container, and why |
| `docs/DATA_MODEL.md` | Before touching item fields, images, or the CSVs |
| `docs/CLAUDE_BROWSER_TASKS.md` | When something needs finding out from a live site |
| `docs/FEATURE_SPECIFICATION.md` | **Before starting anything new.** What the product is meant to be, all three platforms plus the ledger, and the build order |
| `docs/PROJECT_INFO.md` | **Before any API work.** Endpoints, headers, mutations, rate limits, bot protection, field names. Researched already — do not go looking again. §3 (eBay) is unverified — read it before believing it |
| `docs/INTERFACE_PRINCIPLES.md` | **Before touching any screen.** Non-negotiable |
| `docs/LEDGER_DESIGN.md` | Before any purchases/sales work |
| `docs/CROSS_LISTING_TOOLS_RESEARCH.md` | Prior art. Worth ten minutes before designing a feature from scratch |
| `docs/OPEN_QUESTIONS.md` | **At the start of a session.** Decisions taken without an answer. Check whether any have been settled |
| `docs/FILE_STRUCTURE.md` | Before adding a file, or when looking for where something lives |
| `docs/FUTURE_FEATURES.md` | Before starting a feature — it may already have an ID (F- Vinted/Shopify, E- eBay, L- ledger, U- interface, X- cross-platform) |
| `docs/VERSIONING.md` | Before touching a version number |
| `docs/Explained-user_kurzon.md` | How Kurzon works: communication style, conventions, expectations |

## Rules for this repo

1. **Ask, do not assume.** If a decision is not covered by these docs, ask. If it
   cannot be asked, take the cheapest reversible option and add it to
   `docs/OPEN_QUESTIONS.md` with the reasoning.
2. **Write findings down.** Anything researched about any platform goes into
   `EXPLAINED_six-generations_Extension.md` in the same commit — confirmed facts
   in the body, anything found but not yet used in the §9 parking lot. Verified
   API detail also goes to `PROJECT_INFO.md`. The next session starts cold.
   **Update `FEATURE_six-generations_creep.md` whenever a feature's status
   changes.**
3. **Never bump a version without being given the number.** Then follow the
   checklist in `VERSIONING.md` — all five places.
4. **Filenames say what they do.** camelCase, descriptive. Add a row to
   `FILE_STRUCTURE.md`.
5. **Commit and push when a task is done**, without being asked.
6. **Branch names describe the work**: lowercase, hyphens, topic in the name.
7. **The Shopify token never leaves `chrome.storage.local`** — not in the repo,
   not in an export, not in a log line.
8. **Dry run stays the default.** Nothing writes to a live store until the user
   turns it off.
9. Minimal, focused changes. No speculative abstractions, no comments that
   restate the code.
10. **No third-party server, no account, no subscription.** Everything runs on
    the one machine. That is the whole point of building this instead of paying
    for Vendoo or List Perfectly.
11. **Nothing on screen that does not need to be there.** No animation, no
    toasts, no dashboards, no jargon on the first screen.
    `docs/INTERFACE_PRINCIPLES.md` has the full list, and it wins over normal UI
    convention.

## Layout at a glance

```
manifest.json          Chrome entry point
VERSION_v_0.1.0        version marker (rename on bump)
source/
  backgroundServiceWorker.js   coordinator; the ONLY place Shopify calls may happen
  core/                        platform-agnostic logic (parityEngine is the heart)
  connectors/                  one file per platform
  contentScripts/              runs inside the Vinted tab
  popupPanel/  settingsPage/   UI
tests/                 npm test — 36 tests, nothing to install
docs/                  everything above
```

Dependency direction: UI → worker → core/connectors → content script.
`core/` never imports `connectors/`, except `syncRunner.js`.

## Checks before saying a task is done

```bash
npm test                      # includes the version-consistency check
node --check <changed file>   # for anything Chrome loads
```

Then: reload the extension at `chrome://extensions`, and confirm a **dry run**
still produces a sensible plan.
