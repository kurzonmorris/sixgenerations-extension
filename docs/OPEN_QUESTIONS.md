# Open Questions

Decisions taken **without an answer** because the questions could not be
answered in the session where they came up. Each one is cheap to reverse.

**Answer these and the choice gets locked in — or corrected — in the next
commit.** Delete a row once it is settled and record the outcome in CHANGELOG.md.

> **Why these live in a file:** the interactive question prompt has been
> unreliable in these sessions, and chat history is not project memory anyway.
> Answers can be given in plain chat or by editing this file directly.

---

# Answered — 2026-08-05

- **Q8 Shopify domain** → `1kaa6a-ua.myshopify.com`, storefront
  `sixgenerations.co.uk`. Recorded in PROJECT_INFO.md §1.1. **Plan still
  unknown** — it sets the rate-limit budget, so worth filling in.
- **Q9 Vinted domain** → `vinted.co.uk`. The other seven country domains have
  been removed from `host_permissions` and from the settings dropdown.
- **Q10 Scale** → **2000+ garments.** This broke two limits that were fine for a
  small wardrobe; both are fixed, see CHANGELOG.
- **Q1 / Q2 versioning** → keep `v_0.1.0` and the root marker file. Settled.
- **Matching** → storage codes (`13-8 24`) at the end of every description, on
  both platforms. This replaced the `SKU: ABC-123` convention entirely.

**Q7 (what to build next) was not answered.** The scale and key format answers
made the priority obvious on their own, so the read path was hardened first —
that work is done. The question is still open for what comes *after* a live dry
run.

---

# Answer these next

> **Q14–Q25 came in with the eBay + ledger + interface request; Q26–Q33 with the
> Docker/database/orders plan on 2026-09-08.**
> They are the ones that block work. Everything below Q13 is older and still
> open.

## Q14 — Build on what exists, or start again?

The request read like a fresh start: "create a base extension with minimal
features and slowly build it up". This repo already **is** that base — v_0.1.0
reads both platforms, matches on the storage code, writes to Shopify, and has 36
passing tests.

**Taken:** eBay and the ledger get added to this extension. Nothing is thrown
away. The build order is in `FEATURE_SPECIFICATION.md §4`.

**Say so if that is wrong** and the intent really was to start from an empty
folder.

## Q15 — eBay: API or tab? The big one

Full detail in `PROJECT_INFO.md §3.2`. eBay has a proper API, but refreshing the
token every 2 hours needs a client secret, and an extension cannot keep a secret.

1. **Secret in `chrome.storage.local`**, treated exactly like the Shopify token.
2. **A small helper on the Unraid server** holds the secret.
3. **No API** — drive `ebay.co.uk` in a tab, like Vinted.

Option 1 is the smallest step and matches how the Shopify token is already
handled. Option 3 is the only one with no credentials anywhere. **Nothing eBay
gets built until this is answered.**

## Q16 — What is in the eBay listings now?

- Do they carry the storage code (`13-8 24`)? In the description, or in the
  custom label / SKU field?
- If the SKU field is free, the code belongs there — it is exact-match and
  indexed, better than any of the three currently have (`PROJECT_INFO.md §3.5`).
- How many listings are there, and is it the same business account?

Without this, eBay pairing cannot be designed — only guessed at.

## Q17 — Which platform wins, for which field?

Two platforms means one choice per field. Three means a matrix. Fill it in:

| | Stock | Price | Title / description | Photos |
|---|---|---|---|---|
| **Wins** | ? | ? | ? | ? |

Current two-platform behaviour: stock Vinted → Shopify, price and content
Shopify → Vinted. Best guess for three is that Shopify stays the catalogue of
record for price and content while stock is "whoever sold it first wins" — but
that is a guess.

## Q18 — Does it need to work with the computer off?

An extension only runs while Chrome is open. A garment can sell on Vinted at 2am
and stay live on eBay until morning.

1. Accept it — run the check once or twice a day.
2. Leave Chrome open on the Unraid Windows VM.
3. Move the eBay half to the server (possible for eBay, impossible for Vinted).

## Q19 — Where does the spreadsheet live?

Options and trade-offs in `LEDGER_DESIGN.md §3`.

1. **Google Sheets** — live, works from a phone, extension-friendly OAuth.
2. **A local `.csv`/`.xlsx`** — no account, no cloud, but one-way.
3. **Inside the extension**, with export.

And: does a spreadsheet already exist? If purchases are being recorded somewhere
today, the design should match that rather than replace it. **Send a copy with
the columns and a couple of example rows** and this stops being a question.

## Q20 — The interface — ask her, not me

`INTERFACE_PRINCIPLES.md` is written from general neurodivergent-UX guidance. It
is a starting point, not an answer.

- Is she the only person who uses it day to day? On which machine?
- What specifically makes a screen unusable — density, movement, colour, choice,
  wording, all of it?
- Is there an app or site she finds **easy**? Copying something that already
  works beats designing from principles.
- Light or dark? Bigger text?

## Q21 — Job lots: how is cost split?

A £40 bin bag of 30 garments has no per-item price.

1. Even split (£1.33 each).
2. Weighted by what the item is worth.
3. Track the lot only, no per-item profit.

This changes the shape of the Purchases sheet, so it is worth settling early.

## Q22 — Private or business Vinted account?

Two consequences, both large:

- **Fees.** UK private sellers pay no selling fee; business (Pro) accounts do.
  The ledger's fee column depends on which this is.
- **A real API.** Vinted publishes API documentation for **business accounts**
  (`pro-docs.svc.vinted.com`). If this is a Pro account, the whole fragile
  tab-driven Vinted approach may be replaceable with a supported API — which
  would be the biggest single improvement available to this project.

## Q23 — How is a Vinted sale confirmed?

A listing disappearing is not proof of a sale — it may have been deleted, ended,
or hidden. The ledger must never invent a sale. What does the wardrobe actually
show for a sold item, and is there a sold/completed section that can be read?

## Q24 — Is quantity ever more than one?

Everything so far assumes one-of-a-kind garments: one item, three listings, and
selling it anywhere means removing it everywhere. If anything is stocked in
multiples, that assumption breaks and stock has to be counted rather than
switched.

## Q25 — Where does the "purchase" side come from?

Purchases have to be typed by someone — no platform provides them. Who types
them, when, and on what device? If it is on a phone at a car boot sale, that
alone decides Q19 in favour of Google Sheets.

---

## Q26 — Database or CSV as the store?

`docs/SYSTEM_ARCHITECTURE.md §5` argues: **SQLite is the store, CSVs are
exports.** At 100,000 items a pile of CSVs stops working, and "cut a row from one
file and paste it into another" is where data goes missing when something crashes
mid-write.

You still get all four files exactly as described — they are written from the
database, so they are always correct and can never lose a row.

**Say if you would rather the CSVs were genuinely the store.** It is your data
and your call; I would just be building something I expect to have to fix later.

## Q27 — How does the extension hand data to the container?

1. **Direct** — the extension POSTs the wardrobe to the container over the home
   network. Fast, automatic, needs the container's address in the settings.
2. **Via a file** — the extension saves a file, you drop it in a watched folder.
   Simpler, works even when the container is down, one manual step.

Option 1 with option 2 as the fallback is the obvious answer unless the machine
running Chrome cannot reach the server.

## Q28 — Automatic, or automatic with approval?

Per action type, probably:

| Action | Suggested |
|---|---|
| Delist something that sold | **Automatic** — the whole point, and the risk of not doing it is a double sale |
| Update a price to match | Automatic |
| Create a new listing on another platform | **Approval** — it costs money on eBay and is public |
| Delete anything | Approval, always |

## Q29 — Are original photos kept forever?

100,000 items × 5 photos × ~300 KB ≈ **150 GB**. That is fine on a server with
disks, but it should be a decision rather than a surprise. Options: keep all
originals; keep originals only for unsold items and compress the rest; keep
originals for 2 years then compress.

## Q30 — How long are buyer details kept?

Financial records for 5 years is normal and is what the archive is for. Buyer
names, addresses and message histories are personal data and are a separate
question. A reasonable default: full record for as long as a return or dispute is
possible, then trim the address and the message bodies, keeping the money.

Not legal advice — worth deciding deliberately rather than by accident.

## Q31 — Is the web interface reachable from outside the house?

Home network only is simpler and safer. Reachable from a phone anywhere is more
useful when standing at a car boot sale, and needs a password in front of it.

## Q32 — What happens to the existing Chrome extension?

Under the new plan it shrinks to one job: read Vinted, hand it over, and later
perform Vinted writes. Everything else moves to the container. Nothing is thrown
away — `docs/SYSTEM_ARCHITECTURE.md §10` lists where each piece goes.

## Q33 — Where do buyer messages go in `sold_items.csv`?

A conversation inside a spreadsheet cell is unreadable. Options: a separate text
file per order, referenced from the row (recommended); all messages joined into
one cell; or a separate `messages.csv` with one row per message.

---

## Q11 — What happens when a garment is re-boxed?

The pairing key is a *physical location*. Move a garment to a different box and
update only one platform, and the pair breaks — both sides then report as
one-sided. That is the safe failure rather than a wrong edit, but at 2000 items
it will happen regularly.

Options:
1. **Leave it.** Re-boxing means editing both listings by hand, as now.
2. **Build the re-box helper (F-22).** Change the code on both platforms in one
   action. Needs Vinted writes (F-02) first.
3. **Add a second, stable key** — a code that never changes when an item moves —
   and treat the storage code as location data rather than identity.

Option 3 is the robust answer but means touching all 2000 listings once.

## Q12 — Do Shopify SKU fields hold the same storage code?

You said SKUs are on *some* items on both platforms. If a Shopify variant's SKU
field contains something **other** than the storage code, and that item's
description has no code, it will never pair with its Vinted twin.

Knowing what those SKU fields actually contain decides whether the SKU fallback
is useful or should be dropped.

## Q13 — Are storage codes unique per garment?

The engine assumes one garment per code. If a box can hold two items that share
`13-8 24`, the first wins and the second is reported as one-sided.

---

# Earlier decisions, taken without an answer

## Q1 — Version format: `v_0.1.0` or `.js_v0.1.0` on every file?

**Asked because:** the request said `v_x.x.x`, while `Explained-user_kurzon.md`
§3 says versions go after the file extension (`syncRunner.js_v1.0.0`).

**Taken:** `v_x.x.x` as written in the request. One marker file
(`VERSION_v_0.1.0`) at the root, plus the number in the manifest and both UI
headers. Source filenames carry no version.

**Why:** Chrome cannot load a file named `syncRunner.js_v0.1.0`. Per-file
versions would need a build step that copies and renames everything into a
loadable folder before each "Load unpacked" — a real cost for a project that
currently needs no build at all.

**If you want per-file versions anyway:** say so. It means adding a build script
and pointing Chrome at the built folder instead of the repo.

---

## Q2 — Should this have started at v_0.1.0?

**Taken:** `v_0.1.0`, on the grounds that reads work but Vinted writes do not,
and that v_1.0.0 should mean parity runs both ways.

**Your rule** (`Explained-user_kurzon.md` §5) is that version numbers are never
chosen without being told the number. This one was picked in the absence of an
answer — **name a different starting number and it changes immediately.**

---

## Q3 — Extension at the repo root, or in a subfolder?

**Taken:** root. `manifest.json` is at the top, so "Load unpacked" points
straight at the cloned repo folder with nothing to explain.

**Cost:** the root has both extension files and docs in it. The alternative is an
`extension/` subfolder — cleaner root, one more thing to remember when loading.

---

## Q4 — The old copy in `ikabot-modules`

**Taken:** left alone. The branch
`claude/vinted-shopify-sync-extension-r8av6l` in `kurzonmorris/ikabot-modules`
still contains the original `vinted-shopify-sync/` folder.

It is unmerged, so it harms nothing — but it is a second copy. **Say the word and
it gets deleted** so this repo is the only home.

---

## Q5 — Store and account details

Not known, so the settings ship empty and get filled in through the settings
page. Worth recording here once known, since they are needed for any real test:

| Thing | Value | Notes |
|---|---|---|
| Shopify store domain | ✅ `1kaa6a-ua.myshopify.com` | Storefront is `sixgenerations.co.uk` |
| Shopify plan | `?` | **Still open.** Sets the rate-limit budget — PROJECT_INFO.md §1.5 |
| Vinted domain | ✅ `www.vinted.co.uk` | Only domain now permitted |
| Vinted username | `?` | Optional; only a safety check that the right account is signed in |
| Is the store actually called "Six Generations"? | assumed yes | It is in the extension name and both UI headers |

**Never put the Shopify access token in this file or any other file in the repo.**
It goes in the settings page only.

---

## Q6 — Which explanation document to upload

**Taken:** `Explained-user_kurzon.md` — it is the one about how you work, and it
matches "ignore the stuff about ikabot and ikariam".

The other file in that repo, `Explained-ikariam_ikabot.md`, is 36 KB of game and
bot technical detail with nothing relevant to this project, so it was not copied.
Say if you wanted that one too.
