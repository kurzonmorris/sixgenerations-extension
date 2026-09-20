"""Putting one garment back on Vinted, with everything already laid out.

The 972 withdrawn items are the point of this project. Everything built so far
finds them and corrects them. This is the step that puts one back up.

Nothing here talks to Vinted. It is a copying screen, not a robot: the listing
form is filled in by hand, and this makes every answer a copy rather than a
search. The Vinted write path replaces the copying later and will reuse the same
`core/listingSheet.py`.
"""

from pathlib import Path

from . import routes

NAME = "listingHelper"
VERSION = "v_0.1.0"


def register(bot):
    bot.templates(Path(__file__).parent / "templates")
    bot.addRoutes(routes.router)
    bot.addMenuItem("Ready to list", "/list", group="TODAY", order=20)
