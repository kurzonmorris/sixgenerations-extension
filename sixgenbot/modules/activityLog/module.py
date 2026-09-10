"""Shows the recent log without anyone opening a terminal.

Frozen by design: it draws what was there when the page loaded and does not
update itself. Refreshing is a deliberate act — see docs/INTERFACE_LAYOUT.md
section 7.
"""

from pathlib import Path

from . import routes

NAME = "activityLog"
VERSION = "v_0.1.0"


def register(bot):
    bot.templates(Path(__file__).parent / "templates")
    bot.addRoutes(routes.router)
    bot.addMenuItem("Console", "/console", group="SYSTEM", order=90)
