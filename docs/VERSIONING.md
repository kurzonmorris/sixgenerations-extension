# Versioning

## Format

```
v_MAJOR.MINOR.PATCH        e.g. v_0.1.0
```

| Part | Increments when |
|---|---|
| **MAJOR** | Significant or breaking change — settings that need re-entering, a changed sync model, the first fully working two-way release |
| **MINOR** | A new feature or meaningful improvement |
| **PATCH** | A bug fix, with no new behaviour |

Current version: **v_0.1.0**

`0.x` means Vinted writes do not work yet. **v_1.0.0 is reserved for the first
release where parity actually runs both ways.**

## Two versions, two markers

Since 2026-09-10 the repo holds two things, each versioned on its own:

| | Marker | Bumped when |
|---|---|---|
| **The Chrome extension** | `VERSION_v_x.x.x` at the repo root | The extension changes |
| **sixgenbot** | `sixgenbot/VERSION_v_x.x.x` | The server changes |

`tests/versionConsistency.test.mjs` guards the extension's, and requires
**exactly one** marker at the root — which is why sixgenbot's lives inside its
own folder. Each sixgenbot module also carries its own `VERSION` inside
`module.py`; Python cannot import a filename containing dots, so versions never
go in Python filenames.

## Where the version appears

| Place | Form | Why |
|---|---|---|
| `VERSION_v_0.1.0` (repo root) | filename | Visible in the file structure at a glance |
| `manifest.json` → `"version"` | `0.1.0` | Chrome requires bare digits here — no `v_` prefix allowed |
| `manifest.json` → `"version_name"` | `v_0.1.0` | The display form Chrome shows on the extensions page |
| Popup + settings header | `v_0.1.0` | Read at runtime from the manifest, never hardcoded |
| `docs/CHANGELOG.md` top entry | `## v_0.1.0` | The record of what changed |
| `package.json` → `"version"` | `0.1.0` | Keeps npm consistent with the rest |

Only the manifest is read at runtime — `source/core/extensionVersion.js` is the
single source of truth, and both UI pages get the number from it. Nothing else
hardcodes a version string.

## Bump checklist

Never bump a version without being told the new number.

1. Rename the marker file: `git mv VERSION_v_0.1.0 VERSION_v_0.2.0`
2. `manifest.json` → `"version": "0.2.0"` **and** `"version_name": "v_0.2.0"`
3. `package.json` → `"version": "0.2.0"`
4. Add a `## v_0.2.0` entry at the top of `docs/CHANGELOG.md`
5. `npm test` — `versionConsistency.test.mjs` fails if any step was missed
6. Commit with the version in the message, e.g. `Bump to v_0.2.0: <what changed>`

## Note on the filename convention

`Explained-user_kurzon.md` §3 says versions go *after the file extension*
(`resourceTransportManager.py_v1.0.0`). That works for Python modules dropped
into a folder, but **Chrome will not load a file called `syncRunner.js_v1.0.0`** —
the extension would need a build step to strip the suffix before every load.

So source files here carry no version in their name, and the version lives in a
dedicated marker file instead. See `docs/OPEN_QUESTIONS.md` Q1 if you would
rather have it the other way.
