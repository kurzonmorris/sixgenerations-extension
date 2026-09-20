import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from fastapi import APIRouter, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

from ...core.appLogging import getLogger
from ...core.photoStore import (
    duplicateImages,
    failureReasons,
    fetchAll,
    imagesFolder,
    storedCounts,
)
from ...core.photoOrder import move, photosFor
from ...core.sku import formatSku
from ...core.thumbnails import thumbnailFor
from ...core.webApp import render

router = APIRouter()
log = getLogger("photos")


@dataclass
class Run:
    """What the one fetch that may be in flight is doing.

    One run at a time, on purpose: two would fight over the same rows and the
    page could not say anything true about either.
    """

    running: bool = False
    stopping: bool = False
    done: int = 0
    wanted: int = 0
    startedAt: str = ""
    finishedAt: str = ""
    outcome: str = ""


run = Run()
lock = threading.Lock()


def _fetch(bot, limit: int | None) -> None:
    def progress(done: int, wanted: int) -> None:
        run.done, run.wanted = done, wanted

    try:
        counts = fetchAll(
            bot.db.connection(),
            bot.config.dataDir,
            limit=limit,
            onProgress=progress,
            shouldStop=lambda: run.stopping,
        )
        run.outcome = counts.asSentence()
        bot.emit("photos.fetched", fetched=counts.fetched, failed=counts.failed)
    except Exception as error:
        log.error(f"the photo fetch stopped: {error}")
        run.outcome = f"It stopped early: {error}"
    finally:
        with lock:
            run.running = False
            run.stopping = False
            run.finishedAt = datetime.now().strftime("%d %b %Y %H:%M")


@router.get("/photos", response_class=HTMLResponse, include_in_schema=False)
def photos(request: Request, message: str = ""):
    bot = request.app.state.bot
    connection = bot.db.connection()
    return render(
        request,
        "photoLibrary/photos.html",
        message=message,
        counts=storedCounts(connection),
        reasons=failureReasons(connection),
        run=run,
    )


@router.post("/photos/fetch", include_in_schema=False)
def startFetch(request: Request, howMany: str = Form("")):
    bot = request.app.state.bot
    with lock:
        if run.running:
            return RedirectResponse("/photos?message=It+is+already+running.", status_code=303)
        run.running, run.stopping = True, False
        run.done, run.wanted, run.outcome, run.finishedAt = 0, 0, "", ""
        run.startedAt = datetime.now().strftime("%d %b %Y %H:%M")

    limit = int(howMany) if howMany.strip().isdigit() else None
    threading.Thread(target=_fetch, args=(bot, limit), daemon=True).start()
    return RedirectResponse("/photos", status_code=303)


@router.post("/photos/stop", include_in_schema=False)
def stopFetch():
    """Asks it to stop. It finishes the photos already in the air first."""
    with lock:
        if run.running:
            run.stopping = True
    return RedirectResponse("/photos?message=Stopping.+Check+again+in+a+moment.",
                            status_code=303)


@router.get("/photos/duplicates", response_class=HTMLResponse, include_in_schema=False)
def duplicates(request: Request):
    """Identical photographs held against more than one item, by content.

    This is what answers whether two listings with the same title are the same
    garment relisted, or two different ones — EXPLAINED section 3B.11. URLs
    could never answer it: Crosslist copies images when a listing is duplicated.
    """
    connection = request.app.state.bot.db.connection()
    shared = duplicateImages(connection)
    return render(
        request,
        "photoLibrary/duplicates.html",
        shared=shared[:200],
        total=len(shared),
        ready=storedCounts(connection)["here"],
    )


@router.get("/photos/image/{imageId}", include_in_schema=False)
def image(request: Request, imageId: int, small: str = ""):
    """The photograph. `small=yes` serves the small copy, made on first asking."""
    bot = request.app.state.bot
    row = bot.db.connection().execute(
        "SELECT filePath FROM itemImage WHERE imageId = ?", (imageId,)
    ).fetchone()
    if row is None or not row["filePath"]:
        return RedirectResponse("/photos?message=That+photo+is+not+here+yet.", status_code=303)

    folder = imagesFolder(bot.config.dataDir).resolve()
    path = Path(row["filePath"]).resolve()
    if folder not in path.parents or not path.is_file():
        return RedirectResponse("/photos?message=That+photo+is+not+here+yet.", status_code=303)

    if small == "yes":
        smaller = thumbnailFor(bot.config.dataDir, imageId, path)
        if smaller is not None:
            return FileResponse(smaller, media_type="image/jpeg")
    return FileResponse(path)


@router.get("/photos/order/{itemId}", response_class=HTMLResponse, include_in_schema=False)
def order(request: Request, itemId: str, back: str = "/table", message: str = ""):
    """One item's photographs, biggest first, with buttons to move them."""
    bot = request.app.state.bot
    connection = bot.db.connection()
    row = connection.execute(
        "SELECT sku, title FROM item WHERE itemId = ?", (itemId,)
    ).fetchone()
    if row is None:
        return RedirectResponse("/table?message=There+is+no+such+item.", status_code=303)

    return render(
        request,
        "photoLibrary/order.html",
        itemId=itemId,
        sku=formatSku(row["sku"]) or row["sku"],
        title=row["title"],
        photos=photosFor(connection, itemId),
        back=back,
        message=message,
    )


@router.post("/photos/order/{itemId}", include_in_schema=False)
async def reorder(request: Request, itemId: str):
    bot = request.app.state.bot
    form = await request.form()
    back = form.get("back", "/table")

    imageId = form.get("imageId", "")
    where = form.get("where", "")
    if imageId.isdigit() and where in ("up", "down", "first"):
        moved = move(bot.db.connection(), itemId, int(imageId), where)
        if moved:
            bot.emit("photos.reordered", item=itemId)
            log.info(f"photographs reordered for {itemId}")

    return RedirectResponse(
        f"/photos/order/{itemId}?back={quote_plus(back)}", status_code=303
    )
