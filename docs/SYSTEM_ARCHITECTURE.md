# System Architecture — extension, container, or both?

You asked: *"This system will almost certainly need to be a docker container
script but correct me if I'm wrong."*

**You are mostly right, and the one place you are wrong is the important one.**

---

## 1. The short answer

| Job | Where it has to run | Why |
|---|---|---|
| **Reading and writing Vinted** | **The browser, in your signed-in session** | Vinted has no public API for private sellers and sits behind DataDome bot protection. A server calling Vinted with copied cookies gets 403s and risks the account |
| **Everything else** | **A Docker container on the server** | eBay and Shopify have real server-side APIs. The database, images, orders, notifications, tracking and CSVs all want to run 24/7 with the browser shut |

So: **a small extension as the Vinted sensor, and a Python container as the
brain.** Not one or the other.

The extension gets *smaller* than it is today, not bigger. It ends up doing one
job — "read the wardrobe and hand it over" — and the container does the rest.

## 2. Why Vinted cannot move to the container

- **No API for private sellers.** The endpoints the extension uses are Vinted's
  own internal ones, unversioned and undocumented.
- **DataDome.** Volume from one IP is blocked. Public write-ups report cookie
  sessions expiring quickly and 403s as soon as requests scale.
- **Copying cookies to a server is the exact pattern bot protection looks for**,
  and it puts a 2,000-item selling account at risk to save a bit of convenience.

The extension sidesteps all of it because the traffic *is* genuine: a real
browser, a real session, at human pace.

**Unless Q22 changes the answer.** If the Vinted account is (or becomes) a
**business/Pro account**, Vinted publishes a real API — Items, Orders and
Webhooks — and the whole Vinted half moves to the container. Reported catch: a
manual approval process and a **500 active item limit** to start, against 2,000
items. This is worth finding out before much more is built.
(`EXPLAINED_six-generations_Extension.md` §9.1.)

## 3. The three options, honestly

| Option | What it is | Verdict |
|---|---|---|
| **A. Extension only** | Everything in Chrome, CSVs to the Downloads folder | Fails your requirements. No 24/7, no notifications with the browser shut, and browser storage is the wrong home for 100k items |
| **B. Container only** | Python in Docker, driving Vinted with headless Playwright | Tempting and fragile. Headless browsers are fingerprinted by DataDome; you would need a persistent logged-in profile, a VNC window to solve challenges, and it would break without warning. **Not recommended for Vinted** |
| **C. Extension + container** ★ | Extension reads Vinted and posts to the container; container owns data, eBay, Shopify, orders, notifications | **Recommended.** Each part does the thing it is actually good at |

Option B is not wrong forever — it becomes reasonable the day the Pro API exists
or the day Vinted stops mattering. It is just the wrong first bet.

## 4. What each part does

### 4.1 The Chrome extension — the sensor

Shrinks to roughly:

- One button: **"Read my Vinted wardrobe"**.
- Reads every item, with all fields and photo URLs.
- Posts the result to the container (`POST /api/vinted/snapshot`) on the local
  network, or falls back to saving a file if the container is unreachable.
- Later: performs Vinted **writes** the container asks for — price changes,
  hiding a sold item — because those must also come from the real session.
- Holds no database, no ledger, no eBay keys, no long-term state.

### 4.2 The Docker container — the brain

Python, which matches how you already run things. Roughly:

| Part | Job |
|---|---|
| **API** | Receives wardrobe snapshots from the extension; serves the web interface |
| **Database** | The real store of items, listings, orders, messages, images, money |
| **Image store** | Full-resolution photos on disk, numbered in original order |
| **Platform workers** | eBay Sell API and Shopify Admin GraphQL, server-to-server, no browser |
| **Scheduler** | Periodic jobs: poll orders, poll tracking, chase overdue deliveries, nightly backup |
| **Notifier** | ntfy / Telegram / Discord — sold, delivered, overdue, something broken |
| **Exporter** | Writes `onsale_inventory.csv`, `sold_items.csv`, `orders.csv`, `archive.csv` on demand and on a schedule |
| **Web UI** | The calm interface: one screen, one job (`INTERFACE_PRINCIPLES.md`) |

Suggested stack, chosen for "easy to control and maintain" rather than fashion:
**FastAPI + SQLite + APScheduler + Jinja templates**, one container, one volume.
No Node, no build step, no framework churn. Postgres later if it is ever
outgrown — the code should not care which.

## 5. CSV or a database?

You said *"maybe a proper database is better than a csv file"*. Yes — and you can
have both, because they answer different questions.

| | CSV | Database |
|---|---|---|
| 2,000 items | Fine | Fine |
| 100,000 items | Slow, and Excel starts refusing | Unbothered |
| Multiple sizes / categories per item | Cannot do it cleanly | Natural |
| Two things writing at once | Corrupts | Handled |
| "Cut a row from one file into another" | Lose power mid-write, lose the row | One field changes; nothing can be lost |
| Reading it yourself in Excel | Perfect | Needs an export |

**Recommendation: SQLite is the store, CSVs are exports.** SQLite is a single
file — copy it, back it up, move it to HexOS by dragging it. It handles millions
of rows. And the four CSVs you described get written on demand, so you still
open them in Excel exactly as you pictured.

**One correction worth stating plainly:** the "cut a row out of
`onsale_inventory.csv` and paste it into `sold_items.csv`" model is the one part
of your plan I would not build literally. Two files being edited by a background
job is where data goes missing. In the database it is one field —
`status: on_sale → sold` — with the full history kept, and the exporter then
produces exactly the files you asked for, every time, from the truth. Same
result, nothing can be lost. Full detail in `docs/DATA_MODEL.md`.

## 6. The flow, end to end

```
1. NEW OR CHANGED ON VINTED
   extension reads wardrobe ──► container compares against database
                                 ├─ new item        → create, download photos, mark "needs extra info"
                                 ├─ changed item    → update, record what changed
                                 └─ missing item    → check whether it sold

2. READY TO LIST ELSEWHERE
   container checks required fields per platform
     ├─ complete   → publish to eBay / Shopify (manual or automatic)
     └─ incomplete → into the "needs your input" queue, one screen, one item at a time

3. SOLD
   sale detected (Vinted read / eBay API / Shopify API)
     → status = sold, all data retained
     → order record created, buyer messages copied in
     → other platforms delisted  ← the thing that stops double-selling
     → notification sent

4. POSTED
   press "Posted", attach the photo of the parcel in its bag
     → shipment record, tracking number, tracking polled until delivered
     → notification on delivery, and a chase if it goes quiet too long

5. ARCHIVED
   completed order → archive, kept 5 years, exported to archive.csv
```

## 7. Deployment

- One `docker-compose.yml`, one image, one volume:
  `/data/db`, `/data/images`, `/data/exports`, `/data/backups`.
- Runs the same on Unraid today and **HexOS tomorrow** — nothing in it is
  Unraid-specific, which is the point of putting it in a container.
- Nightly backup: copy the database file plus a CSV export set. Both are
  restorable without the application.
- The extension needs the container's address; on a home network that is a
  hostname and a port.

## 8. Security and privacy

- **Secrets live in the container's environment / a mounted secrets file** — the
  Shopify token, eBay keys, notification tokens. Never in the repo, never in a
  CSV, never in a log line.
- The web UI is on the home network. If it is ever reachable from outside, it
  needs a password in front of it — worth deciding early (Q31).
- **Buyer names, addresses and messages are personal data.** Keeping financial
  records for 5 years is normal and sensible; keeping full addresses and message
  histories that long is a separate choice. Worth deciding what gets trimmed and
  when (Q30).

## 9. Scale

At 100,000 items the parts that change:

- Full Vinted reads stop being sensible — read what changed, not everything.
- Images become the biggest thing on disk. 100k items × 5 photos × ~300 KB ≈
  **150 GB**. Plan the volume for it, and decide whether originals are kept
  forever (Q29).
- The web UI must page and filter rather than draw everything.
- SQLite still copes. Postgres becomes worth it only if several things write at
  once.

## 10. What this means for the existing extension

Nothing is wasted. What survives, and where it goes:

| Today | Tomorrow |
|---|---|
| `vintedPageReader.js` | Stays. Gains all the extra fields, and posts to the container |
| `storageCode.js` | Ported to Python in the container, kept in the extension |
| `garmentItem.js` | Becomes the container's item model, with multi-value attributes |
| `parityEngine.js` | Moves to the container and grows a third platform |
| `shopifyStoreConnector.js` | Reimplemented in Python — same queries, same cost limits |
| Settings / popup UI | Shrinks to a connection setting and one button |
| Test suite | Stays for the extension; the container gets its own |

## 11. Open decisions this raises

Added to `docs/OPEN_QUESTIONS.md` as Q26–Q32. The ones that block the most:

- **Q22** — is the Vinted account a business account? Changes the whole
  architecture if yes.
- **Q26** — SQLite or Postgres, and CSVs as exports rather than storage.
- **Q27** — does the extension talk to the container directly, or is the
  hand-over a file?
- **Q28** — is publishing to eBay and Shopify manual, automatic, or automatic
  with a review step?
