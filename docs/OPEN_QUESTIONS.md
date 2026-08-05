# Open Questions

Decisions taken **without an answer** because the questions could not be
answered in the session where they came up. Each one is cheap to reverse.

**Answer these and the choice gets locked in — or corrected — in the next
commit.** Delete a row once it is settled and record the outcome in CHANGELOG.md.

> **Note on how these got here:** the interactive question prompt did not reach
> Kurzon in the sessions where this work was done (asked twice, no answer both
> times). That is why the questions live in this file. Answers can be given in
> plain chat, or by editing this file directly.

---

# Answer these next

The set below blocks the next piece of work. **Q7 is the one that matters most.**

## Q7 — What gets built next?

Nothing is being written until this is answered, because the options conflict.

| Option | What it is | Argument for |
|---|---|---|
| **F-01 — verify the Vinted read path** ← *recommended* | Prove the wardrobe read works against the real account, harden the field mapping, make failures loud | It is the one part written from public references rather than a live account. Everything downstream trusts it. Writing to Vinted before this is proven risks writing to the wrong listing |
| **F-07 — bulk SKU assignment** | A helper that proposes a SKU per garment and writes it to both sides | The right first move *if the wardrobe was never SKU'd* — without SKUs nothing pairs, and a dry run just reports everything as one-sided |
| **F-02 / F-03 — Vinted writes** | Price changes, hiding sold listings | The road to v_1.0.0, but premature until F-01 is proven |
| **Nothing yet** | Kurzon installs v_0.1.0, runs a dry run, reports what it got wrong | The fastest way to find out what is actually broken |

**Feeding into this:** are the Vinted listings already SKU'd, or is the wardrobe
untouched? That single fact decides between F-01 and F-07.

## Q8 — Shopify store domain

The permanent `xxx.myshopify.com` one. Guessed candidates were
`sixgenerations.myshopify.com` / `six-generations.myshopify.com`, neither
confirmed. Also useful: **which Shopify plan**, since it sets the rate-limit
budget (PROJECT_INFO.md §1.5).

Not blocking — it is typed into the settings page at setup — but without it no
one can debug a wrong-domain error from the outside.

## Q9 — Which Vinted domain

Assumed `www.vinted.co.uk` (GBP, UK sizes). Confirming it means the other seven
Vinted domains can be dropped from `host_permissions`, which shortens the
permission warning Chrome shows on install.

A non-UK domain would need the size normalisation re-checked.

## Q10 — Scale

Roughly how many garments are in the wardrobe and in the store? It changes
whether rate-limit backoff (F-10) is a real concern or a theoretical one, and
whether the first dry run will be readable or a wall of text.

---

# Already decided (without an answer)

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
| Shopify store domain | `?` | The permanent `xxx.myshopify.com` one |
| Shopify plan | `?` | Sets the API rate limit budget — see PROJECT_INFO.md §1.5 |
| Vinted domain | assumed `www.vinted.co.uk` | Changeable in settings |
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
