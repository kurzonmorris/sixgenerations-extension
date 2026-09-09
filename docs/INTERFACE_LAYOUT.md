# Interface Layout — the dashboard, as asked for

What the screen is. `INTERFACE_PRINCIPLES.md` says *how* everything on it must
behave; this says *what is there*. Where they disagree, this file records the
disagreement rather than hiding it.

**Asked for on 2026-09-09:**

> A dashboard with a menu system on the left, and the main section holds and
> displays what is selected on the menu. The default first page shows: items
> currently on sale, items to be reviewed, items sold, items posted, items in
> archive, and money made this year, month, week and day. Left menu: To table,
> To post, To review, view list of items, Vinted, eBay, sixgenerations.co.uk,
> Settings, Console.

---

## 1. The one conflict, stated once

`INTERFACE_PRINCIPLES.md` U-01 says **"one screen, one job. No dashboard of
everything at once."** That rule was written from guidance on designing for
autism, ADHD and sensory sensitivity — for the person who uses this daily.

A dashboard with ten numbers on it is the thing that rule exists to prevent.

**It is your system and your call, and this is built as asked.** But there is a
version that gives you the overview and still respects why the rule was there:

| Keeps | Changes |
|---|---|
| Everything on the home page, all ten figures | They are **a plain list of rows**, not tiles, badges, gauges or charts |
| The left menu, always in the same place | Nothing on it moves, highlights on hover, or shows a count that changes while being read |
| Money figures for year, month, week, day | One line each, in words: "This week: £412" |
| Everything reachable in one click | The page **does not refresh itself** while being looked at |

That version is what is specified below. Worth showing her before it is built —
if the counts are too much, the fix is small: one line ("6 things need you
today") with the rest behind it.

## 2. Home page

Ten rows, plain text, each one a link to the screen that shows those items:

```
   Six Generations

   ON SALE            2,041 items
   TO REVIEW             18 items        ← needs you
   TO POST                3 items        ← needs you
   SOLD                  12 items        (this month)
   POSTED                 9 items        (this month)
   ARCHIVE           14,220 items

   MONEY IN
   Today                £34
   This week           £412
   This month        £1,880
   This year        £22,140

   Last checked: 14 minutes ago.   [ Check now ]
```

Rules for it:

- Rows that need action say so **in words**, not by turning red.
- Nothing animates, counts up, or refreshes while it is on screen. "Last checked"
  is a fact, not a live clock.
- If a number cannot be worked out, the row says so plainly rather than showing
  a zero.
- No charts on this page. (Charts are D-163, still unanswered — if the answer is
  yes they belong on their own screen, never here.)

## 3. The left menu

Grouped, because nine flat items is a list to be read and four groups is not.
Your list, plus the ones the workflow needs.

```
  TODAY
    To table            items waiting to be listed          ← meaning to confirm
    To review           missing information before listing
    To post             sold, waiting to go in a bag

  ITEMS
    All items           search and filter everything
    Boxes               what is in each storage box
    Sold
    Archive

  MONEY
    Sales
    Purchases
    Totals

  SITES
    Vinted
    eBay
    sixgenerations.co.uk

  SYSTEM
    Settings
    Console
    Backups             when the last one ran, and whether it worked
```

- The menu never reorders itself and never hides items based on what is in them.
- The item you are on is marked with a word or a solid marker, never by colour
  alone.
- **"To table"** — this needs a definition before it can be built. Items waiting
  to be photographed? Waiting to be entered? It is the first thing on the menu,
  so it is worth getting right.

## 4. The three site links — and why they cannot be embedded

You asked for Vinted, eBay and Shopify to load **inside** the web interface.

**Expect that not to work.** Sites set headers (`X-Frame-Options`,
`Content-Security-Policy: frame-ancestors`) specifically to stop themselves being
loaded inside someone else's page, and eBay and Vinted are both firmly in that
camp — a marketplace being framed by another site is a phishing pattern, so they
block it. Your own Shopify storefront might allow it; the Shopify admin will not.

This was not verifiable from where this was written (the sites refuse a bare
request from this machine), so it is worth 30 seconds with the browser to confirm
— added as a task in `docs/CLAUDE_BROWSER_TASKS.md`.

Three ways to have it anyway:

| Option | What happens | Cost |
|---|---|---|
| **A. Open in a new tab** ★ | The menu item opens Vinted in a browser tab, already on the right page — the item you were looking at, not the home page | Not embedded. But it works today, everywhere, forever |
| **B. Deep links per item** ★ | Every item screen has "Open on Vinted / eBay / the shop" for that garment | The genuinely useful half of what embedding would give you |
| **C. A desktop app later** | Wrap the interface in something with real webviews, which are not bound by those headers | A second thing to build, install and update, on every machine |

A and B together give you almost everything embedding would, and cost nothing.
C stays on the list if it still matters once the rest works.

## 5. The Console view

A screen that shows what the container is doing without opening a terminal.

- Plain lines, newest at the bottom, **frozen by default** — it does not scroll or
  update while being read.
- A **[ Show new lines ]** button that says how many are waiting: "42 new lines".
- Filter to errors only, in one press.
- Copy-all, for pasting somewhere.
- Never the first thing anyone sees, and never a live tail on the home page — a
  scrolling log is exactly what U-03 exists to prevent.

## 6. Two shapes, not one

From your answer about where the work happens:

| Where | What it must be |
|---|---|
| **Next to the boxes** — entering new items | **Phone first.** Big targets, one field at a time, works one-handed, tolerates a bad signal, never loses what was typed if the page reloads |
| **At the desk** — labels, packing, money | **Desktop first.** Keyboard-driven, several items on screen, printing |

The same screens should not try to be both. The item-entry queue is a phone
screen that happens to work on a laptop; the packing list is a desk screen that
happens to survive on a phone.

## 7. Screens behind each menu item

| Menu item | Screen |
|---|---|
| To table | Items in the earliest stage, ready to be worked through one at a time |
| To review | The missing-information queue: one item, only the fields that are missing (D-096, D-097) |
| To post | Sold and unposted, with the Posted button and the parcel photo (D-107) |
| All items | Search, filter, and bulk change (D-186 to D-189) |
| Boxes | What is in each storage code, and what is free (D-245, D-248) |
| Sold / Archive | The record, searchable |
| Sales / Purchases / Totals | The money screens (D-141 onwards) |
| Sites | Links out, per §4 |
| Settings | Connections, secrets, schedules, backups |
| Console | Per §5 |
| Backups | Last run, size, whether the offsite copy went to pCloud |
