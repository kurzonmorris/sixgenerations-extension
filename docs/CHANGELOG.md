# Changelog

Newest first. The top entry must always match `manifest.json` and the root
`VERSION_v_x.x.x` marker file — `tests/versionConsistency.test.mjs` enforces it.

Version rules are in [VERSIONING.md](VERSIONING.md).

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
