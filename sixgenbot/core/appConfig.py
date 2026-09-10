"""Settings, read from one file you can open and edit.

Two files, deliberately separate:

    config.toml    everything ordinary — paths, port, what is switched on
    secrets.toml   tokens and keys, gitignored, never in an export or a log

Both live in the data directory so a backup of that directory is a backup of the
whole service. `config.example.toml` in the repo is the documented template.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULTS = {
    "web": {"host": "0.0.0.0", "port": 8770, "title": "Six Generations"},
    "paths": {"data": "/data"},
    "logging": {"level": "INFO", "keepLines": 2000},
    "modules": {"disabled": []},
}


def _merge(base: dict, overlay: dict) -> dict:
    out = {key: dict(value) if isinstance(value, dict) else value for key, value in base.items()}
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


@dataclass
class Config:
    settings: dict = field(default_factory=lambda: _merge(DEFAULTS, {}))
    secrets: dict = field(default_factory=dict)
    source: Path | None = None

    @property
    def dataDir(self) -> Path:
        return Path(self.settings["paths"]["data"])

    @property
    def port(self) -> int:
        return int(self.settings["web"]["port"])

    @property
    def host(self) -> str:
        return str(self.settings["web"]["host"])

    @property
    def title(self) -> str:
        return str(self.settings["web"]["title"])

    @property
    def disabledModules(self) -> list[str]:
        return list(self.settings["modules"]["disabled"])

    def secret(self, name: str, default: str = "") -> str:
        """Never log the result of this. Environment wins so Docker can inject."""
        return os.environ.get(f"SIXGENBOT_{name.upper()}") or self.secrets.get(name, default)


def _readToml(path: Path) -> dict:
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def loadConfig(dataDir: str | os.PathLike | None = None) -> Config:
    directory = Path(dataDir or os.environ.get("SIXGENBOT_DATA", DEFAULTS["paths"]["data"]))
    settings = _merge(DEFAULTS, _readToml(directory / "config.toml"))
    settings["paths"]["data"] = str(directory)
    return Config(
        settings=settings,
        secrets=_readToml(directory / "secrets.toml"),
        source=directory / "config.toml",
    )
