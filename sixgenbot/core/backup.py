"""Backups, and the restore that proves they were worth taking.

A backup nobody has restored is a hope, not a backup — so `restore` is a first
class command and a test does a full round trip on every run.

The database is copied with SQLite's own online backup, not by copying the file:
copying a file mid-write produces something that looks fine and is not.

**Offsite:** the nightly file lands in `<data>/backups/`. Point pCloud Drive (or
rclone) at that one folder and the offsite copy happens without sixgenbot ever
holding a pCloud password. That is deliberate — see docs/SIXGENBOT_PLAN.md.
"""

from __future__ import annotations

import gzip
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .appLogging import getLogger
from .database import connect

log = getLogger("backup")


@dataclass(frozen=True)
class BackupFile:
    path: Path
    takenAt: datetime
    bytes: int

    @property
    def name(self) -> str:
        return self.path.name


def backupFolder(dataDir: Path) -> Path:
    folder = dataDir / "backups"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def makeBackup(databasePath: Path, dataDir: Path, keep: int = 14) -> BackupFile:
    """One compressed copy of the database, timestamped. Old ones pruned."""
    folder = backupFolder(dataDir)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    target = folder / f"sixgenbot_{stamp}.sqlite.gz"

    # Seconds are in the name because the button can be pressed twice, and a
    # backup that silently overwrites another one is worse than no button.
    attempt = 1
    while target.exists():
        attempt += 1
        target = folder / f"sixgenbot_{stamp}-{attempt}.sqlite.gz"

    scratch = folder / f".{target.name}.tmp"
    source = connect(databasePath)
    copy = sqlite3.connect(scratch)
    try:
        source.backup(copy)          # SQLite's own consistent online backup
        copy.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        copy.close()
        source.close()

    with scratch.open("rb") as raw, gzip.open(target, "wb") as squashed:
        shutil.copyfileobj(raw, squashed)
    scratch.unlink()

    verifyBackup(target)
    pruneBackups(dataDir, keep)

    made = BackupFile(target, datetime.now(), target.stat().st_size)
    log.info(f"backup taken: {made.name} ({made.bytes:,} bytes)")
    return made


def verifyBackup(path: Path) -> dict[str, int]:
    """Opens the backup and asks SQLite whether it is sound. Throws if not."""
    scratch = path.with_suffix(".verify")
    try:
        with gzip.open(path, "rb") as squashed, scratch.open("wb") as raw:
            shutil.copyfileobj(squashed, raw)

        connection = sqlite3.connect(scratch)
        try:
            result = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise ValueError(f"backup {path.name} is damaged: {result}")
            items = connection.execute("SELECT COUNT(*) FROM item").fetchone()[0]
            orders = connection.execute("SELECT COUNT(*) FROM salesOrder").fetchone()[0]
        finally:
            connection.close()
    finally:
        scratch.unlink(missing_ok=True)

    return {"items": items, "orders": orders}


def listBackups(dataDir: Path) -> list[BackupFile]:
    folder = backupFolder(dataDir)
    files = [
        BackupFile(path, datetime.fromtimestamp(path.stat().st_mtime), path.stat().st_size)
        for path in folder.glob("sixgenbot_*.sqlite.gz")
    ]
    return sorted(files, key=lambda f: f.takenAt, reverse=True)


def pruneBackups(dataDir: Path, keep: int = 14) -> list[Path]:
    removed = []
    for old in listBackups(dataDir)[keep:]:
        old.path.unlink()
        removed.append(old.path)
        log.info(f"pruned old backup {old.name}")
    return removed


def restore(backupPath: Path, databasePath: Path) -> dict[str, int]:
    """Puts a backup back.

    The database being replaced is kept beside it as `.beforeRestore` — a
    restore is the moment you least want a one-way door.
    """
    counts = verifyBackup(backupPath)

    if databasePath.exists():
        keepSafe = databasePath.with_suffix(databasePath.suffix + ".beforeRestore")
        shutil.copy2(databasePath, keepSafe)
        log.info(f"the database being replaced was kept as {keepSafe.name}")

    for leftover in (databasePath.with_suffix(databasePath.suffix + "-wal"),
                     databasePath.with_suffix(databasePath.suffix + "-shm")):
        leftover.unlink(missing_ok=True)

    databasePath.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(backupPath, "rb") as squashed, databasePath.open("wb") as raw:
        shutil.copyfileobj(squashed, raw)

    log.info(f"restored {backupPath.name}: {counts['items']} items, {counts['orders']} orders")
    return counts
