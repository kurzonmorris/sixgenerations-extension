"""The Table — every item, one search box, and a page at a time.

The screen that answers "do you have anything with velvet in it?" while the
customer is still standing there. `docs/INTERFACE_LAYOUT.md` calls it the
most-used screen in the system.

It shows and it finds. To change an item, tick it and use "To review" — the
batch edit screen already does that job, and doing it twice would mean two
places to keep right.
"""

from pathlib import Path

from . import routes

NAME = "itemTable"
VERSION = "v_0.1.0"


def register(bot):
    bot.templates(Path(__file__).parent / "templates")
    bot.addRoutes(routes.router)
    bot.addMenuItem("The Table", "/table", group="ITEMS", order=10)
    # The two halves of the catalogue, as plain menu entries. Both are this same
    # screen with one filter set — one list to learn, not two.
    bot.addMenuItem("On Vinted now", "/table?listed=yes", group="ITEMS", order=11)
    bot.addMenuItem("Still to go up", "/table?listed=no", group="ITEMS", order=12)
