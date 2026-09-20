"""The photographs, and the clock they are on.

All 9,098 are hosted on `media-na.crosslist.com` — the subscription being
cancelled, not a marketplace. When it ends those URLs very likely stop
resolving, and for the items never listed anywhere it is the only copy.

Fetching them was a terminal command that blocked for an hour and told you
nothing until it finished. This is the same job with a button, a count you can
come back to, and the failures named.
"""

from pathlib import Path

from . import routes

NAME = "photoLibrary"
VERSION = "v_0.1.0"


def register(bot):
    bot.templates(Path(__file__).parent / "templates")
    bot.addRoutes(routes.router)
    bot.addMenuItem("Photos", "/photos", group="ITEMS", order=20)
