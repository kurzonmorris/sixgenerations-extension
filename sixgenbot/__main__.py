"""python -m sixgenbot serve | check | version

`serve` runs it. `check` loads everything and reports without opening a port,
which is what to run after changing a module.
"""

from __future__ import annotations

import argparse
import sys

from . import VERSION
from .core.appConfig import loadConfig
from .core.appLogging import getLogger, setupLogging
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
    bot.modules = loadModules(bot, disabled=config.disabledModules)
    return bot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sixgenbot")
    parser.add_argument("command", choices=["serve", "check", "version"], nargs="?", default="serve")
    parser.add_argument("--data", help="data directory (default: $SIXGENBOT_DATA or /data)")
    args = parser.parse_args(argv)

    if args.command == "version":
        print(VERSION)
        return 0

    bot = buildBot(args.data)
    failed = [m for m in bot.modules if not m.ok and m.problem != "switched off"]

    if args.command == "check":
        for entry in bot.modules:
            state = "ok" if entry.ok else entry.problem
            print(f"  {entry.folder:<20} {entry.version or '-':<10} {state}")
        print(f"\n{sum(1 for m in bot.modules if m.ok)} of {len(bot.modules)} modules loaded")
        return 1 if failed else 0

    import uvicorn

    uvicorn.run(bot.buildApp(), host=bot.config.host, port=bot.config.port, log_config=None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
