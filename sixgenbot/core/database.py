"""SQLite: connecting to it, migrating it, and searching it.

Plain `sqlite3`, not an ORM. The reasons are in docs/SIXGENBOT_PLAN.md section 4:
the migrations are then the only description of the schema (nothing can drift
out of step with them), the SQL is readable by anyone, and full-text search —
the single most-used feature there will be — is native rather than fought with.

Money is integer pence everywhere. Dates are ISO-8601 text.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .appLogging import getLogger

log = getLogger("database")

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def connect(path: Path) -> sqlite3.Connection:
    """One connection, set up the way this database needs.

    WAL so a long read cannot block a write; foreign keys on so a broken
    reference fails loudly instead of rotting; NORMAL sync because WAL already
    survives a crash and FULL costs a lot for no gain here.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA synchronous = NORMAL")
    connection.execute("PRAGMA busy_timeout = 30000")
    return connection


# --- migrations -------------------------------------------------------------

@dataclass(frozen=True)
class Migration:
    number: int
    name: str
    path: Path


def _availableMigrations(folder: Path = MIGRATIONS) -> list[Migration]:
    found = []
    for file in sorted(folder.glob("*.sql")):
        match = re.match(r"^(\d{4})_([A-Za-z0-9_-]+)\.sql$", file.name)
        if not match:
            raise ValueError(f"migration {file.name} must be named 0001_someName.sql")
        found.append(Migration(int(match.group(1)), match.group(2), file))

    numbers = [m.number for m in found]
    if len(set(numbers)) != len(numbers):
        raise ValueError(f"two migrations share a number: {numbers}")
    return found


def appliedMigrations(connection: sqlite3.Connection) -> set[int]:
    connection.execute(
        "CREATE TABLE IF NOT EXISTS schemaVersion ("
        " number INTEGER PRIMARY KEY, name TEXT NOT NULL, appliedAt TEXT NOT NULL)"
    )
    return {row["number"] for row in connection.execute("SELECT number FROM schemaVersion")}


def migrate(connection: sqlite3.Connection, folder: Path = MIGRATIONS) -> list[Migration]:
    """Runs whatever has not run yet, in order, each in its own transaction.

    Safe to call on every start: already-applied migrations are skipped, so the
    container coming back up is never a risk.
    """
    done = appliedMigrations(connection)
    ran: list[Migration] = []

    for migration in _availableMigrations(folder):
        if migration.number in done:
            continue
        log.info(f"applying migration {migration.number:04d} {migration.name}")

        # BEGIN and COMMIT live inside the script on purpose. executescript()
        # commits whatever is open before it starts, so wrapping it in an
        # outer transaction does not work — the schema would be applied in
        # pieces and a failure halfway would leave a half-built database.
        # The filename pattern above restricts `name` to plain characters, so
        # inlining it here cannot carry anything but letters and digits.
        script = (
            "BEGIN;\n"
            + migration.path.read_text(encoding="utf-8")
            + f"\nINSERT INTO schemaVersion (number, name, appliedAt)"
            f" VALUES ({migration.number}, '{migration.name}', datetime('now'));\n"
            "COMMIT;\n"
        )
        try:
            connection.executescript(script)
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.OperationalError:
                pass  # the failure already closed the transaction
            log.error(f"migration {migration.number:04d} failed — nothing was changed")
            raise
        ran.append(migration)

    if ran:
        log.info(f"{len(ran)} migration(s) applied")
    return ran


def schemaVersion(connection: sqlite3.Connection) -> int:
    done = appliedMigrations(connection)
    return max(done) if done else 0


# --- search -----------------------------------------------------------------

def reindexItem(connection: sqlite3.Connection, itemId: str) -> None:
    """Rebuilds one item's searchable text.

    Everything a person might type goes in: the title and description, the
    brand, the SKU, private notes, every attribute value, and every category
    path. That is what makes "anything with velvet in it?" a single query.

    Explicit rather than a trigger, because the text is spread over three tables
    and a trigger on `item` alone would quietly go stale.
    """
    row = connection.execute(
        "SELECT sku, title, description, brand, conditionNote, notes FROM item WHERE itemId = ?",
        (itemId,),
    ).fetchone()
    if row is None:
        connection.execute("DELETE FROM itemSearch WHERE itemId = ?", (itemId,))
        return

    parts = [row["sku"], row["title"], row["description"], row["brand"],
             row["conditionNote"], row["notes"]]
    parts += [
        f"{a['attribute']} {a['system']} {a['value']}".strip()
        for a in connection.execute(
            "SELECT attribute, system, value FROM itemAttribute WHERE itemId = ?", (itemId,)
        )
    ]
    parts += [
        c["categoryPath"]
        for c in connection.execute(
            "SELECT categoryPath FROM itemCategory WHERE itemId = ?", (itemId,)
        )
    ]

    connection.execute("DELETE FROM itemSearch WHERE itemId = ?", (itemId,))
    connection.execute(
        "INSERT INTO itemSearch (itemId, body) VALUES (?, ?)",
        (itemId, " ".join(part for part in parts if part)),
    )


def searchItems(connection: sqlite3.Connection, text: str, limit: int = 100) -> list[str]:
    """Item ids matching free text, best match first. Empty text matches nothing."""
    cleaned = text.strip()
    if not cleaned:
        return []
    # Quote each word so punctuation a person typed cannot become FTS syntax.
    query = " ".join(f'"{word}"' for word in re.findall(r"\w+", cleaned))
    if not query:
        return []
    rows = connection.execute(
        "SELECT itemId FROM itemSearch WHERE itemSearch MATCH ? ORDER BY rank LIMIT ?",
        (query, limit),
    )
    return [row["itemId"] for row in rows]


# --- counts -----------------------------------------------------------------

def counts(connection: sqlite3.Connection) -> dict[str, int]:
    """What the status page and the dashboard show. Empty database, all zeros."""
    byStatus = {
        row["status"]: row["total"]
        for row in connection.execute("SELECT status, COUNT(*) AS total FROM item GROUP BY status")
    }
    total = sum(byStatus.values())
    orders = connection.execute("SELECT COUNT(*) AS total FROM salesOrder").fetchone()["total"]
    images = connection.execute("SELECT COUNT(*) AS total FROM itemImage").fetchone()["total"]
    return {
        "items": total,
        "onSale": byStatus.get("on_sale", 0),
        "needsInfo": byStatus.get("needs_info", 0),
        "sold": byStatus.get("sold", 0),
        "posted": byStatus.get("posted", 0),
        "archived": byStatus.get("archived", 0),
        "orders": orders,
        "images": images,
    }


# --- one database, many threads ---------------------------------------------

class Database:
    """Owns the file, and hands out one connection per thread.

    FastAPI runs synchronous endpoints in a thread pool, and a single sqlite3
    connection must not be shared across threads. One per thread, opened on
    first use, is the simple answer — SQLite handles the locking, and WAL means
    readers never block the writer.
    """

    def __init__(self, path: Path) -> None:
        import threading

        self.path = Path(path)
        self._local = threading.local()

    def connection(self) -> sqlite3.Connection:
        existing = getattr(self._local, "connection", None)
        if existing is None:
            existing = connect(self.path)
            self._local.connection = existing
        return existing

    def migrate(self) -> list[Migration]:
        return migrate(self.connection())

    @property
    def version(self) -> int:
        return schemaVersion(self.connection())

    def counts(self) -> dict[str, int]:
        return counts(self.connection())

    def close(self) -> None:
        existing = getattr(self._local, "connection", None)
        if existing is not None:
            existing.close()
            self._local.connection = None
