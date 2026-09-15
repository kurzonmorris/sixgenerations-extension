"""Changing a garment's details, with a record of what changed.

Every field that changes is written to `event` with its value before and after,
because a batch save touching forty items has to be explainable afterwards —
and undone from the same screen (D-198).

Two things are not columns and so are handled separately:

  * **Sizes** are `itemAttribute` rows, one per system. This is the field the
    whole backlog turns on — Vinted changed how sizes are displayed and the
    catalogue came down to be corrected by hand.
  * **Colours** are a list, first one primary.

Money arrives from the screen in pounds and is stored in pence, always.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from .database import reindexItem
from .readiness import factsFor, suggestedStatus

# Statuses this may recompute. An item that is on sale or sold is not moved by
# somebody tidying its description.
SETTLED = ("sold", "posted", "completed", "archived", "removed", "on_sale", "reserved")


@dataclass(frozen=True)
class Field:
    name: str
    label: str
    kind: str            # text | long | money | number | size | colours
    column: str = ""
    system: str = ""


FIELDS = [
    Field("title", "Title", "text", column="title"),
    Field("brand", "Brand", "text", column="brand"),
    Field("sizeUk", "Size UK", "size", system="UK"),
    Field("sizeEu", "Size EU", "size", system="EU"),
    Field("sizeUs", "Size US", "size", system="US"),
    Field("sizeLetter", "Size letter", "size", system="letter"),
    Field("colours", "Colour", "colours"),
    Field("price", "Price", "money", column="price"),
    Field("condition", "Condition", "text", column="conditionNote"),
    Field("weightGrams", "Weight in grams", "number", column="weightGrams"),
    Field("description", "Description", "long", column="description"),
    Field("notes", "Private notes", "long", column="notes"),
]

BY_NAME = {field.name: field for field in FIELDS}


def readMoney(text: str) -> int | None:
    """Pounds as typed to pence. "£12.50", "12.50" and "12" all work."""
    cleaned = str(text or "").strip().lstrip("£").replace(",", "")
    if not cleaned:
        return None
    return round(float(cleaned) * 100)


def showMoney(pence: int | None) -> str:
    return "" if pence is None else f"{pence / 100:.2f}"


def readColours(text: str) -> list[str]:
    parts = str(text or "").replace(",", ";").split(";")
    return [part.strip() for part in parts if part.strip()]


def currentValues(connection: sqlite3.Connection, itemId: str) -> dict[str, str]:
    """What the edit boxes start with, as strings ready for an input."""
    row = connection.execute("SELECT * FROM item WHERE itemId = ?", (itemId,)).fetchone()
    if row is None:
        return {}

    sizes = {
        attribute["system"]: attribute["value"]
        for attribute in connection.execute(
            "SELECT system, value FROM itemAttribute WHERE itemId = ? AND attribute = 'size'",
            (itemId,),
        )
    }
    colours = [
        attribute["value"]
        for attribute in connection.execute(
            "SELECT value FROM itemAttribute WHERE itemId = ? AND attribute = 'colour'"
            " ORDER BY isPrimary DESC, position",
            (itemId,),
        )
    ]

    values: dict[str, str] = {}
    for field in FIELDS:
        if field.kind == "size":
            values[field.name] = sizes.get(field.system, "")
        elif field.kind == "colours":
            values[field.name] = "; ".join(colours)
        elif field.kind == "money":
            values[field.name] = showMoney(row[field.column])
        elif field.kind == "number":
            values[field.name] = "" if row[field.column] is None else str(row[field.column])
        else:
            values[field.name] = row[field.column] or ""
    return values


def _record(connection, itemId, field, before, after, actor) -> None:
    connection.execute(
        "INSERT INTO event (happenedAt, actor, action, subject, field, valueBefore, valueAfter)"
        " VALUES (?, ?, 'edit', ?, ?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), actor, itemId, field, before, after),
    )


def _writeSize(connection, itemId: str, system: str, value: str) -> None:
    connection.execute(
        "DELETE FROM itemAttribute WHERE itemId = ? AND attribute = 'size' AND system = ?",
        (itemId, system),
    )
    if not value:
        return
    hasPrimary = connection.execute(
        "SELECT COUNT(*) AS total FROM itemAttribute"
        " WHERE itemId = ? AND attribute = 'size' AND isPrimary = 1",
        (itemId,),
    ).fetchone()["total"]
    connection.execute(
        "INSERT INTO itemAttribute (itemId, attribute, value, system, source, isPrimary)"
        " VALUES (?, 'size', ?, ?, 'manual', ?)",
        (itemId, value, system, 0 if hasPrimary else 1),
    )


def _writeColours(connection, itemId: str, colours: list[str]) -> None:
    connection.execute(
        "DELETE FROM itemAttribute WHERE itemId = ? AND attribute = 'colour'", (itemId,)
    )
    for position, colour in enumerate(colours):
        connection.execute(
            "INSERT INTO itemAttribute (itemId, attribute, value, source, isPrimary, position)"
            " VALUES (?, 'colour', ?, 'manual', ?, ?)",
            (itemId, colour, 1 if position == 0 else 0, position),
        )


def applyEdits(
    connection: sqlite3.Connection,
    itemId: str,
    changes: dict[str, str],
    actor: str = "user",
) -> list[tuple[str, str, str]]:
    """Writes the fields that actually differ. Returns (field, before, after)."""
    before = currentValues(connection, itemId)
    if not before:
        return []

    made: list[tuple[str, str, str]] = []
    for name, raw in changes.items():
        field = BY_NAME.get(name)
        if field is None:
            continue

        wanted = str(raw or "").strip()
        if field.kind == "money":
            wanted = showMoney(readMoney(wanted))
        elif field.kind == "colours":
            wanted = "; ".join(readColours(wanted))

        was = before[name]
        if wanted == was:
            continue

        if field.kind == "size":
            _writeSize(connection, itemId, field.system, wanted)
        elif field.kind == "colours":
            _writeColours(connection, itemId, readColours(wanted))
        elif field.kind == "money":
            connection.execute(
                f"UPDATE item SET {field.column} = ? WHERE itemId = ?",
                (readMoney(wanted), itemId),
            )
        elif field.kind == "number":
            connection.execute(
                f"UPDATE item SET {field.column} = ? WHERE itemId = ?",
                (int(wanted) if wanted else None, itemId),
            )
        else:
            connection.execute(
                f"UPDATE item SET {field.column} = ? WHERE itemId = ?", (wanted, itemId)
            )

        _record(connection, itemId, field.label, was, wanted, actor)
        made.append((field.label, was, wanted))

    if made:
        reindexItem(connection, itemId)
    return made


def markChecked(connection: sqlite3.Connection, itemId: str, actor: str = "user") -> bool:
    """A person has confirmed the details. Returns True if that was new.

    Confirming is also the moment the status is worked out again, because an
    item only leaves "needs information" once somebody has looked at it.
    """
    row = connection.execute(
        "SELECT status, verifiedAt FROM item WHERE itemId = ?", (itemId,)
    ).fetchone()
    if row is None or row["verifiedAt"]:
        return False

    now = datetime.now().isoformat(timespec="seconds")
    connection.execute("UPDATE item SET verifiedAt = ? WHERE itemId = ?", (now, itemId))
    _record(connection, itemId, "Checked", "", now, actor)

    if row["status"] not in SETTLED:
        wanted = suggestedStatus(factsFor(connection, itemId))
        if wanted != row["status"]:
            connection.execute("UPDATE item SET status = ? WHERE itemId = ?", (wanted, itemId))
            _record(connection, itemId, "Status", row["status"], wanted, actor)
    return True
