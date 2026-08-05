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
