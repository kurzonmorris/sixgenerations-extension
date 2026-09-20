"""Putting an item's photographs in the order you want them shown.

**The order matters.** The first photograph is the one a buyer sees in a list on
every platform, so it decides whether they open the listing at all.

**Crosslist's order is not the seller's order.** The importer records it as
`orderSource = 'crosslist'` for exactly that reason — it is a guess. Moving a
photograph here marks it `'manual'`, which is the one order that should never be
overwritten by reading a platform later.

Positions are 1, 2, 3 with no gaps, and `UNIQUE (itemId, position)` holds. So a
move cannot swap two rows one at a time: the first write would collide with the
row it is swapping with. Every move renumbers the whole item in two passes.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime


def photosFor(connection: sqlite3.Connection, itemId: str) -> list[sqlite3.Row]:
    return list(connection.execute(
        "SELECT imageId, position, filePath, sourceUrl, role, orderSource, fetchError"
        " FROM itemImage WHERE itemId = ? ORDER BY position", (itemId,)
    ))


def _renumber(connection, itemId: str, order: list[int]) -> None:
    """Writes 1..N in the given order.

    Two passes. The first parks every row on a negative number so no write can
    land on a position another row still holds; the second writes the real ones.
    """
    for number, imageId in enumerate(order, start=1):
        connection.execute(
            "UPDATE itemImage SET position = ? WHERE imageId = ? AND itemId = ?",
            (-number, imageId, itemId),
        )
    for number, imageId in enumerate(order, start=1):
        connection.execute(
            "UPDATE itemImage SET position = ?, orderSource = 'manual'"
            " WHERE imageId = ? AND itemId = ?",
            (number, imageId, itemId),
        )


def _record(connection, itemId: str, before: list[int], after: list[int]) -> None:
    connection.execute(
        "INSERT INTO event (happenedAt, actor, action, subject, field, valueBefore, valueAfter)"
        " VALUES (?, 'user', 'edit', ?, 'Photograph order', ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), itemId,
         ",".join(str(i) for i in before), ",".join(str(i) for i in after)),
    )


def move(connection: sqlite3.Connection, itemId: str, imageId: int, where: str) -> bool:
    """`where` is up, down or first. True if anything actually moved."""
    order = [row["imageId"] for row in photosFor(connection, itemId)]
    if imageId not in order:
        return False

    at = order.index(imageId)
    wanted = list(order)
    if where == "up" and at > 0:
        wanted[at - 1], wanted[at] = wanted[at], wanted[at - 1]
    elif where == "down" and at < len(wanted) - 1:
        wanted[at + 1], wanted[at] = wanted[at], wanted[at + 1]
    elif where == "first" and at > 0:
        wanted.insert(0, wanted.pop(at))

    if wanted == order:
        return False

    connection.execute("BEGIN IMMEDIATE")
    try:
        _renumber(connection, itemId, wanted)
        _record(connection, itemId, order, wanted)
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    return True
