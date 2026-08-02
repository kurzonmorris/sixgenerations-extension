# Open Questions

Decisions taken **without an answer** because the questions could not be
answered in the session where they came up. Each one is cheap to reverse.

**Answer these and the choice gets locked in — or corrected — in the next
commit.** Delete a row once it is settled and record the outcome in CHANGELOG.md.

---

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
