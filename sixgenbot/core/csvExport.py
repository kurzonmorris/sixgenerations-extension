"""Writing the inventory back out as a spreadsheet.

The flattening rules are `docs/DATA_MODEL.md §5`, and they matter: a spreadsheet
has one box per cell, so anything an item can have several of has to come out
predictably or it cannot be read back in.

  * Known size systems get their own column — `sizeUk`, `sizeEu`, `sizeUs`,
    `sizeLetter` — and anything else lands in `sizeOther`.
  * Lists are separated by `;`  →  `colours = Navy;White`
  * Key/value lists use `key=value;`  →  `measurements = chest=46cm;length=98cm`
  * **Never a comma inside a value.** Quoting survives it; the first person to
    open the file in something careless does not.

Opens cleanly in LibreOffice Calc, which is what this business uses.
"""

from __future__ import annotations

import csv
import io
import re
import sqlite3

COLUMNS = [
    "sku", "legacyCode", "title", "description", "brand", "condition",
    "sizeUk", "sizeEu", "sizeUs", "sizeLetter", "sizeOther",
    "measurements", "colourMain", "colours", "materials",
    "price", "cost", "weightGrams",
    "status", "verified", "dateAdded", "dateListed", "dateSold",
    "categories", "photoCount", "photosOnDisk", "importNote", "notes", "itemId",
]

SIZE_COLUMNS = {"UK": "sizeUk", "EU": "sizeEu", "US": "sizeUs", "letter": "sizeLetter"}


def _joined(values) -> str:
    """Semicolons, and never a comma — see the note at the top.

    A comma inside a value becomes a space, and runs of whitespace collapse, so
    "Navy, dark" comes out as "Navy dark" rather than with a gap in it.
    """
    cleaned = (re.sub(r"\s+", " ", str(v).replace(",", " ")).strip() for v in values)
    return ";".join(value for value in cleaned if value)


def _attributes(connection: sqlite3.Connection) -> dict[str, list[sqlite3.Row]]:
    grouped: dict[str, list[sqlite3.Row]] = {}
    for row in connection.execute(
        "SELECT itemId, attribute, value, system, isPrimary, position FROM itemAttribute"
        " ORDER BY itemId, attribute, position"
    ):
        grouped.setdefault(row["itemId"], []).append(row)
    return grouped


def _categories(connection: sqlite3.Connection) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for row in connection.execute("SELECT itemId, categoryPath FROM itemCategory"):
        grouped.setdefault(row["itemId"], []).append(row["categoryPath"])
    return grouped


def _photos(connection: sqlite3.Connection) -> dict[str, tuple[int, int]]:
    return {
        row["itemId"]: (row["total"], row["onDisk"])
        for row in connection.execute(
            "SELECT itemId, COUNT(*) AS total,"
            " SUM(CASE WHEN filePath != '' THEN 1 ELSE 0 END) AS onDisk"
            " FROM itemImage GROUP BY itemId"
        )
    }


def exportItems(connection: sqlite3.Connection, status: str = "") -> str:
    """Every item, or just those with one status, as CSV text."""
    attributes = _attributes(connection)
    categories = _categories(connection)
    photos = _photos(connection)

    sql = "SELECT * FROM item"
    parameters: tuple = ()
    if status:
        sql += " WHERE status = ?"
        parameters = (status,)
    sql += " ORDER BY sku"

    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()

    for item in connection.execute(sql, parameters):
        mine = attributes.get(item["itemId"], [])
        sizes = [a for a in mine if a["attribute"] == "size"]
        colours = [a for a in mine if a["attribute"] == "colour"]
        totalPhotos, onDisk = photos.get(item["itemId"], (0, 0))

        row = {
            "sku": item["sku"],
            "legacyCode": item["legacyCode"],
            "title": item["title"],
            "description": item["description"],
            "brand": item["brand"],
            "condition": item["conditionNote"],
            "sizeOther": _joined(s["value"] for s in sizes if s["system"] not in SIZE_COLUMNS),
            "measurements": _joined(
                f"{a['value']}={a['numericValue'] or ''}{a['system']}"
                for a in mine if a["attribute"] == "measurement"
            ),
            "colourMain": next((c["value"] for c in colours if c["isPrimary"]), ""),
            "colours": _joined(c["value"] for c in colours),
            "materials": _joined(a["value"] for a in mine if a["attribute"] == "material"),
            "price": "" if item["price"] is None else f"{item['price'] / 100:.2f}",
            "cost": "" if item["cost"] is None else f"{item['cost'] / 100:.2f}",
            "weightGrams": item["weightGrams"] or "",
            "status": item["status"],
            "verified": item["verifiedAt"] or "",
            "dateAdded": item["dateAdded"] or "",
            "dateListed": item["dateListed"] or "",
            "dateSold": item["dateSold"] or "",
            "categories": _joined(categories.get(item["itemId"], [])),
            "photoCount": totalPhotos,
            "photosOnDisk": onDisk or 0,
            "importNote": item["importNote"],
            "notes": item["notes"],
            "itemId": item["itemId"],
        }
        for size in sizes:
            column = SIZE_COLUMNS.get(size["system"])
            if column:
                row[column] = size["value"]

        writer.writerow(row)

    return out.getvalue()
