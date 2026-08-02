# File Structure — what every file is for

Every filename says what it does. If you add a file, add a row here.

```
sixgenerations-extension/
├── manifest.json                Chrome's entry point: name, version, permissions, which file is what
├── VERSION_v_0.1.0              Version marker — the number is visible in the file listing
├── package.json                 Test runner config + version. NOT a build step; Chrome ignores it
├── CLAUDE.md                    Read first by Claude Code each session — points at these docs
├── README.md                    Start here: what this is, how to install, how to run it
├── .gitignore
│
├── icons/                       Toolbar and store icons (16/32/48/128 px)
│
├── source/                      Everything Chrome actually loads
│   ├── backgroundServiceWorker.js    The coordinator. Routes messages, runs the schedule,
│   │                                 holds run state, and is the ONLY place allowed to make
│   │                                 Shopify network calls (CORS exemption lives here)
│   │
│   ├── core/                         Platform-agnostic logic — no Vinted or Shopify specifics
│   │   ├── extensionVersion.js       Single source of version truth; stamps it into the UI
│   │   ├── messageTypes.js           Message names, storage keys, default settings
│   │   ├── settingsStore.js          Reads/writes settings + the SKU link table
│   │   ├── activityLog.js            Ring-buffer log of everything a run does
│   │   ├── garmentItem.js            The normalised garment: size, brand, colour, condition,
│   │   │                             plus the size/price normalisation and the pairing key
│   │   ├── parityEngine.js           Compares both catalogues, produces the action plan.
│   │   │                             Pure functions — this is the testable heart
│   │   └── syncRunner.js             Executes a plan: fetch, diff, apply (or dry-run), record
│   │
│   ├── connectors/                   One file per platform. All platform quirks live here
│   │   ├── shopifyStoreConnector.js  Admin GraphQL: read catalogue, write price/stock/content
│   │   └── vintedWardrobeConnector.js Finds a signed-in Vinted tab and asks it for the wardrobe
│   │
│   ├── contentScripts/
│   │   └── vintedPageReader.js       Runs INSIDE the Vinted tab. Reads the wardrobe using the
│   │                                 user's own session. Standalone — content scripts can't
│   │                                 use ES modules, so it repeats a few constants
│   │
│   ├── popupPanel/                   The toolbar popup: connection status, run button, log
│   │   ├── popupPanel.html
│   │   ├── popupPanel.js
│   │   └── popupPanel.css
│   │
│   ├── settingsPage/                 The full settings page (opens in a tab)
│   │   ├── settingsPage.html
│   │   ├── settingsPage.js
│   │   └── settingsPage.css
│   │
│   └── sharedStyles.css              Colours, dark mode, buttons — shared by both pages
│
├── tests/                            Run with `npm test`. No dependencies to install
│   ├── chromeApiStub.mjs             Fake chrome.* API so extension code runs under Node
│   ├── parityEngine.test.mjs         The matching and diff rules
│   ├── extensionWiring.test.mjs      Service worker message handling, settings, token redaction
│   └── versionConsistency.test.mjs   Fails if the version drifts between its four homes
│
└── docs/
    ├── PROJECT_INFO.md               ★ API and web-code reference. Researched once, kept here
    ├── FILE_STRUCTURE.md             This file
    ├── SETUP_GUIDE.md                Install and configure, written for the Windows VM
    ├── VERSIONING.md                 The v_x.x.x rules and the bump checklist
    ├── CHANGELOG.md                  What changed in each version
    ├── FUTURE_FEATURES.md            The backlog, with IDs (F-01, F-02, …)
    ├── OPEN_QUESTIONS.md             ★ Decisions made without an answer — check and correct
    └── Explained-user_kurzon.md      How Kurzon works. Reference doc from the ikabot project
```

## The dependency rule

```
        popupPanel / settingsPage
                    ↓ (messages only)
        backgroundServiceWorker
             ↓              ↓
          core/         connectors/
                             ↓
                     contentScripts/  (Vinted tab)
```

- `core/` never imports from `connectors/` — except `syncRunner.js`, which is the
  one place the two meet.
- `connectors/` may import from `core/`, never the other way round.
- UI pages never call a platform directly; they send a message to the worker.

Keeping that direction means the parity rules can be tested without a browser,
which is why `npm test` needs nothing installed.
