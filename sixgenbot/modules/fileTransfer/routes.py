import re
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from ...core.appLogging import getLogger
from ...core.backup import listBackups
from ...core.crosslistImport import importExport
from ...core.csvExport import exportItems
from ...core.webApp import render

router = APIRouter()
log = getLogger("files")

SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")
BIGGEST = 200 * 1024 * 1024      # a 2 MB export has room to grow a hundredfold


def importsFolder(bot) -> Path:
    folder = bot.config.dataDir / "imports"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def tidyName(name: str) -> str:
    """Whatever the browser sent becomes a plain filename in our own folder."""
    return SAFE_NAME.sub("_", Path(name or "").name).strip("._") or "upload.csv"


def insideFolder(folder: Path, name: str) -> Path | None:
    """Resolves a name against one folder and refuses anything that escapes it."""
    candidate = (folder / Path(name).name).resolve()
    return candidate if candidate.parent == folder.resolve() and candidate.is_file() else None


@router.get("/files", response_class=HTMLResponse, include_in_schema=False)
def files(request: Request, message: str = ""):
    bot = request.app.state.bot
    uploaded = sorted(
        importsFolder(bot).glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    return render(
        request,
        "fileTransfer/files.html",
        message=message,
        uploaded=[
            {
                "name": path.name,
                "bytes": path.stat().st_size,
                "when": datetime.fromtimestamp(path.stat().st_mtime),
            }
            for path in uploaded
        ],
        backups=listBackups(bot.config.dataDir)[:5],
        counts=bot.db.counts(),
    )


@router.post("/files/upload", include_in_schema=False)
async def upload(request: Request, spreadsheet: UploadFile):
    bot = request.app.state.bot
    name = tidyName(spreadsheet.filename)

    if not name.lower().endswith(".csv"):
        return RedirectResponse("/files?message=That+is+not+a+CSV+file.", status_code=303)

    raw = await spreadsheet.read()
    if len(raw) > BIGGEST:
        return RedirectResponse("/files?message=That+file+is+too+big.", status_code=303)

    (importsFolder(bot) / name).write_bytes(raw)
    log.info(f"uploaded {name} ({len(raw):,} bytes)")
    return RedirectResponse(f"/files/preview/{name}", status_code=303)


@router.get("/files/preview/{name}", response_class=HTMLResponse, include_in_schema=False)
def preview(request: Request, name: str):
    """What importing it would do. Nothing is written by looking."""
    bot = request.app.state.bot
    path = insideFolder(importsFolder(bot), name)
    if path is None:
        return RedirectResponse("/files?message=There+is+no+such+file.", status_code=303)

    try:
        counts = importExport(bot.db.connection(), path, dryRun=True)
        problem = ""
    except Exception as error:
        counts, problem = None, str(error)

    return render(request, "fileTransfer/preview.html", fileName=name, counts=counts, problem=problem)


@router.post("/files/import/{name}", include_in_schema=False)
def runImport(request: Request, name: str):
    bot = request.app.state.bot
    path = insideFolder(importsFolder(bot), name)
    if path is None:
        return RedirectResponse("/files?message=There+is+no+such+file.", status_code=303)

    try:
        counts = importExport(bot.db.connection(), path, dryRun=False)
        bot.emit("import.finished", file=name, created=counts.created, updated=counts.updated)
        message = f"Imported {name}: {counts.created} new, {counts.updated} updated."
    except Exception as error:
        log.error(f"import of {name} failed: {error}")
        message = f"{name} could not be imported: {error}"

    return RedirectResponse(f"/files?message={message.replace(' ', '+')}", status_code=303)


@router.get("/files/items.csv", include_in_schema=False)
def downloadItems(request: Request, status: str = ""):
    bot = request.app.state.bot
    body = exportItems(bot.db.connection(), status=status)
    stamp = datetime.now().strftime("%Y-%m-%d")
    label = f"sixgen_{status or 'items'}_{stamp}.csv"
    return Response(
        body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{label}"'},
    )


@router.get("/files/backup/{name}", include_in_schema=False)
def downloadBackup(request: Request, name: str):
    bot = request.app.state.bot
    path = insideFolder(bot.config.dataDir / "backups", name)
    if path is None:
        return RedirectResponse("/files?message=There+is+no+such+backup.", status_code=303)
    return Response(
        path.read_bytes(),
        media_type="application/gzip",
        headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
    )
