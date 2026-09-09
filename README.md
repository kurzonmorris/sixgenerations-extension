# Six Generations — marketplace bridge

**v_0.1.0**

A Chrome extension (Manifest V3) that keeps the same second-hand garments in step
across **Vinted**, **eBay** and the **Shopify** store — stock, price and listing
content — and records what each one cost and what it sold for. Built around
garments, not generic products.

> **Status today:** Vinted and Shopify are read and compared; Shopify writes work.
> **Vinted writes do not exist yet.** **eBay is not connected yet**, and the
> ledger is not built. Dry run is **on by default**; nothing is written until you
> turn it off.
>
> Where it is going is in **[docs/FEATURE_SPECIFICATION.md](docs/FEATURE_SPECIFICATION.md)**.
> A dozen questions have to be answered before the eBay and ledger work can start
> — they are in **[docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md)**.

---

## Quick start

```powershell
git clone https://github.com/kurzonmorris/sixgenerations-extension.git
```

`chrome://extensions` → **Developer mode** on → **Load unpacked** → pick the
cloned folder. No build step.

Then follow **[docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** to connect the Shopify
custom app and the Vinted session.

## Documentation

| File | What is in it |
|---|---|
| **[docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** | Install, connect both sites, first run, troubleshooting |
| **[EXPLAINED_six-generations_Extension.md](EXPLAINED_six-generations_Extension.md)** | **The project's memory.** How the code works, which lines matter, every platform fact, every trap, and a parking lot of things found but not used |
| **[FEATURE_six-generations_creep.md](FEATURE_six-generations_creep.md)** | **Everything the system does today**, plus everything planned. Check here before asking for something twice |
| **[doyouwantfeatures.md](doyouwantfeatures.md)** | 252 possible features — 118 answered yes, with Kurzon's own notes; sections 11–24 still open |
| **[docs/INTERFACE_LAYOUT.md](docs/INTERFACE_LAYOUT.md)** | The dashboard, the left menu and the item Table, as asked for |
| **[docs/EXISTING_LEDGER.md](docs/EXISTING_LEDGER.md)** | Five years of real books, analysed — and what the new system must not lose |
| **[docs/SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md)** | Extension vs Docker container, and why Vinted cannot move to the server |
| **[docs/DATA_MODEL.md](docs/DATA_MODEL.md)** | Items with several sizes, colours and categories at once; images; orders; the four CSVs |
| **[docs/CLAUDE_BROWSER_TASKS.md](docs/CLAUDE_BROWSER_TASKS.md)** | Ready-to-paste prompts for gathering facts from the live sites |
| **[docs/FEATURE_SPECIFICATION.md](docs/FEATURE_SPECIFICATION.md)** | What the whole product is meant to do — three platforms and the ledger — and the order to build it in |
| **[docs/PROJECT_INFO.md](docs/PROJECT_INFO.md)** | API and web-code reference: endpoints, headers, mutations, rate limits, bot protection. Researched once and kept |
| **[docs/INTERFACE_PRINCIPLES.md](docs/INTERFACE_PRINCIPLES.md)** | The rules every screen must follow. A requirement, not styling |
| **[docs/LEDGER_DESIGN.md](docs/LEDGER_DESIGN.md)** | The purchases and sales spreadsheet |
| **[docs/CROSS_LISTING_TOOLS_RESEARCH.md](docs/CROSS_LISTING_TOOLS_RESEARCH.md)** | What Vendoo, List Perfectly, Crosslist and the rest do, and why none of them handles Vinted |
| **[docs/FILE_STRUCTURE.md](docs/FILE_STRUCTURE.md)** | What every file is for |
| **[docs/FUTURE_FEATURES.md](docs/FUTURE_FEATURES.md)** | The backlog — F- Vinted/Shopify, E- eBay, L- ledger, U- interface, X- cross-platform |
| **[docs/VERSIONING.md](docs/VERSIONING.md)** | The `v_x.x.x` rules and the bump checklist |
| **[docs/CHANGELOG.md](docs/CHANGELOG.md)** | What changed in each version |
| **[docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md)** | Decisions taken without an answer — worth a read |
| **[CLAUDE.md](CLAUDE.md)** | Project memory and working rules |

## How it works

```
   Vinted tab  ──►  vintedPageReader  ──►  vintedWardrobeConnector ─┐
  (your session)                                                    ├─►  parityEngine  ──►  plan
   Shopify Admin GraphQL  ──►  shopifyStoreConnector ────────────────┘                        │
                                                                                              ▼
                                                              dry run: report  |  live: apply
```

- **Matching** is by the storage code already at the end of every description on
  both sites — `13-8 24`, meaning column 13, box 8 high, item 24. SKU fields are
  used only where a code is missing. Title + size is a last resort: it is shown
  in the plan as *review-match* and is **never written from**.
- **Direction is per field group.** Stock defaults to Vinted → Shopify (a garment
  usually sells on Vinted first), price and content default to Shopify → Vinted.
  Each can be reversed or switched off.
- **Sizes are normalised** before comparison, so `UK 10`, `Size 10` and `10` never
  register as a difference. This is the main thing generic sync tools get wrong
  for a wardrobe.
- **Everything is logged** — every planned action with before/after values, every
  failure with the platform's own message. **Export report** writes it all to JSON
  with the token redacted, which is the handover point for any external monitor.

## Tests

```bash
npm test
```

36 tests, no dependencies to install — Node's built-in runner. They cover the
storage-code parsing and its false-match guards, the matching and diff rules,
the service worker's message handling, token redaction, and that the version has
not drifted between the five places it appears.

## Security

- The Shopify Admin token is store-owner-grade. It lives in
  `chrome.storage.local` on one machine, is never synced to a Google account, and
  is redacted from exports. Revoke the custom app if the machine is shared or
  lost.
- Host permissions cover Vinted domains and `*.myshopify.com` only.
- No third-party servers, no telemetry.

## On Vinted's terms

Vinted restricts automated access. This extension acts only as the signed-in
user, at human scale, on that user's own wardrobe — no anonymous scraping, no
other members' data, no traffic without a session. Keep automatic intervals
conservative; account risk is yours.
