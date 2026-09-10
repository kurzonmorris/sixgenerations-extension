"""The application, and the object modules register themselves against.

`Bot` is the whole contract. A module gets handed one and calls these:

    bot.addRoutes(router)                    its own pages
    bot.addMenuItem(label, path, group=...)  where it appears in the left menu
    bot.onEvent(name, handler)               what it reacts to
    bot.emit(name, **payload)                what it announces
    bot.templates(folder)                    its own templates

`addJob` and `addMigrations` arrive with the scheduler and the database in
stage 2 — they are not stubbed here, because a function that silently does
nothing is worse than one that does not exist yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from .. import VERSION
from .appConfig import Config
from .appLogging import getLogger
from .eventBus import EventBus

log = getLogger("web")

HERE = Path(__file__).resolve().parent.parent

# The order the left menu is drawn in. A module names its group; unknown groups
# are appended, so a new one does not need core to change.
MENU_GROUPS = ["TODAY", "ITEMS", "MONEY", "SITES", "SYSTEM"]


@dataclass(frozen=True)
class MenuItem:
    label: str
    path: str
    group: str
    owner: str
    order: int = 100


class Bot:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.events = EventBus()
        self.menu: list[MenuItem] = []
        self.modules: list = []
        self.currentModule: str | None = None
        self._routers: list[APIRouter] = []
        self._templateDirs: list[Path] = [HERE / "templates"]

    # --- what a module calls -------------------------------------------------

    def addRoutes(self, router: APIRouter) -> None:
        self._routers.append(router)

    def addMenuItem(self, label: str, path: str, group: str = "SYSTEM", order: int = 100) -> None:
        self.menu.append(MenuItem(label, path, group.upper(), self.currentModule or "core", order))

    def onEvent(self, event: str, handler) -> None:
        self.events.subscribe(event, handler, owner=self.currentModule or "core")

    def emit(self, event: str, **payload) -> int:
        return self.events.emit(event, **payload)

    def templates(self, folder: Path | str) -> None:
        self._templateDirs.append(Path(folder))

    # --- what core does with it ---------------------------------------------

    def groupedMenu(self) -> list[tuple[str, list[MenuItem]]]:
        groups = {item.group for item in self.menu}
        ordered = [name for name in MENU_GROUPS if name in groups]
        ordered += sorted(groups - set(MENU_GROUPS))
        return [
            (name, sorted((i for i in self.menu if i.group == name), key=lambda i: (i.order, i.label)))
            for name in ordered
        ]

    def buildApp(self) -> FastAPI:
        app = FastAPI(title=self.config.title, version=VERSION, docs_url=None, redoc_url=None)

        jinja = Jinja2Templates(directory=str(HERE / "templates"))
        jinja.env.loader = ChoiceLoader([FileSystemLoader(str(d)) for d in self._templateDirs])
        jinja.env.globals.update(
            siteTitle=self.config.title,
            version=VERSION,
            menu=self.groupedMenu,
        )
        app.state.bot = self
        app.state.templates = jinja

        app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
        for router in self._routers:
            app.include_router(router)

        @app.get("/health", response_class=HTMLResponse, include_in_schema=False)
        def health() -> HTMLResponse:
            broken = [m.name for m in self.modules if not m.ok and m.problem != "switched off"]
            body = "ok" if not broken else f"modules failed: {', '.join(broken)}"
            return HTMLResponse(body, status_code=200 if not broken else 503)

        log.info(f"{len(self._routers)} routers, {len(self.menu)} menu items")
        return app


def render(request, name: str, **context) -> HTMLResponse:
    """One way to draw a page, so every module's pages come out the same."""
    templates = request.app.state.templates
    return templates.TemplateResponse(request=request, name=name, context=context)
