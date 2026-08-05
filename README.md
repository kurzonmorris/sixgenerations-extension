# Six Generations — Vinted ↔ Shopify Sync

**v_0.1.0**

A Chrome extension (Manifest V3) that keeps the Six Generations **Vinted**
wardrobe and **Shopify** store in parity — stock, price, and listing content.
Built around garments, not generic products.

> **Status:** reads both sides and reports every difference. Shopify writes work.
> **Vinted writes do not exist yet** — that is the road to v_1.0.0.
> Dry run is **on by default**; nothing is written until you turn it off.

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
| **[docs/PROJECT_INFO.md](docs/PROJECT_INFO.md)** | API and web-code reference: endpoints, headers, mutations, rate limits, bot protection. Researched once and kept |
| **[docs/FILE_STRUCTURE.md](docs/FILE_STRUCTURE.md)** | What every file is for |
| **[docs/FUTURE_FEATURES.md](docs/FUTURE_FEATURES.md)** | The backlog, F-01 to F-20 |
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
