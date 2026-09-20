"""Everything needed to put one garment on Vinted, on one screen.

**This is the step nothing helped with.** Items could be found, chosen and
corrected, and then putting one back on Vinted meant hunting through the
catalogue for its details and its photographs. That is the 3-to-6-items-a-day
limit, and 972 withdrawn items are waiting behind it.

Nothing here talks to Vinted. It lays the answers out, in the order the listing
form asks for them, so each one is a copy rather than a search. The Vinted write
path comes later and will reuse the same pieces.

**The SKU is put back on the end of the description here**, by `sku.withSku()`.
It is how the garment is recognised next time, on every platform, and a
description retyped without it is a garment the system loses.
"""

from __future__ import annotations

import io
import sqlite3
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from .itemEdit import showMoney
from .readiness import factsFor, missingFor, recommendedFor
from .sku import describeSku, formatSku, withSku


@dataclass
class Sheet:
    itemId: str = ""
    sku: str = ""
    whereItIs: str = ""
    title: str = ""
    description: str = ""          # the SKU already on the end
    brand: str = ""
    condition: str = ""
    price: str = ""
    weightGrams: str = ""
    sizes: list[tuple[str, str]] = field(default_factory=list)
    colours: list[str] = field(default_factory=list)
    materials: list[str] = field(default_factory=list)
    category: str = ""
    photos: list[int] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    worthAdding: list[str] = field(default_factory=list)
    listedOn: str = ""


def sheetFor(connection: sqlite3.Connection, itemId: str) -> Sheet | None:
    row = connection.execute("SELECT * FROM item WHERE itemId = ?", (itemId,)).fetchone()
    if row is None:
        return None

    attributes = list(connection.execute(
        "SELECT attribute, value, system, isPrimary FROM itemAttribute"
        " WHERE itemId = ? ORDER BY isPrimary DESC, position", (itemId,)))
    category = connection.execute(
        "SELECT categoryPath FROM itemCategory WHERE itemId = ?"
        " ORDER BY isPrimary DESC LIMIT 1", (itemId,)).fetchone()
    facts = factsFor(connection, itemId)

    return Sheet(
        itemId=itemId,
        sku=formatSku(row["sku"]) or row["sku"],
        whereItIs=describeSku(row["sku"]),
        title=row["title"],
        description=withSku(row["description"], row["sku"]),
        brand=row["brand"],
        condition=row["conditionNote"],
        price=showMoney(row["price"]),
        weightGrams="" if row["weightGrams"] is None else str(row["weightGrams"]),
        sizes=[(a["system"], a["value"]) for a in attributes if a["attribute"] == "size"],
        colours=[a["value"] for a in attributes if a["attribute"] == "colour"],
        materials=[a["value"] for a in attributes if a["attribute"] == "material"],
        category=category["categoryPath"] if category else "",
        photos=[image["imageId"] for image in connection.execute(
            "SELECT imageId FROM itemImage WHERE itemId = ? AND filePath != ''"
            " ORDER BY position", (itemId,))],
        missing=missingFor(facts),
        worthAdding=recommendedFor(facts),
        listedOn=row["dateListed"] or "",
    )


def photoZip(connection: sqlite3.Connection, itemId: str, sku: str) -> bytes:
    """Every photograph, numbered in the order they will be shown.

    The numbers are the point: a listing form uploads them in the order they are
    picked, and 01 before 02 is the only way to be sure that happens.
    """
    made = io.BytesIO()
    safeSku = "".join(c if c.isalnum() else "-" for c in (sku or itemId)).strip("-")
    with zipfile.ZipFile(made, "w", zipfile.ZIP_STORED) as bundle:
        for number, row in enumerate(connection.execute(
            "SELECT filePath FROM itemImage WHERE itemId = ? AND filePath != ''"
            " ORDER BY position", (itemId,)), start=1):
            path = Path(row["filePath"])
            if path.is_file():
                bundle.write(path, f"{safeSku}_{number:02d}{path.suffix}")
    return made.getvalue()


def waitingToList(connection: sqlite3.Connection, limit: int = 50) -> list[sqlite3.Row]:
    """Never listed, has photographs here, in the order the room is walked.

    Photographs are the bar: an item without them cannot be listed at all, and
    the Photos page is where that is fixed.
    """
    from .sku import SQL_ORDER

    return list(connection.execute(
        "SELECT * FROM item WHERE dateListed IS NULL"
        " AND status NOT IN ('sold','posted','completed','archived','removed')"
        " AND EXISTS (SELECT 1 FROM itemImage p WHERE p.itemId = item.itemId"
        "             AND p.filePath != '')"
        f" ORDER BY {SQL_ORDER} LIMIT ?", (limit,)))
