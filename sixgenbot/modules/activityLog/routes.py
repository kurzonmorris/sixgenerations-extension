from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ...core.appLogging import recentLines
from ...core.webApp import render

router = APIRouter()

PROBLEMS = {"WARNING", "ERROR", "CRITICAL"}


@router.get("/console", response_class=HTMLResponse, include_in_schema=False)
def console(request: Request, only: str = ""):
    problemsOnly = only == "problems"
    lines = recentLines(limit=300, levels=PROBLEMS if problemsOnly else None)
    return render(request, "activityLog/log.html", lines=reversed(lines), problemsOnly=problemsOnly)
