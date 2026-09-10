"""Logging to the console, to a file, and to a ring buffer the UI can read.

The ring buffer is what the Console screen shows without anyone opening a
terminal. It is capped, so a long run cannot fill memory.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

_buffer: deque[Line] = deque(maxlen=2000)


@dataclass(frozen=True)
class Line:
    at: str
    level: str
    source: str
    message: str


class _BufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        _buffer.append(
            Line(
                at=datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
                level=record.levelname,
                source=record.name.replace("sixgenbot.", ""),
                message=record.getMessage(),
            )
        )


def setupLogging(level: str = "INFO", logFile: Path | None = None, keepLines: int = 2000) -> None:
    global _buffer
    _buffer = deque(_buffer, maxlen=keepLines)

    root = logging.getLogger("sixgenbot")
    root.setLevel(level.upper())
    root.handlers.clear()
    root.propagate = False

    plain = logging.Formatter("%(asctime)s  %(levelname)-7s %(name)s  %(message)s", "%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler()
    console.setFormatter(plain)
    root.addHandler(console)

    if logFile:
        logFile.parent.mkdir(parents=True, exist_ok=True)
        rotating = RotatingFileHandler(logFile, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
        rotating.setFormatter(plain)
        root.addHandler(rotating)

    root.addHandler(_BufferHandler())


def getLogger(name: str) -> logging.Logger:
    return logging.getLogger(f"sixgenbot.{name}")


def recentLines(limit: int = 200, levels: set[str] | None = None) -> list[Line]:
    lines = [line for line in _buffer if not levels or line.level in levels]
    return lines[-limit:]


def clearLines() -> None:
    _buffer.clear()
