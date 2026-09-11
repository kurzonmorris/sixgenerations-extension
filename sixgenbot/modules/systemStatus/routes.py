from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ...core.webApp import render

router = APIRouter()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def status(request: Request):
    bot = request.app.state.bot
    working = [m for m in bot.modules if m.ok]
    broken = [m for m in bot.modules if not m.ok and m.problem != "switched off"]
    off = [m for m in bot.modules if m.problem == "switched off"]

    return render(
        request,
        "systemStatus/status.html",
        working=working,
        broken=broken,
        off=off,
        dataDir=bot.config.dataDir,
        events=bot.events.events,
        counts=bot.db.counts(),
        schemaVersion=bot.db.version,
        databasePath=bot.db.path,
        jobs=bot.scheduler.jobs,
    )
