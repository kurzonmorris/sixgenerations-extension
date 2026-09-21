"""Reading the Vinted wardrobe into the database.

Vinted is the primary platform: garments are created there and mostly sell
there. So the database is only trustworthy if it knows what is actually on
Vinted right now — `docs/FEATURE_SPECIFICATION.md §4` puts this first, before
any writing, for exactly that reason.

The extension does the reading, in the signed-in browser session, because a
private Vinted account has no API and sits behind DataDome. This module is the
other end: it takes the read, says what it would change, and changes nothing
until somebody presses the button.

**A read is never applied by arriving.** `POST /vinted/read` only stores it and
works out a plan. Applying happens from this page. That keeps the dry-run rule
and means an unexpected POST cannot alter the catalogue.
"""

from pathlib import Path

from . import routes

NAME = "vintedSync"
VERSION = "v_0.1.0"


def register(bot):
    bot.templates(Path(__file__).parent / "templates")
    bot.addRoutes(routes.router)
    bot.addMenuItem("Vinted", "/vinted", group="SITES", order=10)
