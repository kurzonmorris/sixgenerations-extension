from datetime import datetime
from urllib.parse import quote_plus

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from ...core.appLogging import getLogger
from ...core.database import reindexItem
from ...core.itemEdit import readMoney
from ...core.listingSheet import photoZip, sheetFor, waitingToList
from ...core.readiness import factsFor, summarise
from ...core.sku import formatSku
from ...core.webApp import render

router = APIRouter()
log = getLogger("listing")


@router.get("/list", response_class=HTMLResponse, include_in_schema=False)
def waiting(request: Request, message: str = ""):
    """What could go up next: never listed, and the photographs are here."""
    bot = request.app.state.bot
    connection = bot.db.connection()
    rows = waitingToList(connection)

    total = connection.execute(
        "SELECT COUNT(*) AS total FROM item WHERE dateListed IS NULL"
        " AND status NOT IN ('sold','posted','completed','archived','removed')"
    ).fetchone()["total"]
    withoutPhotos = connection.execute(
        "SELECT COUNT(*) AS total FROM item WHERE dateListed IS NULL"
        " AND status NOT IN ('sold','posted','completed','archived','removed')"
        " AND NOT EXISTS (SELECT 1 FROM itemImage p WHERE p.itemId = item.itemId"
        "                 AND p.filePath != '')"
    ).fetchone()["total"]

    return render(
        request,
        "listingHelper/waiting.html",
        message=message,
        neverListed=total,
        withoutPhotos=withoutPhotos,
        items=[{
            "itemId": row["itemId"],
            "sku": formatSku(row["sku"]) or row["sku"],
            "title": row["title"],
            "needs": summarise(factsFor(connection, row["itemId"])),
        } for row in rows],
    )


@router.get("/list/{itemId}", response_class=HTMLResponse, include_in_schema=False)
def sheet(request: Request, itemId: str, message: str = ""):
    bot = request.app.state.bot
    made = sheetFor(bot.db.connection(), itemId)
    if made is None:
        return RedirectResponse("/list?message=There+is+no+such+item.", status_code=303)
    return render(request, "listingHelper/sheet.html", sheet=made, message=message)


@router.get("/list/{itemId}/photos.zip", include_in_schema=False)
def photos(request: Request, itemId: str):
    bot = request.app.state.bot
    connection = bot.db.connection()
    row = connection.execute("SELECT sku FROM item WHERE itemId = ?", (itemId,)).fetchone()
    if row is None:
        return RedirectResponse("/list?message=There+is+no+such+item.", status_code=303)

    label = (formatSku(row["sku"]) or row["sku"]).replace(" ", "-")
    body = photoZip(connection, itemId, label)
    return Response(
        body,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{label}.zip"'},
    )


@router.post("/list/{itemId}/listed", include_in_schema=False)
def markListed(request: Request, itemId: str, url: str = Form(""), price: str = Form("")):
    """Records that this is now on Vinted, because you have just put it there.

    `readiness.suggestedStatus()` never returns `on_sale`, and that is right:
    being ready is not being listed. This is the other half — a person saying it
    is up, which is the only thing that can say so until the Vinted read exists.
    """
    bot = request.app.state.bot
    connection = bot.db.connection()
    row = connection.execute("SELECT sku, price FROM item WHERE itemId = ?", (itemId,)).fetchone()
    if row is None:
        return RedirectResponse("/list?message=There+is+no+such+item.", status_code=303)

    now = datetime.now().isoformat(timespec="seconds")
    listedPrice = readMoney(price) if price.strip() else row["price"]

    connection.execute("BEGIN IMMEDIATE")
    try:
        connection.execute(
            "UPDATE item SET dateListed = ?, status = 'on_sale' WHERE itemId = ?", (now, itemId))
        connection.execute(
            "INSERT INTO listing (itemId, platform, url, state, price, listedAt)"
            " VALUES (?, 'vinted', ?, 'live', ?, ?)"
            " ON CONFLICT (itemId, platform) DO UPDATE SET"
            " url = excluded.url, state = 'live', price = excluded.price,"
            " listedAt = excluded.listedAt",
            (itemId, url.strip(), listedPrice, now))
        connection.execute(
            "INSERT INTO event (happenedAt, actor, action, subject, field, valueBefore, valueAfter)"
            " VALUES (?, 'user', 'listed', ?, 'Vinted', 'not listed', ?)",
            (now, itemId, url.strip() or "live"))
        connection.execute("COMMIT")
    except Exception as error:
        connection.execute("ROLLBACK")
        log.error(f"could not record the listing for {itemId}: {error}")
        return RedirectResponse(
            f"/list/{itemId}?message=That+could+not+be+saved.+Please+try+again.",
            status_code=303)

    reindexItem(connection, itemId)
    bot.emit("item.listed", item=itemId, platform="vinted")
    log.info(f"{row['sku']} recorded as listed on Vinted")

    done = quote_plus(f"{formatSku(row['sku']) or row['sku']} is up. That is one more.")
    return RedirectResponse(f"/list?message={done}", status_code=303)
