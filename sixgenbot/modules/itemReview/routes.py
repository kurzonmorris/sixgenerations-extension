from urllib.parse import quote_plus

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ...core.appLogging import getLogger
from ...core.database import searchItems
from ...core.itemEdit import BY_NAME, FIELDS, applyEdits, currentValues, markChecked
from ...core.itemQuery import Filters, buildWhere, countItems, findPage
from ...core.readiness import factsFor, summarise
from ...core.sku import SQL_ORDER, formatSku
from ...core.webApp import render

router = APIRouter()
log = getLogger("review")

PAGE_SIZE = 50
MOST_AT_ONCE = 40          # a batch you can still hold in your head
MOST_IN_A_COLUMN = 200     # one box each, so many more fit before it is a wall
SEARCH_CEILING = 500

# Every column that can be shown, in the order they are drawn. The ones with a
# matching editable field become boxes on the edit screen; the rest are there to
# recognise the garment by.
COLUMNS = [
    ("sku", "SKU"),
    ("title", "Title"),
    ("brand", "Brand"),
    ("sizeUk", "Size UK"),
    ("sizeEu", "Size EU"),
    ("sizeUs", "Size US"),
    ("sizeLetter", "Size letter"),
    ("colours", "Colour"),
    ("price", "Price"),
    ("condition", "Condition"),
    ("weightGrams", "Weight in grams"),
    ("description", "Description"),
    ("notes", "Private notes"),
    ("photos", "Photos"),
    ("status", "Status"),
    ("listed", "Listed"),
    ("needs", "What it needs"),
]

COLUMN_NAMES = [name for name, _ in COLUMNS]
DEFAULT_COLUMNS = ["sku", "title", "brand", "sizeUk", "price", "needs"]

# Which list is being worked through. "Never listed" is the 988 — the ones the
# whole project exists to put back up.
LISTS = {
    "unchecked": "Not checked yet",
    "offline": "Never listed",
    "listed": "Listed, not checked",
}

NOT_IN_PLAY = "('sold','posted','completed','archived','removed')"


def chosenColumns(request: Request, show: str) -> list[str]:
    raw = show if show else request.cookies.get("reviewColumns", "")
    picked = [name for name in raw.split(",") if name in COLUMN_NAMES]
    return picked or DEFAULT_COLUMNS


def _where(which: str) -> str:
    clause = f"verifiedAt IS NULL AND status NOT IN {NOT_IN_PLAY}"
    if which == "offline":
        return clause + " AND dateListed IS NULL"
    if which == "listed":
        return clause + " AND dateListed IS NOT NULL"
    return clause


def findItems(connection, which: str, q: str, page: int) -> tuple[list, int]:
    where = _where(which)
    parameters: list = []

    if q.strip():
        found = searchItems(connection, q, limit=SEARCH_CEILING)
        if not found:
            return [], 0
        where += f" AND itemId IN ({','.join('?' * len(found))})"
        parameters = found

    total = connection.execute(
        f"SELECT COUNT(*) AS total FROM item WHERE {where}", parameters
    ).fetchone()["total"]

    rows = connection.execute(
        f"SELECT * FROM item WHERE {where} ORDER BY {SQL_ORDER} LIMIT ? OFFSET ?",
        parameters + [PAGE_SIZE, (page - 1) * PAGE_SIZE],
    ).fetchall()
    return rows, total


def describe(connection, row, columns: list[str]) -> dict:
    """One row, carrying only what the chosen columns actually need."""
    itemId = row["itemId"]
    cells = {"sku": formatSku(row["sku"]) or row["sku"],
             "status": row["status"].replace("_", " "),
             "listed": row["dateListed"] or "no"}

    if any(name in BY_NAME for name in columns):
        cells.update(currentValues(connection, itemId))
    if "photos" in columns:
        cells["photos"] = connection.execute(
            "SELECT COUNT(*) AS total FROM itemImage WHERE itemId = ?", (itemId,)
        ).fetchone()["total"]
    if "needs" in columns:
        cells["needs"] = summarise(factsFor(connection, itemId))

    return {"itemId": itemId, "sku": cells["sku"], "title": row["title"], "cells": cells}


@router.get("/review", response_class=HTMLResponse, include_in_schema=False)
def review(request: Request, which: str = "unchecked", q: str = "", page: int = 1,
           show: str = "", message: str = ""):
    bot = request.app.state.bot
    connection = bot.db.connection()
    which = which if which in LISTS else "unchecked"
    page = max(1, page)
    columns = chosenColumns(request, show)

    rows, total = findItems(connection, which, q, page)
    pages = max(1, -(-total // PAGE_SIZE))

    response = render(
        request,
        "itemReview/review.html",
        message=message,
        which=which,
        lists=LISTS,
        q=q,
        page=min(page, pages),
        pages=pages,
        total=total,
        columns=columns,
        allColumns=COLUMNS,
        mostAtOnce=MOST_AT_ONCE,
        items=[describe(connection, row, columns) for row in rows],
    )
    if show:
        response.set_cookie("reviewColumns", ",".join(columns), max_age=60 * 60 * 24 * 365)
    return response


@router.post("/review/edit", response_class=HTMLResponse, include_in_schema=False)
async def edit(request: Request):
    """The chosen items, ready to change.

    Two ways in: the ticked rows, or everything that matches the filters. Two
    ways to lay it out: one card per item, or **one column** — every item's
    brand under one another, which is what makes Tab walk down the column
    instead of across one item.
    """
    bot = request.app.state.bot
    connection = bot.db.connection()
    form = await request.form()

    only = form.get("only", "")
    only = only if only in BY_NAME else ""
    limit = MOST_IN_A_COLUMN if only else MOST_AT_ONCE

    columns = chosenColumns(request, form.get("columns", ""))
    fields = [BY_NAME[only]] if only else [BY_NAME[name] for name in columns if name in BY_NAME]

    if form.get("useFilters") == "yes":
        filters = Filters(**{
            name: form.get(name, "") for name in Filters().__dataclass_fields__
        })
        where, parameters, _ = buildWhere(connection, filters)
        matched = countItems(connection, where, parameters)
        picked = [row["itemId"] for row in findPage(connection, where, parameters, "sku", 1, limit)]
        carry = list(filters.asPairs())
    else:
        ticked = form.getlist("pick")
        matched, picked, carry = len(ticked), ticked[:limit], []

    if not picked:
        return RedirectResponse("/review?message=Tick+the+items+you+want+to+work+on.",
                                status_code=303)
    if not fields:
        return RedirectResponse("/review?message=Choose+at+least+one+thing+to+change.",
                                status_code=303)

    items = []
    for itemId in picked:
        row = connection.execute(
            "SELECT sku, title FROM item WHERE itemId = ?", (itemId,)
        ).fetchone()
        if row is None:
            continue
        thumbnail = connection.execute(
            "SELECT imageId FROM itemImage WHERE itemId = ? AND filePath != ''"
            " ORDER BY position LIMIT 1", (itemId,)
        ).fetchone()
        items.append({
            "itemId": itemId,
            "sku": formatSku(row["sku"]) or row["sku"],
            "title": row["title"],
            "thumbnail": thumbnail["imageId"] if thumbnail else None,
            "values": currentValues(connection, itemId),
            "needs": summarise(factsFor(connection, itemId)),
        })

    return render(
        request,
        "itemReview/reviewEdit.html",
        items=items,
        fields=fields,
        only=only,
        everyField=FIELDS,
        matched=matched,
        limit=limit,
        columns=",".join(columns),
        carry=carry,
        back=form.get("back", "/review"),
        which=form.get("which", "unchecked"),
    )


@router.post("/review/save", include_in_schema=False)
async def save(request: Request):
    bot = request.app.state.bot
    connection = bot.db.connection()
    form = await request.form()

    edits: dict[str, dict[str, str]] = {}
    for key in form.keys():
        parts = key.split(":", 2)
        if len(parts) == 3 and parts[0] == "f":
            edits.setdefault(parts[1], {})[parts[2]] = form[key]

    # One column at a time has no box per row — it would sit between the two
    # boxes Tab is meant to join. The whole batch is marked together instead.
    everyOne = form.get("checkAll") == "yes"

    changed = checked = 0
    connection.execute("BEGIN IMMEDIATE")
    try:
        for itemId, changes in edits.items():
            made = applyEdits(connection, itemId, changes)
            changed += len(made)
            wanted = everyOne or form.get(f"checked:{itemId}")
            if wanted and markChecked(connection, itemId):
                checked += 1
        connection.execute("COMMIT")
    except Exception as error:
        connection.execute("ROLLBACK")
        log.error(f"batch save failed, nothing was changed: {error}")
        return RedirectResponse(
            "/review?message=Nothing+was+saved.+Please+try+again.", status_code=303
        )

    if changed or checked:
        bot.emit("items.edited", items=len(edits), changes=changed, checked=checked)
    log.info(f"{len(edits)} items, {changed} changes, {checked} marked as checked")

    message = quote_plus(
        f"Saved {len(edits)} items. {changed} changes, {checked} marked as checked."
    )
    back = form.get("back", "") or f"/review?which={form.get('which', 'unchecked')}"
    joiner = "&" if "?" in back else "?"
    return RedirectResponse(f"{back}{joiner}message={message}", status_code=303)
