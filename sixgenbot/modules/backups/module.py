"""Nightly backup, and a page that says whether it worked.

The offsite half is deliberately not in here: the nightly file lands in
<data>/backups/ and pCloud Drive or rclone copies that one folder. sixgenbot
never holds a pCloud password, which is one fewer secret to lose.
"""

from pathlib import Path

from . import routes

NAME = "backups"
VERSION = "v_0.1.0"


def register(bot):
    bot.templates(Path(__file__).parent / "templates")
    bot.addRoutes(routes.router)
    bot.addMenuItem("Backups", "/backups", group="SYSTEM", order=80)
    bot.addJob("nightlyBackup", "30 2 * * *", lambda: routes.runBackup(bot))
