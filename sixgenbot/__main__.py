"""python -m sixgenbot serve | check | migrate | backup | restore | version

`serve` runs it. `check` loads everything and reports without opening a port,
which is what to run after changing a module. `backup` and `restore` are the
pair that matter: a backup nobody has put back is a hope, not a backup.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import VERSION
from .core.appConfig import loadConfig
from .core.appLogging import getLogger, setupLogging
from .core.backup import listBackups, makeBackup, restore
from .core.moduleLoader import loadModules
from .core.webApp import Bot


def buildBot(dataDir: str | None = None) -> Bot:
    config = loadConfig(dataDir)
    setupLogging(
        level=config.settings["logging"]["level"],
        logFile=config.dataDir / "logs" / "sixgenbot.log",
        keepLines=int(config.settings["logging"]["keepLines"]),
    )
    log = getLogger("start")
    log.info(f"sixgenbot {VERSION}")
    log.info(f"data directory: {config.dataDir}")

    bot = Bot(config)
    applied = bot.db.migrate()
    log.info(f"database schema v{bot.db.version} at {bot.db.path}"
             + (f" ({len(applied)} migration(s) just applied)" if applied else ""))
    bot.modules = loadModules(bot, disabled=config.disabledModules)
    return bot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sixgenbot")
    parser.add_argument(
        "command",
        choices=["serve", "check", "migrate", "backup", "restore", "version"],
        nargs="?",
        default="serve",
    )
    parser.add_argument("--data", help="data directory (default: $SIXGENBOT_DATA or /data)")
    parser.add_argument("--file", help="restore: which backup to put back (default: the newest)")
    args = parser.parse_args(argv)

    if args.command == "version":
        print(VERSION)
        return 0

    bot = buildBot(args.data)
    failed = [m for m in bot.modules if not m.ok and m.problem != "switched off"]

    if args.command == "migrate":
        print(f"database schema is v{bot.db.version}")
        return 0

    if args.command == "backup":
        made = makeBackup(bot.db.path, bot.config.dataDir)
        print(f"{made.path}  ({made.bytes:,} bytes)")
        return 0

    if args.command == "restore":
        if args.file:
            chosen = Path(args.file)
        else:
            available = listBackups(bot.config.dataDir)
            if not available:
                print("no backups found")
                return 1
            chosen = available[0].path
        bot.db.close()
        counts = restore(chosen, bot.db.path)
        print(f"restored {chosen.name}: {counts['items']} items, {counts['orders']} orders")
        return 0

    if args.command == "check":
        for entry in bot.modules:
            state = "ok" if entry.ok else entry.problem
            print(f"  {entry.folder:<20} {entry.version or '-':<10} {state}")
        print(f"\n{sum(1 for m in bot.modules if m.ok)} of {len(bot.modules)} modules loaded")

        counts = bot.db.counts()
        print(f"database schema v{bot.db.version}: {counts['items']} items, {counts['orders']} orders")
        backups = listBackups(bot.config.dataDir)
        print(f"backups: {len(backups)}" + (f", newest {backups[0].name}" if backups else " — none yet"))
        return 1 if failed else 0

    import uvicorn

    uvicorn.run(
        bot.buildApp(startScheduler=True),
        host=bot.config.host,
        port=bot.config.port,
        log_config=None,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
