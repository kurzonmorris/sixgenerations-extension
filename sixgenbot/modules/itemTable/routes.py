from urllib.parse import urlencode

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from ...core.appLogging import getLogger
from ...core.itemQuery import (
    MISSING,
    PAGE_SIZE,
    SEARCH_CEILING,
    SORTS,
    STATUS_WORDS,
    Filters,
    buildWhere,
    choicesFor,
    countItems,
    describe,
    findPage,
)
from ...core.sku import formatSku
from ...core.webApp import render

router = APIRouter()
log = getLogger("table")

COLUMNS = [
    ("photo", "Photo"),
    ("sku", "SKU"),
    ("title", "Title"),
    ("brand", "Brand"),
    ("size", "Size"),
    ("colour", "Colour"),
    ("price", "Price"),
    ("status", "Status"),
    ("photos", "Photos"),
    ("listed", "Listed"),
    ("added", "Added"),
]

COLUMN_NAMES = [name for name, _ in COLUMNS]
DEFAULT_COLUMNS = ["photo", "sku", "title", "brand", "size", "price", "status"]


def _withoutPage(request: Request) -> str:
    """The current query again, minus the page, so a paging link can add its own."""
    kept = [(k, v) for k, v in request.query_params.multi_items() if k != "page"]
    return urlencode(kept)


def chosenColumns(request: Request, show: list[str]) -> list[str]:
    picked = [name for name in show if name in COLUMN_NAMES]
    if picked:
        return picked
    remembered = request.cookies.get("tableColumns", "")
    picked = [name for name in remembered.split(",") if name in COLUMN_NAMES]
    return picked or DEFAULT_COLUMNS


def _decorate(connection, rows: list, columns: list[str]) -> list[dict]:
    """Everything the chosen columns need, in as few queries as the page has.

    One query per kind of thing, for the page's 50 rows — never one per row,
    which is what makes a table feel slow at 100,000 items.
    """
    if not rows:
        return []
    ids = [row["itemId"] for row in rows]
    marks = ",".join("?" * len(ids))

    thumbnails: dict[str, int] = {}
    if "photo" in columns:
        for image in connection.execute(
            f"SELECT itemId, MIN(position) AS first, imageId FROM itemImage"
            f" WHERE itemId IN ({marks}) AND filePath != '' GROUP BY itemId",
            ids,
        ):
            thumbnails[image["itemId"]] = image["imageId"]

    counted: dict[str, int] = {}
    if "photos" in columns:
        for image in connection.execute(
            f"SELECT itemId, COUNT(*) AS total FROM itemImage"
            f" WHERE itemId IN ({marks}) GROUP BY itemId",
            ids,
        ):
            counted[image["itemId"]] = image["total"]

    attributes: dict[tuple[str, str], list[str]] = {}
    if "size" in columns or "colour" in columns:
        for row in connection.execute(
            f"SELECT itemId, attribute, value, system FROM itemAttribute"
            f" WHERE itemId IN ({marks}) AND attribute IN ('size', 'colour')"
            " ORDER BY isPrimary DESC, position",
            ids,
        ):
            shown = f"{row['value']} {row['system']}".strip() if row["attribute"] == "size" \
                else row["value"]
            attributes.setdefault((row["itemId"], row["attribute"]), []).append(shown)

    made = []
    for row in rows:
        itemId = row["itemId"]
        made.append({
            "itemId": itemId,
            "cells": {
                "photo": thumbnails.get(itemId),
                "sku": formatSku(row["sku"]) or row["sku"],
                "title": row["title"],
                "brand": row["brand"],
                "size": ", ".join(attributes.get((itemId, "size"), [])),
                "colour": ", ".join(attributes.get((itemId, "colour"), [])),
                "price": "" if row["price"] is None else f"£{row['price'] / 100:.2f}",
                "status": STATUS_WORDS.get(row["status"], row["status"]),
                "photos": counted.get(itemId, 0),
                "listed": row["dateListed"] or "never",
                "added": row["dateAdded"] or "",
            },
        })
    return made


@router.get("/table", response_class=HTMLResponse, include_in_schema=False)
def table(
    request: Request,
    q: str = "",
    status: str = "",
    brand: str = "",
    size: str = "",
    colour: str = "",
    box: str = "",
    photos: str = "",
    listed: str = "",
    priceFrom: str = "",
    priceTo: str = "",
    missing: str = "",
    titleHas: str = "",
    descriptionHas: str = "",
    notesHas: str = "",
    addedFrom: str = "",
    addedTo: str = "",
    addedDays: str = "",
    checked: str = "",
    sharedCode: str = "",
    sort: str = "sku",
    page: int = 1,
    show: list[str] | None = Query(None),
    message: str = "",
):
    bot = request.app.state.bot
    connection = bot.db.connection()
    filters = Filters(q, status, brand, size, colour, box, photos, listed, priceFrom,
                      priceTo, missing, titleHas, descriptionHas, notesHas, addedFrom,
                      addedTo, addedDays, checked, sharedCode)
    sort = sort if sort in SORTS else "sku"
    page = max(1, page)
    columns = chosenColumns(request, show or [])

    where, parameters, atCeiling = buildWhere(connection, filters)
    total = countItems(connection, where, parameters)
    pages = max(1, -(-total // PAGE_SIZE))
    page = min(page, pages)
    rows = findPage(connection, where, parameters, sort, page, PAGE_SIZE)

    response = render(
        request,
        "itemTable/table.html",
        filters=filters,
        message=message,
        carry=filters.asPairs(),
        missingChoices=[(name, words) for name, (words, _) in MISSING.items()],
        sentence=describe(filters, total),
        atCeiling=atCeiling,
        ceiling=SEARCH_CEILING,
        total=total,
        page=page,
        pages=pages,
        sort=sort,
        sorts=SORTS,
        columns=columns,
        allColumns=COLUMNS,
        choices=choicesFor(connection),
        statusWords=STATUS_WORDS,
        items=_decorate(connection, rows, columns),
        baseQuery=_withoutPage(request),
    )
    if show:
        response.set_cookie("tableColumns", ",".join(columns), max_age=60 * 60 * 24 * 365)
    return response
