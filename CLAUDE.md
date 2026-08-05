# CLAUDE.md — read this first

Project memory for the Six Generations extension. **This repo does not rely on
chat history.** Everything needed is in `docs/`.

## What this is

A Chrome extension (Manifest V3) that keeps the Six Generations **Vinted**
wardrobe and **Shopify** store in parity — stock, price, and listing content.
The products are clothes, and the code is built around garments (size, brand,
colour, condition) rather than generic products.

Current version: **v_0.1.0** — reads both sides and reports every difference.
Shopify writes work. **Vinted writes do not exist yet.**

**The pairing key is the storage code** (`13-8 24` = column 13, box 8, item 24)
at the end of every listing description, on both platforms. Not the SKU field —
that is only on some items. See `docs/PROJECT_INFO.md §2A`.

## Read these before working

| File | When |
|---|---|
| `docs/PROJECT_INFO.md` | **Before any API work.** Endpoints, headers, mutations, rate limits, bot protection, field names. Researched already — do not go looking again |
| `docs/OPEN_QUESTIONS.md` | **At the start of a session.** Decisions taken without an answer. Check whether any have been settled |
| `docs/FILE_STRUCTURE.md` | Before adding a file, or when looking for where something lives |
| `docs/FUTURE_FEATURES.md` | Before starting a feature — it may already have an ID (F-01…F-20) |
| `docs/VERSIONING.md` | Before touching a version number |
| `docs/Explained-user_kurzon.md` | How Kurzon works: communication style, conventions, expectations |

## Rules for this repo

1. **Ask, do not assume.** If a decision is not covered by these docs, ask. If it
   cannot be asked, take the cheapest reversible option and add it to
   `docs/OPEN_QUESTIONS.md` with the reasoning.
2. **Write findings down.** Anything researched about Vinted or Shopify goes into
   `PROJECT_INFO.md` in the same commit. The next session starts cold.
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
