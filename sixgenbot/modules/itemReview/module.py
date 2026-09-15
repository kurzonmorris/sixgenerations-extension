"""The screen the backlog is cleared on.

Almost the whole catalogue came offline when Vinted changed how sizes are
displayed, and it is still down: 988 items photographed, described, priced and
earning nothing. Correcting them one page at a time is the work. This screen is
that work — pick a batch, show only the fields that need attention, fix them,
save the lot.

Judged the way `CLAUDE.md` says to judge a feature: does it put more items up in
a day. This is the one that does.
"""

from pathlib import Path

from . import routes

NAME = "itemReview"
VERSION = "v_0.1.0"


def register(bot):
    bot.templates(Path(__file__).parent / "templates")
    bot.addRoutes(routes.router)
    bot.addMenuItem("To review", "/review", group="TODAY", order=10)
