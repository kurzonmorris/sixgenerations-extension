"""Reading the Crosslist export into the database.

The file is analysed in full in `docs/CROSSLIST_EXPORT.md`. The things that
shape this code:

* **One row is one item.** Repeated titles are separate garments.
* **The weight and the SKU are in the description**, not in columns. `W65g` on
  97.4% of rows, `B8-3 36` on 80.9%. The `ShippingWeight` column holds defaults
  nobody set, so it is ignored.
* **`B` just means box.** It is kept on the raw code for continuity and ignored
  when matching.
* **Some items have no code at all** — jackets, toys and books that do not fit a
  box. That is a real state, not a mistake, so they import and are flagged.
* **A few codes are shared**, usually because an item was returned and relisted.
  Both rows import; neither is merged; the clash is recorded.
* **Nothing is imported as `on_sale`.** What is live is answered by reading
  Vinted, never by a CSV.

Run it twice and nothing doubles: `crosslistId` identifies the row.
"""

from __future__ import annotations

import csv
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .appLogging import getLogger
from .database import reindexItem
from .sku import parseSku

log = getLogger("import")

csv.field_size_limit(10_000_000)

# "W65g", "W 405 g", "W220g." — the weight, on its own line near the end.
WEIGHT = re.compile(r"\bW\s?(\d{1,5})\s?g\b", re.IGNORECASE)

# The raw code as written, kept verbatim: "B8-3 36", "C01", "B2-1", "B1-1 05A".
RAW_CODE = re.compile(r"^([A-Za-z]{0,3}\s?\d{1,3}(?:\s*-\s*\d{1,3})?(?:[-\s]\d{1,5}[A-Za-z]?)?)$")

CONDITIONS = {
    "New": "New with tags",
    "NewWithoutTags": "New without tags",
    "VeryGood": "Very good",
    "Good": "Good",
    "Satisfactory": "Satisfactory",
}


@dataclass
class ImportCounts:
    read: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    withoutCode: int = 0
    sharedCode: int = 0
    photosQueued: int = 0
    problems: list[str] = field(default_factory=list)

    def asSentence(self) -> str:
        return (
            f"{self.read} rows read — {self.created} new, {self.updated} updated, "
            f"{self.unchanged} unchanged. {self.withoutCode} have no SKU, "
            f"{self.sharedCode} share one. {self.photosQueued} photos to fetch."
        )


def lastLines(description: str, howMany: int = 4) -> list[str]:
    return [line.strip() for line in description.replace("\r", "").split("\n") if line.strip()][-howMany:]


def readWeight(description: str) -> int | None:
    """Grams, from the `W###g` line. The ShippingWeight column is not used."""
    found = WEIGHT.search(description or "")
    return int(found.group(1)) if found else None


def readRawCode(description: str) -> str:
    """The code exactly as written, `B` and all, or '' when there is none.

    Only the final line is considered, and only if it looks like a code rather
    than prose — a description ending "...size 10-12" must not become a location.
    """
    lines = lastLines(description or "", 2)
    if not lines:
        return ""
    tail = lines[-1].rstrip(".,;: ")
    if WEIGHT.fullmatch(tail) or len(tail) > 14:
        return ""
    return tail if RAW_CODE.match(tail) else ""


def price(text: str) -> int | None:
    """Pence. '12.00' becomes 1200."""
    try:
        return round(float(text) * 100)
    except (TypeError, ValueError):
        return None


def whenListed(row: dict) -> str | None:
    return row.get("LastListedOn") or None


def statusFor(row: dict) -> str:
    """Never `on_sale` — that is Vinted's to say, not a file's."""
    return "sold" if row.get("Sold") else "needs_info"


@dataclass
class PlannedItem:
    crosslistId: str
    sku: str
    legacyCode: str
    title: str
    description: str
    brand: str
    conditionNote: str
    price: int | None
    weightGrams: int | None
    status: str
    dateAdded: str
    dateListed: str | None
    dateSold: str | None
    categoryPath: str
    colours: list[str]
    size: str
    photos: list[str]
    note: str = ""


def planRow(row: dict) -> PlannedItem:
    description = row.get("Description", "")
    raw = readRawCode(description)
    return PlannedItem(
        crosslistId=row["Id"],
        sku=parseSku(description),
        legacyCode=raw,
        title=(row.get("Title") or "").strip(),
        description=description.strip(),
        brand=(row.get("Brand") or "").strip(),
        conditionNote=CONDITIONS.get(row.get("Condition", ""), (row.get("Condition") or "").strip()),
        price=price(row.get("Price", "")),
        weightGrams=readWeight(description),
        status=statusFor(row),
        dateAdded=(row.get("Created") or "").strip(),
        dateListed=whenListed(row),
        dateSold=row.get("Sold") or None,
        categoryPath=(row.get("CategoryLabel") or "").strip(),
        colours=[c for c in (row.get("Color"), row.get("Color2")) if c],
        size=(row.get("SizeLabel") or "").strip(),
        photos=[p for p in (row.get("Photos") or "").split("|") if p.strip()],
    )


def readExport(path: Path) -> list[PlannedItem]:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return [planRow(row) for row in csv.DictReader(handle)]


def _sharedCodes(planned: list[PlannedItem]) -> set[str]:
    seen: dict[str, int] = {}
    for item in planned:
        if item.sku:
            seen[item.sku] = seen.get(item.sku, 0) + 1
    return {sku for sku, count in seen.items() if count > 1}


def _recordEvent(connection, subject: str, action: str, detail: str = "") -> None:
    connection.execute(
        "INSERT INTO event (happenedAt, actor, action, subject, detail)"
        " VALUES (datetime('now'), 'import', ?, ?, ?)",
        (action, subject, detail),
    )


def importExport(connection: sqlite3.Connection, path: Path, dryRun: bool = True) -> ImportCounts:
    """Reads the file and, unless this is a dry run, writes it.

    Dry run is the default everywhere in this project, and an import touching
    2,125 items is exactly where that matters.
    """
    planned = readExport(path)
    clashes = _sharedCodes(planned)
    counts = ImportCounts(read=len(planned))

    for item in planned:
        if not item.sku:
            counts.withoutCode += 1
            item.note = "no SKU in the description"
        elif item.sku in clashes:
            counts.sharedCode += 1
            item.note = f"SKU {item.sku} is used by more than one item"

        counts.photosQueued += len(item.photos)

        existing = connection.execute(
            "SELECT itemId, title, price FROM item WHERE crosslistId = ?", (item.crosslistId,)
        ).fetchone()

        if dryRun:
            if existing is None:
                counts.created += 1
            elif existing["title"] != item.title or existing["price"] != item.price:
                counts.updated += 1
            else:
                counts.unchanged += 1
            continue

        if existing is None:
            counts.created += 1
            _writeNew(connection, item)
        else:
            changed = _writeUpdate(connection, existing["itemId"], item)
            counts.updated += 1 if changed else 0
            counts.unchanged += 0 if changed else 1

    if not dryRun:
        connection.commit() if connection.in_transaction else None

    log.info(("would import: " if dryRun else "imported: ") + counts.asSentence())
    return counts


def _uniqueSku(connection, wanted: str, crosslistId: str) -> str:
    """The SKU column is unique, but the data is not — a few codes are shared.

    A returned-and-relisted garment ends up twice in the export with the same
    code. Both rows are kept, so the second gets a suffix and the clash is
    written into `importNote` rather than silently resolved.
    """
    if not wanted:
        return f"(no code) {crosslistId[:8]}"
    taken = connection.execute("SELECT 1 FROM item WHERE sku = ?", (wanted,)).fetchone()
    return wanted if taken is None else f"{wanted} #{crosslistId[:6]}"


def _writeNew(connection, item: PlannedItem) -> str:
    itemId = str(uuid.uuid4())
    connection.execute(
        "INSERT INTO item (itemId, sku, crosslistId, legacyCode, status, title, description,"
        " brand, conditionNote, price, weightGrams, dateAdded, dateListed, dateSold, importNote)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            itemId,
            _uniqueSku(connection, item.sku, item.crosslistId),
            item.crosslistId,
            item.legacyCode,
            item.status,
            item.title,
            item.description,
            item.brand,
            item.conditionNote,
            item.price,
            item.weightGrams,
            item.dateAdded or None,
            item.dateListed,
            item.dateSold,
            item.note,
        ),
    )
    _writeChildren(connection, itemId, item)
    _recordEvent(connection, itemId, "imported", f"from Crosslist row {item.crosslistId}")
    reindexItem(connection, itemId)
    return itemId


def _writeUpdate(connection, itemId: str, item: PlannedItem) -> bool:
    before = connection.execute(
        "SELECT title, description, brand, price, status FROM item WHERE itemId = ?", (itemId,)
    ).fetchone()
    rowChanged = (
        before["title"] != item.title
        or before["description"] != item.description
        or before["brand"] != item.brand
        or before["price"] != item.price
    )

    if rowChanged:
        connection.execute(
            "UPDATE item SET title = ?, description = ?, brand = ?, conditionNote = ?,"
            " price = ?, weightGrams = ?, dateListed = ?, dateSold = ?, legacyCode = ?,"
            " importNote = ? WHERE itemId = ?",
            (
                item.title, item.description, item.brand, item.conditionNote, item.price,
                item.weightGrams, item.dateListed, item.dateSold, item.legacyCode,
                item.note, itemId,
            ),
        )

    # Always, even when the item row is identical. A later export very often
    # changes only a size or brings photographs the earlier one lacked — the
    # September export differs from May in nothing but its 9,098 photo URLs.
    childrenChanged = _refreshChildren(connection, itemId, item)
    if not rowChanged and not childrenChanged:
        return False
    _recordEvent(
        connection, itemId, "updated by import",
        f"title {before['title']!r} -> {item.title!r}" if before["title"] != item.title else "details changed",
    )
    reindexItem(connection, itemId)
    return True


def _refreshChildren(connection, itemId: str, item: PlannedItem) -> bool:
    """Brings sizes, colours, categories and photos back into step on a re-import.

    Two rules, because a later export must never destroy work already done:

    * **Only Crosslist's own rows are replaced.** An attribute or category added
      by hand carries a different `source` and is left alone.
    * **Photos are only ever added.** Never removed, never renumbered — the files
      may already be downloaded, and the order may have been corrected by hand or
      read back from Vinted, both of which beat the export.

    Without this, importing a corrected export would fix the title and silently
    leave the old size and the missing photographs in place.
    """
    wasThere = _crosslistChildren(connection, itemId)

    connection.execute(
        "DELETE FROM itemAttribute WHERE itemId = ? AND source = 'crosslist'", (itemId,)
    )
    connection.execute(
        "DELETE FROM itemCategory WHERE itemId = ? AND platform = 'crosslist'", (itemId,)
    )
    _writeAttributes(connection, itemId, item)
    changed = _crosslistChildren(connection, itemId) != wasThere

    have = {
        row["sourceUrl"]
        for row in connection.execute("SELECT sourceUrl FROM itemImage WHERE itemId = ?", (itemId,))
    }
    nextPosition = (
        connection.execute(
            "SELECT COALESCE(MAX(position), 0) AS highest FROM itemImage WHERE itemId = ?", (itemId,)
        ).fetchone()["highest"]
        + 1
    )
    for url in item.photos:
        if url.strip() in have:
            continue
        connection.execute(
            "INSERT INTO itemImage (itemId, position, role, filePath, sourceUrl, orderSource)"
            " VALUES (?, ?, 'photo', '', ?, 'crosslist')",
            (itemId, nextPosition, url.strip()),
        )
        nextPosition += 1
        changed = True

    return changed


def _crosslistChildren(connection, itemId: str) -> set:
    """What the import owns on this item, as a comparable set."""
    attributes = {
        (r["attribute"], r["value"], r["system"])
        for r in connection.execute(
            "SELECT attribute, value, system FROM itemAttribute"
            " WHERE itemId = ? AND source = 'crosslist'",
            (itemId,),
        )
    }
    categories = {
        ("category", r["categoryPath"], "")
        for r in connection.execute(
            "SELECT categoryPath FROM itemCategory WHERE itemId = ? AND platform = 'crosslist'",
            (itemId,),
        )
    }
    return attributes | categories


def _writeChildren(connection, itemId: str, item: PlannedItem) -> None:
    _writeAttributes(connection, itemId, item)
    for position, url in enumerate(item.photos, start=1):
        connection.execute(
            "INSERT INTO itemImage (itemId, position, role, filePath, sourceUrl, orderSource)"
            " VALUES (?, ?, 'photo', '', ?, 'crosslist')",
            (itemId, position, url.strip()),
        )


def _writeAttributes(connection, itemId: str, item: PlannedItem) -> None:
    if item.size:
        connection.execute(
            "INSERT INTO itemAttribute (itemId, attribute, value, system, source, isPrimary)"
            " VALUES (?, 'size', ?, '', 'crosslist', 1)",
            (itemId, item.size),
        )
    for position, colour in enumerate(item.colours):
        connection.execute(
            "INSERT INTO itemAttribute (itemId, attribute, value, source, isPrimary, position)"
            " VALUES (?, 'colour', ?, 'crosslist', ?, ?)",
            (itemId, colour, 1 if position == 0 else 0, position),
        )
    if item.categoryPath:
        connection.execute(
            "INSERT INTO itemCategory (itemId, platform, categoryPath, isPrimary)"
            " VALUES (?, 'crosslist', ?, 1)",
            (itemId, item.categoryPath),
        )
