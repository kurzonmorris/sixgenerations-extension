import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from ...core.appLogging import getLogger
from ...core.sku import formatSku, parseSku
from ...core.vintedRead import applyRead, planRead
from ...core.webApp import render

router = APIRouter()
log = getLogger("vinted")

SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")
BIGGEST = 40 * 1024 * 1024        # 2,000 listings of JSON is well under a megabyte


def readsFolder(bot) -> Path:
    folder = bot.config.dataDir / "reads"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def insideFolder(folder: Path, name: str) -> Path | None:
    candidate = (folder / Path(name).name).resolve()
    return candidate if candidate.parent == folder.resolve() and candidate.is_file() else None


def itemsFrom(raw: bytes) -> list[dict]:
    """The extension sends {items: [...]}; a hand-saved file may be a bare list."""
    loaded = json.loads(raw.decode("utf-8"))
    items = loaded.get("items", []) if isinstance(loaded, dict) else loaded
    if not isinstance(items, list):
        raise ValueError("that file does not hold a list of listings")
    return [item for item in items if isinstance(item, dict)]


@router.get("/vinted", response_class=HTMLResponse, include_in_schema=False)
def vinted(request: Request, message: str = ""):
    bot = request.app.state.bot
    reads = sorted(readsFolder(bot).glob("*.json"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    onVinted = bot.db.connection().execute(
        "SELECT COUNT(*) AS total FROM listing WHERE platform = 'vinted' AND state = 'live'"
    ).fetchone()["total"]

    return render(
        request,
        "vintedSync/vinted.html",
        message=message,
        onVinted=onVinted,
        reads=[{"name": path.name,
                "when": datetime.fromtimestamp(path.stat().st_mtime),
                "bytes": path.stat().st_size} for path in reads[:10]],
    )


@router.post("/vinted/read", include_in_schema=False)
async def receive(request: Request):
    """Where the extension sends a wardrobe read.

    It only stores it and answers with what it would do. Nothing is written to
    the catalogue here, so a POST that was not expected cannot change anything.
    """
    bot = request.app.state.bot
    raw = await request.body()
    if len(raw) > BIGGEST:
        return JSONResponse({"error": "that read is too big"}, status_code=413)

    try:
        items = itemsFrom(raw)
    except Exception as error:
        return JSONResponse({"error": f"that read could not be understood: {error}"},
                            status_code=400)

    name = f"vinted-{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    (readsFolder(bot) / name).write_bytes(raw)
    plan = planRead(bot.db.connection(), items)
    log.info(f"read of {len(items)} Vinted listings stored as {name}: {plan.asSentence()}")

    return JSONResponse({
        "stored": name,
        "listings": len(items),
        "wouldDo": plan.asSentence(),
        "nothingWritten": True,
        "openThisPage": "/vinted",
    })


@router.post("/vinted/upload", include_in_schema=False)
async def upload(request: Request, wardrobe: UploadFile):
    bot = request.app.state.bot
    raw = await wardrobe.read()
    if len(raw) > BIGGEST:
        return RedirectResponse("/vinted?message=That+file+is+too+big.", status_code=303)
    try:
        itemsFrom(raw)
    except Exception as error:
        return RedirectResponse(
            f"/vinted?message=That+file+could+not+be+read:+{error}".replace(" ", "+"),
            status_code=303)

    name = SAFE_NAME.sub("_", Path(wardrobe.filename or "").name) or "wardrobe.json"
    if not name.endswith(".json"):
        name += ".json"
    (readsFolder(bot) / name).write_bytes(raw)
    return RedirectResponse(f"/vinted/plan/{name}", status_code=303)


@router.get("/vinted/plan/{name}", response_class=HTMLResponse, include_in_schema=False)
def plan(request: Request, name: str, message: str = ""):
    """What this read would change. Nothing is written by looking."""
    bot = request.app.state.bot
    path = insideFolder(readsFolder(bot), name)
    if path is None:
        return RedirectResponse("/vinted?message=There+is+no+such+read.", status_code=303)

    try:
        made = planRead(bot.db.connection(), itemsFrom(path.read_bytes()))
        problem = ""
    except Exception as error:
        made, problem = None, str(error)

    return render(request, "vintedSync/plan.html",
                  fileName=name, plan=made, problem=problem, message=message)


@router.post("/vinted/apply/{name}", include_in_schema=False)
def apply(request: Request, name: str):
    bot = request.app.state.bot
    path = insideFolder(readsFolder(bot), name)
    if path is None:
        return RedirectResponse("/vinted?message=There+is+no+such+read.", status_code=303)

    try:
        made = applyRead(bot.db.connection(), itemsFrom(path.read_bytes()), dryRun=False)
    except Exception as error:
        log.error(f"applying {name} failed, nothing was changed: {error}")
        return RedirectResponse(
            f"/vinted/plan/{name}?message=Nothing+was+changed.+Please+try+again.",
            status_code=303)

    bot.emit("vinted.read.applied", file=name, new=len(made.newItems))
    log.info(f"applied {name}: {made.asSentence()}")
    return RedirectResponse(
        f"/vinted?message={made.asSentence().replace(' ', '+')}", status_code=303)


@router.post("/vinted/link", include_in_schema=False)
async def link(request: Request):
    """Joins one Vinted listing to one garment, by hand.

    Most listings cannot be matched on their own: 377 have no code at the end,
    and 621 carry a code two garments share. **This only has to be done once
    each.** After it, the Vinted listing id settles that pairing for good and no
    future read will ask again.
    """
    bot = request.app.state.bot
    connection = bot.db.connection()
    form = await request.form()

    sourceId = str(form.get("sourceId", "")).strip()
    wanted = str(form.get("itemId", "")).strip()
    typed = str(form.get("sku", "")).strip()
    back = str(form.get("back", "/vinted"))

    if not sourceId:
        return RedirectResponse(f"{back}?message=That+listing+has+no+address.", status_code=303)

    if wanted:
        # A garment picked from the page. This is the only way to settle a code
        # two garments share, because the code itself is the ambiguity.
        found = connection.execute(
            "SELECT itemId, sku FROM item WHERE itemId = ?", (wanted,)).fetchall()
    else:
        code = parseSku(typed) or parseSku(f"x {typed}")
        if not code:
            return RedirectResponse(f"{back}?message=Type+a+SKU+like+13-8+24.", status_code=303)
        found = connection.execute(
            "SELECT itemId, sku FROM item WHERE sku = ? OR sku LIKE ?", (code, f"{code} #%")
        ).fetchall()

    if len(found) != 1:
        words = ("No item has that SKU." if not found
                 else "Two items share that SKU — pick one from the list instead.")
        return RedirectResponse(f"{back}?message={words.replace(' ', '+')}", status_code=303)

    itemId = found[0]["itemId"]
    now = datetime.now().isoformat(timespec="seconds")
    connection.execute(
        "INSERT INTO listing (itemId, platform, externalId, url, state, lastSyncedAt)"
        " VALUES (?, 'vinted', ?, ?, 'live', ?)"
        " ON CONFLICT (itemId, platform) DO UPDATE SET"
        " externalId = excluded.externalId, url = excluded.url, lastSyncedAt = excluded.lastSyncedAt",
        (itemId, sourceId, str(form.get("url", "")).strip(), now))
    connection.execute(
        "INSERT INTO event (happenedAt, actor, action, subject, field, valueBefore, valueAfter)"
        " VALUES (?, 'user', 'linked', ?, 'Vinted listing', '', ?)", (now, itemId, sourceId))
    log.info(f"listing {sourceId} linked to {found[0]['sku']} by hand")

    shown = formatSku(found[0]["sku"]) or found[0]["sku"]
    linked = shown.replace(" ", "+")
    return RedirectResponse(
        f"{back}?message=Linked+to+{linked}.+It+will+not+be+asked+again.", status_code=303)
