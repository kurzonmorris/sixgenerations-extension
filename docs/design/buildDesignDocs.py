"""Builds the four design documents. Run it after any change to the feature file.

    python docs/design/buildDesignDocs.py

Writes four HTML files into `docs/design/`. They are generated so that part 3
can never drift away from `FEATURE_six-generations_creep.md`.
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
from collections import Counter, defaultdict

import designDocPages as P
import designDocShared as S

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent.parent

STATE_WORD = {
    "built": ("built", "On screen and working today"),
    "part": ("part", "Partly there — some of it is missing"),
    "planned": ("planned", "Named in the plans, nothing built"),
    "proposed": ("question", "Claude's idea — not asked for. Say yes, no or change it"),
}

# Which built-feature section belongs to which screen. Everything in the feature
# file lands somewhere, so nothing is left unallocated.
SECTION_TO_PAGE = {
    "A.1 Reading": "The extension (Vinted and Shopify)",
    "A.2 Matching": "The extension (Vinted and Shopify)",
    "A.3 Comparing and planning": "The extension (Vinted and Shopify)",
    "A.4 Writing (Shopify only)": "sixgenerations.co.uk — the shop",
    "A.5 Safety": "Rules that hold everywhere",
    "A.6 sixgenbot — the server": "The server itself",
    "A.6b sixgenbot — the database": "The server itself",
    "A.6c sixgenbot — stage 3 foundations": "Files — in and out",
    "A.6d sixgenbot — stage 3, the import": "Files — in and out",
    "A.6e sixgenbot — the Files page": "Files — in and out",
    "A.6f sixgenbot — To review, the batch edit screen (U-16)": "To review",
    "A.6g sixgenbot — the Photos page": "Photos",
    "A.6h sixgenbot — The Table": "The Table — every garment",
    "A.6i sixgenbot — small copies of the photographs": "The Table — every garment",
    "A.6j sixgenbot — choosing items, and editing down a column": "Edit the chosen items",
    "A.6k sixgenbot — photographs and old values while editing": "Edit the chosen items",
    "A.6l sixgenbot — Ready to list": "Ready to list",
    "A.6m sixgenbot — reading Vinted into the database": "Vinted",
    "A.6n the extension — confirming it is the right shop": "Rules that hold everywhere",
    "A.7 Running it (the extension)": "The extension (Vinted and Shopify)",
}

STATUS_FROM_MARK = {
    "✅": "built", "🟡": "part", "◐": "part", "⛔": "stub",
    "📋": "planned", "❓": "question",
}


def features() -> list[dict]:
    raw = (ROOT / "FEATURE_six-generations_creep.md").read_text()
    rows, part, section = [], "", ""
    for line in raw.splitlines():
        if line.startswith("# Part "):
            part = line.lstrip("# ").strip()
        elif line.startswith("## "):
            section = re.sub(r"\*\(.*?\)\*", "", line.lstrip("# ")).strip()
        m = re.match(r"^\|\s*\*{0,2}([A-Z]-[\d–\-]+)\*{0,2}\s*\|\s*([^|]*?)\s*\|\s*(.+?)\s*\|\s*$", line)
        if not m:
            continue
        ident, mark, rest = m.groups()
        bits = [b.strip() for b in rest.split("|")]
        declined = part.startswith("Part E")
        rows.append({
            "id": ident,
            "status": "declined" if declined else STATUS_FROM_MARK.get(mark, "planned"),
            "part": part, "section": section,
            "what": mark if declined else bits[0],
            "where": bits[0] if declined else (bits[1] if len(bits) > 1 else ""),
        })
    return rows


def clean(text: str) -> str:
    """Markdown bold and code, as HTML. The feature text is written in Markdown."""
    text = S.esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def stamp() -> str:
    commit = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%h %cs"],
                            capture_output=True, text=True).stdout.strip()
    return f"Generated from the repository at {commit}. Regenerate with python docs/design/buildDesignDocs.py"


# --------------------------------------------------------------- part 1
def buildPages(rows):
    body = [
        '<p class="lead">Every screen, drawn. Boxes are regions of the page; a line '
        'runs from each note to the part it describes. Nothing here is a picture — '
        'it is all boxes, lines and colour, so it prints and reads at any size.</p>',
        S.regionKey(),
        '<div class="note"><b>How to read the state of a page.</b> A dashed red box '
        'means that part is <b>not built</b>. An orange block headed '
        '<b>YOU NEED TO FILL THIS IN</b> is a decision only you can make — and every '
        'one of them offers <b>Claude decides</b> as a real answer, so none of them '
        'has to hold the work up.</div>',
    ]
    bygroup = defaultdict(list)
    for p in P.PAGES:
        bygroup[p["group"]].append(p)

    for group in ["TODAY", "ITEMS", "MONEY", "SITES", "SYSTEM"]:
        body.append(f"<h2>{group}</h2>")
        for p in bygroup.get(group, []):
            kind, words = STATE_WORD[p["state"]]
            body.append(f'<h3>{S.esc(p["name"])} &nbsp; {S.tag(kind)}</h3>')
            body.append(f'<p class="lead"><code>{S.esc(p["url"])}</code> — {p["summary"]}</p>')
            height = max(520, max((r["y"] + r["h"] for r in p["regions"]), default=460) + 60)
            body.append("<figure>" + S.diagram(p["name"], p["regions"], p["callouts"], height)
                        + f'<figcaption>{S.esc(p["name"])} — {S.esc(words)}</figcaption></figure>')
            for question, options in p["asks"]:
                body.append(S.ask(question, options))
    return "\n".join(body)


# --------------------------------------------------------------- part 2
def buildDetail(rows):
    body = ['<p class="lead">What happens on each screen, with every feature from the '
            'feature file allocated to one. Nothing is left floating.</p>']

    allocated = defaultdict(list)
    for row in rows:
        if row["part"].startswith("Part A"):
            allocated[SECTION_TO_PAGE.get(row["section"], "The server itself")].append(row)

    pageByName = {p["name"].split(" — ")[0]: p for p in P.PAGES}

    for where, items in allocated.items():
        body.append(f"<h2>{S.esc(where)}</h2>")
        short = where.split(" — ")[0]
        match = pageByName.get(short)
        if match:
            body.append(f'<p class="lead"><code>{S.esc(match["url"])}</code> — {match["summary"]}</p>')
        body.append("<table><tr><th>ID</th><th>What it does</th><th>Where in the code</th></tr>")
        for row in sorted(items, key=lambda r: (r["id"][0], int(re.sub(r"\D", "", r["id"]) or 0))):
            body.append(f'<tr><td>{S.esc(row["id"])}</td><td>{clean(row["what"])}</td>'
                        f'<td>{clean(row["where"])}</td></tr>')
        body.append("</table>")

    body.append("<h2>Promised but not built</h2>")
    body.append('<p class="lead">Named in the plans, with no screen behind them yet. '
                'Part 4 says when each one is scheduled.</p>')
    body.append("<table><tr><th>ID</th><th>What it would do</th><th>Group</th></tr>")
    for row in rows:
        if row["part"].startswith("Part D") and row["status"] in ("planned", "part"):
            body.append(f'<tr><td>{S.esc(row["id"])}</td><td>{clean(row["what"])}</td>'
                        f'<td>{S.esc(row["section"])}</td></tr>')
    body.append("</table>")

    body.append("<h2>Deliberately refusing, for now</h2>")
    body.append('<p class="lead">These exist in the code and say so plainly rather than '
                'failing strangely.</p>')
    body.append("<table><tr><th>ID</th><th>What it refuses</th><th>Where</th></tr>")
    for row in rows:
        if row["status"] == "stub":
            body.append(f'<tr><td>{S.esc(row["id"])}</td><td>{clean(row["what"])}</td>'
                        f'<td>{clean(row["where"])}</td></tr>')
    body.append("</table>")
    return "\n".join(body)


# --------------------------------------------------------------- part 3
def buildStatus(rows):
    counts = Counter(r["status"] for r in rows)
    body = [
        '<p class="lead">Every feature ever discussed, and exactly where it stands. '
        'This table is generated from <code>FEATURE_six-generations_creep.md</code>, '
        'so it cannot drift away from the code.</p>',
        S.statusKey(),
        "<h2>The count</h2>",
        "<table><tr><th>State</th><th>How many</th><th>What it means</th></tr>",
    ]
    for key, (fg, bg, word) in S.STATUS.items():
        meaning = {
            "built": "On screen, working, and covered by a test.",
            "part": "Some of it works. The missing half is named in part 4.",
            "stub": "The code is there and refuses on purpose, with a reason.",
            "planned": "Agreed and waiting. Part 4 says when.",
            "question": "Waiting on an answer from you. Part 1 holds the questions.",
            "declined": "You said no. Kept so the same idea does not come round again.",
        }[key]
        body.append(f'<tr><td>{S.tag(key)}</td><td><b>{counts.get(key, 0)}</b></td>'
                    f"<td>{meaning}</td></tr>")
    body.append(f'<tr><td><b>Everything</b></td><td><b>{len(rows)}</b></td>'
                f"<td>Features discussed since the project began.</td></tr></table>")

    order = ["built", "part", "stub", "planned", "question", "declined"]
    for key in order:
        group = [r for r in rows if r["status"] == key]
        if not group:
            continue
        body.append(f"<h2>{S.STATUS[key][2]} — {len(group)}</h2>")
        body.append("<table><tr><th>ID</th><th>State</th><th>What it is</th>"
                    "<th>Where</th><th>Part of</th></tr>")
        for row in group:
            body.append(
                f'<tr><td>{S.esc(row["id"])}</td><td>{S.tag(row["status"])}</td>'
                f'<td>{clean(row["what"])}</td><td>{clean(row["where"])}</td>'
                f'<td>{S.esc(row["section"])}</td></tr>')
        body.append("</table>")
    return "\n".join(body)


# --------------------------------------------------------------- part 4
STAGES = [
    dict(
        n="A", name="Answer the questions that block screens", weeks="an evening",
        goal="Nothing is built in this stage. It removes the guesswork from every stage after it.",
        why="Four screens cannot be designed without decisions only you can make. Each one in "
            "part 1 offers <b>Claude decides</b>, so this can be as short as saying “you choose”.",
        does=["Q51 — may the Table have in-place editing (JavaScript)?",
              "What the dashboard shows, and where the technical Status block goes",
              "What the Boxes page is for",
              "Whether a page for one garment should exist (and so where history lives)",
              "Whether the five years of old books get imported"],
        touches=["docs/OPEN_QUESTIONS.md", "docs/INTERFACE_LAYOUT.md"],
        test="Every orange block in part 1 has an answer written next to it.",
        needs="<b>You.</b> Reading part 1 and saying yes, no, or “you choose”.",
    ),
    dict(
        n="B", name="The dashboard — make the first screen about the work", weeks="2–3 days",
        goal="Replace the technical Status page as the first thing you see.",
        why="The first screen is the one seen most. Today it is about the server; it should be "
            "about today's work. It also needs nothing new underneath — every count already exists.",
        does=["Needs fixing at the top (U-15): failed copies, double sales, dead connections",
              "Today: to review · to post · ready to list, each a link with the filter set",
              "The counts: on sale, never listed, sold this month",
              "Items listed per day (X-09) — the number the project is judged on",
              "Move the technical block to SYSTEM"],
        touches=["sixgenbot/modules/dashboard/ (new)", "sixgenbot/core/itemQuery.py (counts)",
                 "sixgenbot/modules/systemStatus/ (moves off /)"],
        interacts="Reads only. Every number is a query that already exists in itemQuery; the links "
                  "carry the same filter names the Table already understands.",
        test="Counts match The Table with the same filter set. Nothing moves on its own. "
             "A dashboard with nothing wrong still shows the block, with one line.",
        needs="Stage A, question 1 and 2.",
    ),
    dict(
        n="C", name="One garment, and its history (U-18)", weeks="2–3 days",
        goal="A page for a single garment, with every change it has ever had.",
        why="Every list wants somewhere to click through to, and there is nowhere. The history "
            "rows are <b>already being written</b> by every edit, every Vinted read and every "
            "photograph move — this is only the screen that reads them.",
        does=["Everything the garment says now, every field",
              "Its photographs in order, with the reorder link",
              "Where it is listed: Vinted, eBay, the shop",
              "Its history: every change, what it was before, who did it and when",
              "Links out to edit it, to Ready to list, to the box it is in"],
        touches=["sixgenbot/modules/itemPage/ (new)", "the `event` table (already filled)",
                 "every existing table gains a link to it"],
        interacts="Pure read, except the links out. The event table already records actor "
                  "(user / vinted / system), field, value before and value after.",
        test="An edit made on the To review screen appears in the history within the same minute, "
             "with its old value. A Vinted read appears as actor “vinted”.",
        needs="Stage A, question 4.",
    ),
    dict(
        n="D", name="Writing to Vinted — price and hiding a sold listing", weeks="1–2 weeks",
        goal="The first writes. Change a price; hide a listing that has sold elsewhere.",
        why="These two are the smallest useful writes and the least dangerous. They do not create "
            "anything and they do not touch descriptions, so the SKU can never be lost.",
        does=["Drive Vinted's own edit form in the signed-in tab",
              "Price only, then hide or delete",
              "Dry run first, always: show the plan, then do it",
              "Record every write in the garment's history",
              "Stop on anything unexpected rather than guessing"],
        touches=["source/connectors/vintedWardrobeConnector.js (setPrice, archive)",
                 "source/contentScripts/vintedPageReader.js (the edit form)",
                 "sixgenbot/core/vintedRead.py (what to ask for)"],
        interacts="Needs the linking from stage 0 to be done — a write can only go to a listing "
                  "whose Vinted number is known. Reads stay the source of truth.",
        test="A dry run on ten garments lists exactly what it would change. A real run on ONE "
             "garment changes that one and nothing else. The description is untouched.",
        needs="<b>Investigation first.</b> Vinted's edit form has to be read from the live site — "
              "docs/CLAUDE_BROWSER_TASKS.md. Nothing here can be written from documentation.",
    ),
    dict(
        n="E", name="Writing descriptions and titles, keeping the SKU", weeks="1 week",
        goal="Change listing text on Vinted without ever losing the storage code.",
        why="This is how the 972 withdrawn garments get their sizes corrected in place, rather "
            "than being relisted from scratch.",
        does=["Use withSku() so the code is always on the end",
              "Leave a padded code (B5-5 004) exactly as it is",
              "Show the before and after text before writing anything",
              "Refuse to write if the code would change"],
        touches=["sixgenbot/core/sku.py (withSku, already correct)",
                 "source/connectors/vintedWardrobeConnector.js (updateContent)"],
        interacts="Reuses the description already shown on Ready to list. A write that would "
                  "change the parsed code is a bug, not a feature — it stops.",
        test="A hundred descriptions round-trip with the code unchanged, padding and all.",
        needs="Stage D.",
    ),
    dict(
        n="F", name="Creating a Vinted listing outright", weeks="2–3 weeks",
        goal="One button: put this garment on Vinted.",
        why="<b>This is the point of the project.</b> 972 garments are waiting, 3 to 6 go up a day "
            "by hand. This is the step that changes that number.",
        does=["Upload the photographs in order",
              "Fill the form from the garment, including the SKU on the end",
              "Category and size pickers — the hardest part, and why F comes after E",
              "Record the new listing number straight away, so it is linked for ever",
              "One garment at a time, with the plan shown first"],
        touches=["source/contentScripts/vintedPageReader.js (the new-listing form)",
                 "sixgenbot/core/listingSheet.py (already produces every answer)",
                 "sixgenbot/modules/listingHelper/ (becomes a button, not a copying screen)"],
        interacts="listingSheet already assembles everything the form asks for — that work is done. "
                  "This stage is the driving, not the data.",
        test="One garment, end to end, on the real account. Then ten. The photographs come out in "
             "the right order and the SKU is on the end.",
        needs="Stages D and E. <b>Investigation of the new-listing form on the live site.</b>",
    ),
    dict(
        n="G", name="The ledger — sales, purchases, totals", weeks="2 weeks",
        goal="The money side, matching the existing books exactly.",
        why="Everything about the garment is built; nothing about what it cost or made. "
            "docs/EXISTING_LEDGER.md has five years of real numbers to check against.",
        does=["Record a sale against a garment, with fees and postage",
              "Record a purchase as a lot, sharing cost across its garments",
              "Petrol in the profit sum, exactly as the sheet does it",
              "A monthly export shaped like the old sheet",
              "Import the five years of old books, read-only"],
        touches=["sixgenbot/modules/ledger/ (new)", "the salesOrder, lot, purchase, postingTrip "
                 "tables (all already in the database)", "sixgenbot/core/csvExport.py"],
        interacts="The tables exist and are empty. A sale read from Vinted (stage H) fills them "
                  "automatically; before that they are filled by hand.",
        test="A month imported from the old sheet totals the same to the penny. If it does not, "
             "the import is wrong.",
        needs="Stage A, question 5. The petrol price per litre.",
    ),
    dict(
        n="H", name="Sales and orders read from Vinted", weeks="1 week",
        goal="A sale on Vinted appears here without being typed.",
        why="Removes the main piece of daily typing, and makes To post possible.",
        does=["Read sold listings and buyer details in the signed-in session",
              "Match to the garment by its listing number",
              "Fill the sale record: price, postage, fees where Vinted says",
              "Never estimate a fee — NULL means “not told”, not zero"],
        touches=["source/contentScripts/vintedPageReader.js (the orders endpoints)",
                 "sixgenbot/core/vintedRead.py", "sixgenbot/modules/ledger/"],
        interacts="Depends on stage G for somewhere to put the numbers, and on linking for the "
                  "match. Buyer details are personal data — docs/DATA_MODEL.md §6.",
        test="A real sale appears with the right garment, the right money, and nothing guessed.",
        needs="Stage G. Investigation of the Vinted orders pages.",
    ),
    dict(
        n="I", name="To post, and the Boxes page", weeks="1 week",
        goal="The two screens that make the daily round easier.",
        why="Both are named in the layout and both are small once the data behind them exists.",
        does=["To post: what is sold and waiting, where it is, one Posted button",
              "A parcel photograph kept against the sale",
              "Boxes: pick a column, pick a box, see what is in it and which numbers are free"],
        touches=["sixgenbot/modules/posting/ (new)", "sixgenbot/modules/boxes/ (new)",
                 "sixgenbot/core/sku.py (SQL_ORDER, already correct)"],
        interacts="To post reads the sale records from stage H. Boxes reads only the SKU, so it "
                  "could in fact be built at any time.",
        test="A sale marked posted leaves the list and keeps its photograph. Boxes agrees with "
             "the real shelf for one column, checked by hand.",
        needs="Stage H for To post. Stage A, question 3 for Boxes.",
    ),
    dict(
        n="J", name="eBay, read only", weeks="1–2 weeks",
        goal="See what is on eBay, and answer Q16 with real data.",
        why="Reading cannot damage anything, and it settles whether eBay listings carry the "
            "storage code — which decides how everything after it works.",
        does=["Connect by API from the server, not the browser",
              "Read every listing",
              "The three-way list: here, Vinted, eBay",
              "Answer Q16 properly"],
        touches=["sixgenbot/modules/ebaySync/ (new)", "docs/PROJECT_INFO.md §3 (unverified — "
                 "<b>check every line against the live API</b>)"],
        interacts="Same shape as the Vinted read: arrive, plan, apply. The same linking problem, "
                  "and the same rule — a read never writes over a correction.",
        test="The listing count matches what eBay's own page says.",
        needs="eBay developer keys. <b>PROJECT_INFO §3 is unverified</b> and must be checked first.",
    ),
    dict(
        n="K", name="eBay writes, and sold-anywhere-removes-everywhere", weeks="2 weeks",
        goal="The payoff: one garment sells, and it comes down everywhere else.",
        why="This is the thing a cross-listing tool is for, and it is the last big piece.",
        does=["Write price and stock to eBay",
              "End an eBay listing when it sells on Vinted, and the reverse",
              "The shop kept in step too",
              "Dry run first, every time"],
        touches=["sixgenbot/modules/ebaySync/", "sixgenbot/modules/vintedSync/",
                 "the existing Shopify writes in the extension"],
        interacts="Needs every read working and every listing linked. A double sale is the thing "
                  "this prevents — and the thing that goes on the dashboard when it happens.",
        test="A test garment on all three, sold on one, gone from the other two within one run.",
        needs="Stages D, F and J.",
    ),
]


def buildSchedule(rows):
    body = ['<p class="lead">The order to build in, and what each stage needs. Each stage is '
            'sized so it can be built, tested and merged on its own — a stage that is too big '
            'is where mistakes come from.</p>',
            '<div class="note"><b>What “needs” means.</b> Some stages wait on an answer from you; '
            'some wait on finding something out from a live website, which cannot be guessed from '
            'documentation. Those are marked, because they are the ones that stall.</div>',
            "<h2>The order at a glance</h2>",
            "<table><tr><th>Stage</th><th>What it is</th><th>Roughly</th><th>Waits on</th></tr>"]
    for st in STAGES:
        body.append(f'<tr><td><b>{st["n"]}</b></td><td>{S.esc(st["name"])}</td>'
                    f'<td>{S.esc(st["weeks"])}</td><td>{st["needs"]}</td></tr>')
    body.append("</table>")

    for st in STAGES:
        body.append(f'<h2>Stage {st["n"]} — {S.esc(st["name"])}</h2>')
        body.append(f'<p><b>What it is for.</b> {st["goal"]}</p>')
        body.append(f'<p><b>Why now.</b> {st["why"]}</p>')
        body.append("<h3>What gets built</h3><ul>"
                    + "".join(f"<li>{clean(d)}</li>" for d in st["does"]) + "</ul>")
        body.append("<h3>Files it touches</h3><ul>"
                    + "".join(f"<li><code>{S.esc(t)}</code></li>"
                              if "/" in t and "(" not in t else f"<li>{clean(t)}</li>"
                              for t in st["touches"]) + "</ul>")
        if st.get("interacts"):
            body.append(f'<h3>How it fits the rest</h3><p>{st["interacts"]}</p>')
        body.append(f'<h3>How we know it works</h3><p>{st["test"]}</p>')
        body.append(f'<h3>What it waits on</h3><p>{st["needs"]}</p>')

    body.append("<h2>What is already done</h2>")
    built = len([r for r in rows if r["status"] == "built"])
    body.append(f'<p>{built} features are built and working — part 3 lists every one. In short: '
                'the database, the import of 2,125 garments, all 9,098 photographs brought off '
                'Crosslist, the Table, To review with batch editing, Ready to list, and reading '
                'the Vinted wardrobe back in.</p>')
    body.append('<div class="note"><b>The one number that matters.</b> 3 to 6 garments go up a '
                'day, against 972 waiting and about 4.6 bought a day. Stage F is the only stage '
                'that changes that number — everything before it exists to make stage F safe.</div>')
    return "\n".join(body)


def main():
    rows = features()
    when = stamp()
    HERE.mkdir(parents=True, exist_ok=True)
    out = {
        "01_pages.html": ("Part 1 — every page, drawn", buildPages(rows)),
        "02_pagesInDetail.html": ("Part 2 — what happens on each page", buildDetail(rows)),
        "03_featureStatus.html": ("Part 3 — every feature and its status", buildStatus(rows)),
        "04_buildSchedule.html": ("Part 4 — the build schedule", buildSchedule(rows)),
    }
    for name, (title, content) in out.items():
        (HERE / name).write_text(S.page(title, "", content, when))
        print(f"  {name}  {len((HERE / name).read_text()):,} bytes")
    (HERE / "features.json").write_text(json.dumps(rows, indent=1))
    print(f"{len(rows)} features, {Counter(r['status'] for r in rows)}")


if __name__ == "__main__":
    main()
