"""Finds modules, checks them, and registers them.

A module is any folder under `sixgenbot/modules/` containing a `module.py` that
declares NAME and VERSION and defines `register(bot)`.

Nothing here names a module. Adding a feature means adding a folder — core does
not change. A module that fails to load is reported and skipped: the rest of the
service still starts, which is the whole point of the arrangement.
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path

from .appLogging import getLogger

log = getLogger("modules")

MODULES_PACKAGE = "sixgenbot.modules"


@dataclass
class LoadedModule:
    name: str
    version: str
    folder: str
    ok: bool
    problem: str = ""


def _findFolders(packageName: str) -> list[str]:
    package = importlib.import_module(packageName)
    root = Path(package.__file__).parent
    return sorted(
        item.name
        for item in pkgutil.iter_modules([str(root)])
        if item.ispkg and (root / item.name / "module.py").is_file()
    )


def loadModules(bot, disabled: list[str] | None = None, package: str = MODULES_PACKAGE) -> list[LoadedModule]:
    """`package` exists so the failure path can be tested against a fixture —
    the claim that one broken module cannot stop the others is the point of the
    whole arrangement, so it is worth proving rather than trusting."""
    skip = set(disabled or [])
    loaded: list[LoadedModule] = []

    for folder in _findFolders(package):
        if folder in skip:
            log.info(f"{folder} is switched off in the settings")
            loaded.append(LoadedModule(folder, "", folder, ok=False, problem="switched off"))
            continue

        try:
            module = importlib.import_module(f"{package}.{folder}.module")
            name = getattr(module, "NAME", "")
            version = getattr(module, "VERSION", "")
            register = getattr(module, "register", None)

            if not name or not version or not callable(register):
                raise AttributeError("module.py must declare NAME, VERSION and register(bot)")

            bot.currentModule = name
            register(bot)
            bot.currentModule = None

            loaded.append(LoadedModule(name, version, folder, ok=True))
            log.info(f"loaded {name} {version}")
        except Exception as error:
            bot.currentModule = None
            loaded.append(LoadedModule(folder, "", folder, ok=False, problem=str(error)))
            log.error(f"could not load {folder}: {error}")

    working = sum(1 for entry in loaded if entry.ok)
    log.info(f"{working} of {len(loaded)} modules loaded")
    return loaded
