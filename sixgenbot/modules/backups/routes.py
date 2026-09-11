from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from ...core.appLogging import getLogger
from ...core.backup import listBackups, makeBackup
from ...core.webApp import render

router = APIRouter()
log = getLogger("backups")


def runBackup(bot):
    """Shared by the nightly job and the button, so they cannot drift apart."""
    made = makeBackup(bot.db.path, bot.config.dataDir)
    bot.emit("backup.taken", path=str(made.path), bytes=made.bytes)
    return made


@router.get("/backups", response_class=HTMLResponse, include_in_schema=False)
def backups(request: Request):
    bot = request.app.state.bot
    files = listBackups(bot.config.dataDir)
    return render(
        request,
        "backups/backups.html",
        files=files,
        folder=bot.config.dataDir / "backups",
        databasePath=bot.db.path,
        schemaVersion=bot.db.version,
    )


@router.post("/backups/now", include_in_schema=False)
def backupNow(request: Request):
    try:
        runBackup(request.app.state.bot)
    except Exception as error:
        log.error(f"backup failed: {error}")
    return RedirectResponse("/backups", status_code=303)
