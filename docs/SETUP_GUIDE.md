# Setup Guide

Written for the **Windows VM**, since that is where this will be run. The steps
are identical on SteamOS apart from the paths.

---

## 1. Get the files

```powershell
cd %USERPROFILE%\Documents
git clone https://github.com/kurzonmorris/sixgenerations-extension.git
```

To update later:

```powershell
cd %USERPROFILE%\Documents\sixgenerations-extension
git pull
```

There is **no build step**. Chrome loads the folder exactly as it is.

## 2. Load it into Chrome

1. Go to `chrome://extensions`
2. Turn on **Developer mode** (top right)
3. **Load unpacked**
4. Select `%USERPROFILE%\Documents\sixgenerations-extension`
   — the folder containing `manifest.json`, not a subfolder

The toolbar icon appears, showing **v_0.1.0** in the popup header. After a
`git pull`, press the **reload** arrow on the extension card to pick up changes.

## 3. Connect Shopify

In the store admin:

1. **Settings → Apps and sales channels → Develop apps → Create an app**
2. Name it something like `Six Generations Sync`
3. **Configure Admin API scopes** — tick exactly these four:
   - `read_products`
   - `write_products`
   - `read_inventory`
   - `write_inventory`
4. **Install app**, then reveal and copy the **Admin API access token**
   (starts `shpat_`). It is shown **once** — copy it now.

In the extension's settings page:

- **Store domain** — the permanent `xxx.myshopify.com` one, not a custom domain
- **Admin API access token** — paste it
- **API version** — leave at `2025-01` unless you have read
  `PROJECT_INFO.md §1.2` about what changes in newer versions
- Press **Test connection**. It should report the shop name and currency, and
  fill in the inventory location by itself.

### Keep the token safe

It has full product and inventory rights on the store. It is stored in
`chrome.storage.local` on that machine only — never synced to a Google account,
never written to the repo, and redacted from exported reports. If the VM is
shared or rebuilt, delete the custom app in Shopify to revoke it.

## 4. Connect Vinted

1. Sign in to Vinted normally, in a tab, on the domain set in settings
   (default `www.vinted.co.uk`)
2. Press **Test connection** in the extension settings

It should report the signed-in username. If it says *"No Vinted content script in
that tab"*, reload the Vinted tab — the extension was installed after the tab was
opened.

The extension never sees your Vinted password. It reads through the session that
tab already has.

## 5. Set up matching — do this before any live run

Shopify variants have a SKU field. Vinted has nothing equivalent, so the code
goes in the **Vinted listing description**:

```
Lovely wool coat, barely worn.

SKU: COAT-001
```

`SKU: COAT-001` or `[COAT-001]` both work. It must match the Shopify variant's
SKU exactly (case is ignored).

Anything without a SKU falls back to matching on title + size. That is reported
so you can see it, but it is **never** used to drive a write.

## 6. First run

1. Open the popup
2. Leave **Dry run** ticked
3. Press **Run sync**

You get a plan: how many matched, how many exist on only one side, and every
difference found. Nothing is written.

Read the plan carefully the first time — it is the fastest way to find garments
that are missing a SKU, or priced differently to what you expected.

Only when the plan looks right, untick **Dry run** and run it again.

## 7. Automatic runs

Off by default. The settings page offers 15 minutes to daily. Start with manual
or daily: Vinted sits behind bot protection (`PROJECT_INFO.md §2.4`), and there
is no reason to poll a wardrobe every quarter of an hour.

Automatic runs need a signed-in Vinted tab open, same as manual ones.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Shopify is not configured" | Domain or token empty | Fill both in on the settings page |
| "Shopify rejected the access token (401/403)" | Wrong token, or missing scopes | Re-check the four scopes, reinstall the custom app, copy the new token |
| "Not signed in on www.vinted.co.uk" | No Vinted session in that tab | Sign in to Vinted, then retry |
| "No Vinted content script in that tab" | Tab predates the extension | Reload the Vinted tab |
| "Vinted content script did not answer" | Page still loading, or Vinted changed something | Reload the tab; if it repeats, check the activity log for which read path was tried |
| Wardrobe reads as 0 items | Vinted changed their endpoint | Check the log for `via` — see `PROJECT_INFO.md §2.2` |
| "No Shopify location selected" | Location never resolved | Press **Test connection** on the settings page |
| Everything shows as "present on one side only" | SKUs do not match | Compare a Shopify variant SKU against the `SKU:` line in the matching Vinted description |

### Where to look when something goes wrong

1. **Popup → Activity** — the live log
2. **Export report** — the whole run as JSON, token redacted
3. `chrome://extensions` → **Service worker** link → Console — raw errors from
   the worker itself

## Running the tests

```powershell
cd %USERPROFILE%\Documents\sixgenerations-extension
npm test
```

21 tests, nothing to install — it uses Node's built-in runner. Worth running
after any change, and always after a version bump.
