"""Says whether sixgenbot is alive and what loaded. The home page until the
dashboard replaces it in stage 4."""

from pathlib import Path

from . import routes

NAME = "systemStatus"
VERSION = "v_0.1.0"


def register(bot):
    bot.templates(Path(__file__).parent / "templates")
    bot.addRoutes(routes.router)
    bot.addMenuItem("Status", "/", group="SYSTEM", order=10)
