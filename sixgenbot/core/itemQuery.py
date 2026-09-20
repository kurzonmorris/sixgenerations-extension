"""Finding items: one search box, filters down the side, a page at a time.

`docs/INTERFACE_LAYOUT.md §4` in code. Two rules shape all of it:

  * **Nothing loads the whole table.** Every count and every page is a query
    with a LIMIT. This has to hold at 100,000 items, not just at 2,125.
  * **The filters say what they are doing, in words.** "On sale, size 12, with
    photographs — 34 items", never a row of ticked boxes the reader must decode.

Money is pence in the database and pounds on the screen, as everywhere else.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, fields
from datetime import date, timedelta

from .database import searchItems
from .sku import SQL_ORDER

PAGE_SIZE = 50
SEARCH_CEILING = 1000     # a search that matches more than this says so

STATUS_WORDS = {
    "draft": "ready to list",
    "needs_info": "to review",
    "on_sale": "on sale",
    "reserved": "reserved",
    "sold": "sold",
    "posted": "posted",
    "completed": "completed",
    "archived": "archived",
    "removed": "removed",
}

SORTS = {
    "sku": ("Storage order", SQL_ORDER),
    "newest": ("Newest first", "dateAdded DESC, " + SQL_ORDER),
    "oldest": ("Oldest first", "dateAdded ASC, " + SQL_ORDER),
    "cheapest": ("Cheapest first", "price IS NULL, price ASC"),
    "dearest": ("Dearest first", "price IS NULL, price DESC"),
    "title": ("Title, A to Z", "title COLLATE NOCASE, " + SQL_ORDER),
}


# "Everything with no brand" is 385 items on the real catalogue, and "no size"
# is 424. Those are the batches worth working through, so each one is a choice
# rather than something to be built out of a search.
MISSING = {
    "brand": ("no brand", "brand = ''"),
    "title": ("no title", "title = ''"),
    "description": ("no description", "description = ''"),
    "price": ("no price", "(price IS NULL OR price <= 0)"),
    "weight": ("no weight", "weightGrams IS NULL"),
    "size": ("no size", "NOT EXISTS (SELECT 1 FROM itemAttribute a"
                        " WHERE a.itemId = item.itemId AND a.attribute = 'size')"),
    "colour": ("no colour", "NOT EXISTS (SELECT 1 FROM itemAttribute a"
                            " WHERE a.itemId = item.itemId AND a.attribute = 'colour')"),
    "photos": ("no photographs", "NOT EXISTS (SELECT 1 FROM itemImage p"
                                 " WHERE p.itemId = item.itemId AND p.filePath != '')"),
    "category": ("no category", "NOT EXISTS (SELECT 1 FROM itemCategory c"
                                " WHERE c.itemId = item.itemId)"),
}


@dataclass
class Filters:
    q: str = ""
    status: str = ""
    brand: str = ""
    size: str = ""
    colour: str = ""
    box: str = ""
    photos: str = ""          # yes | no
    listed: str = ""          # yes | no
    priceFrom: str = ""       # pounds, as typed
    priceTo: str = ""
    missing: str = ""         # a key of MISSING
    titleHas: str = ""
    descriptionHas: str = ""
    notesHas: str = ""
    addedFrom: str = ""       # 2026-04-01, or 2026-04-01 09:00
    addedTo: str = ""
    addedDays: str = ""       # added in the last N days
    checked: str = ""         # yes | no
    sharedCode: str = ""      # yes

    def anySet(self) -> bool:
        return any(getattr(self, f.name) for f in fields(self))

    def asPairs(self) -> list[tuple[str, str]]:
        """Every filter that is set, for putting back into a form or a link."""
        return [(f.name, getattr(self, f.name)) for f in fields(self)
                if getattr(self, f.name)]


def _endOfDay(when: str) -> str:
    """An inclusive "to" date.

    dateAdded holds "2026-04-21 13:11:32". Comparing that against "2026-04-21"
    would drop everything added that day, because the text is longer. Adding the
    end of the day fixes it and still lets the index do the work.
    """
    when = when.strip()
    return f"{when} 23:59:59" if len(when) == 10 else when


def _pence(pounds: str) -> int | None:
    cleaned = str(pounds or "").strip().lstrip("£").replace(",", "")
    try:
        return round(float(cleaned) * 100)
    except ValueError:
        return None


def buildWhere(connection: sqlite3.Connection, filters: Filters) -> tuple[str, list, bool]:
    """(where clause, parameters, the search hit its ceiling)."""
    clauses: list[str] = ["1 = 1"]
    parameters: list = []
    atCeiling = False

    if filters.q.strip():
        found = searchItems(connection, filters.q, limit=SEARCH_CEILING)
        atCeiling = len(found) == SEARCH_CEILING
        if not found:
            return "0 = 1", [], False
        clauses.append(f"itemId IN ({','.join('?' * len(found))})")
        parameters += found

    if filters.status:
        clauses.append("status = ?")
        parameters.append(filters.status)

    if filters.brand.strip():
        clauses.append("brand LIKE ?")
        parameters.append(f"%{filters.brand.strip()}%")

    if filters.box.strip():
        clauses.append("sku LIKE ?")
        parameters.append(f"{filters.box.strip().replace(' ', '-')}-%")

    if filters.size.strip():
        clauses.append(
            "EXISTS (SELECT 1 FROM itemAttribute a WHERE a.itemId = item.itemId"
            " AND a.attribute = 'size' AND a.value = ?)"
        )
        parameters.append(filters.size.strip())

    if filters.colour.strip():
        # Colours are free text — "Navy blue" should be found by "navy".
        clauses.append(
            "EXISTS (SELECT 1 FROM itemAttribute a WHERE a.itemId = item.itemId"
            " AND a.attribute = 'colour' AND a.value LIKE ?)"
        )
        parameters.append(f"%{filters.colour.strip()}%")

    if filters.photos in ("yes", "no"):
        word = "EXISTS" if filters.photos == "yes" else "NOT EXISTS"
        clauses.append(
            f"{word} (SELECT 1 FROM itemImage p WHERE p.itemId = item.itemId"
            " AND p.filePath != '')"
        )

    if filters.listed == "yes":
        clauses.append("dateListed IS NOT NULL")
    elif filters.listed == "no":
        clauses.append("dateListed IS NULL")

    low, high = _pence(filters.priceFrom), _pence(filters.priceTo)
    if low is not None:
        clauses.append("price >= ?")
        parameters.append(low)
    if high is not None:
        clauses.append("price <= ?")
        parameters.append(high)

    if filters.missing in MISSING:
        clauses.append(MISSING[filters.missing][1])

    for column, wanted in (("title", filters.titleHas),
                           ("description", filters.descriptionHas),
                           ("notes", filters.notesHas)):
        if wanted.strip():
            clauses.append(f"{column} LIKE ?")
            parameters.append(f"%{wanted.strip()}%")

    if filters.addedFrom.strip():
        clauses.append("dateAdded >= ?")
        parameters.append(filters.addedFrom.strip())
    if filters.addedTo.strip():
        clauses.append("dateAdded <= ?")
        parameters.append(_endOfDay(filters.addedTo))
    if filters.addedDays.strip().isdigit():
        since = date.today() - timedelta(days=int(filters.addedDays))
        clauses.append("dateAdded >= ?")
        parameters.append(since.isoformat())

    if filters.checked == "yes":
        clauses.append("verifiedAt IS NOT NULL")
    elif filters.checked == "no":
        clauses.append("verifiedAt IS NULL")

    if filters.sharedCode == "yes":
        clauses.append("sku LIKE '%#%'")

    return " AND ".join(clauses), parameters, atCeiling


def countItems(connection: sqlite3.Connection, where: str, parameters: list) -> int:
    return connection.execute(
        f"SELECT COUNT(*) AS total FROM item WHERE {where}", parameters
    ).fetchone()["total"]


def findPage(
    connection: sqlite3.Connection,
    where: str,
    parameters: list,
    sort: str = "sku",
    page: int = 1,
    pageSize: int = PAGE_SIZE,
) -> list[sqlite3.Row]:
    order = SORTS.get(sort, SORTS["sku"])[1]
    return list(
        connection.execute(
            f"SELECT * FROM item WHERE {where} ORDER BY {order} LIMIT ? OFFSET ?",
            parameters + [pageSize, (max(1, page) - 1) * pageSize],
        )
    )


def describe(filters: Filters, total: int) -> str:
    """The sentence above the results — INTERFACE_LAYOUT section 4.3.

    "On sale, size 12, with photographs — 34 items", in words, because a row of
    ticked boxes makes the reader work out what they are looking at.
    """
    parts: list[str] = []
    if filters.q.strip():
        parts.append(f"matching “{filters.q.strip()}”")
    if filters.status:
        parts.append(STATUS_WORDS.get(filters.status, filters.status))
    if filters.brand.strip():
        parts.append(f"brand {filters.brand.strip()}")
    if filters.size.strip():
        parts.append(f"size {filters.size.strip()}")
    if filters.colour.strip():
        parts.append(f"colour {filters.colour.strip()}")
    if filters.box.strip():
        parts.append(f"box {filters.box.strip()}")
    if filters.photos == "yes":
        parts.append("with photographs")
    elif filters.photos == "no":
        parts.append("without photographs")
    if filters.listed == "yes":
        parts.append("listed somewhere")
    elif filters.listed == "no":
        parts.append("never listed")
    if filters.priceFrom.strip() or filters.priceTo.strip():
        low = filters.priceFrom.strip() or "0"
        high = filters.priceTo.strip()
        parts.append(f"£{low} to £{high}" if high else f"£{low} and over")
    if filters.missing in MISSING:
        parts.append(f"with {MISSING[filters.missing][0]}")
    for label, wanted in (("title", filters.titleHas),
                          ("description", filters.descriptionHas),
                          ("notes", filters.notesHas)):
        if wanted.strip():
            parts.append(f"{label} containing “{wanted.strip()}”")
    if filters.addedDays.strip().isdigit():
        days = int(filters.addedDays)
        parts.append("added today" if days == 0 else f"added in the last {days} days")
    if filters.addedFrom.strip() or filters.addedTo.strip():
        low = filters.addedFrom.strip()
        high = filters.addedTo.strip()
        if low and high:
            parts.append(f"added between {low} and {high}")
        else:
            parts.append(f"added from {low}" if low else f"added up to {high}")
    if filters.checked == "yes":
        parts.append("already checked")
    elif filters.checked == "no":
        parts.append("not checked yet")
    if filters.sharedCode == "yes":
        parts.append("sharing a code with another item")

    counted = f"{total:,} item" + ("" if total == 1 else "s")
    if not parts:
        return f"Everything — {counted}."
    first = parts[0][0].upper() + parts[0][1:]
    return ", ".join([first] + parts[1:]) + f" — {counted}."


def choicesFor(connection: sqlite3.Connection) -> dict[str, list[str]]:
    """What to offer in the filter lists. Only values that actually exist."""
    sizes = [
        row["value"]
        for row in connection.execute(
            "SELECT value, COUNT(*) AS total FROM itemAttribute WHERE attribute = 'size'"
            " GROUP BY value ORDER BY total DESC LIMIT 60"
        )
    ]
    statuses = [
        row["status"]
        for row in connection.execute(
            "SELECT status, COUNT(*) AS total FROM item GROUP BY status ORDER BY total DESC"
        )
    ]
    return {"sizes": sorted(sizes), "statuses": statuses}
