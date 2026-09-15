"""Getting files in and out without a terminal.

Sending a spreadsheet to the server previously meant a network share and a
`cp` with the right quoting. This is the same job with a button.
"""

from pathlib import Path

from . import routes

NAME = "fileTransfer"
VERSION = "v_0.1.0"


def register(bot):
    bot.templates(Path(__file__).parent / "templates")
    bot.addRoutes(routes.router)
    bot.addMenuItem("Files", "/files", group="SYSTEM", order=40)
