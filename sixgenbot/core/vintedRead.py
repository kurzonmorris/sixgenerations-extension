"""Taking a read of the Vinted wardrobe and putting it into the database.

The extension reads Vinted in the signed-in browser session and hands the result
here. This file decides what that read *means*, and it is deliberately cautious.

**The rule that shapes everything: a read never overwrites a correction.**

The whole catalogue came offline because Vinted showed sizes wrongly. Those
sizes are still wrong on Vinted. A read that copied them back over the corrected
ones would undo the work the project exists to do. So:

  * Facts **about the listing** — its address, its price on Vinted, whether it
    is live or sold — are always written. They are Vinted's to state.
  * A field on the **garment** is filled in only when ours is empty.
  * A field that differs is **reported, never overwritten**. A person decides.

Matching is by the Vinted listing id first, then by the SKU in the description.
Never by title: two garments with the same title are common here, and a wrong
match is worse than no match.
"""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from .database import reindexItem
from .sku import formatSku, withSku

# What a read may fill in when ours is empty, mapped to the item column.
FILLABLE = {
    "brand": "brand",
    "title": "title",
    "description": "description",
    "condition": "conditionNote",
}


@dataclass
class Difference:
    itemId: str
    sku: str
    field: str
    ours: str
    theirs: str


@dataclass
class Plan:
    newItems: list[dict] = field(default_factory=list)
    linked: list[dict] = field(default_factory=list)       # matched, listing recorded
    alreadyLinked: list[dict] = field(default_factory=list)
    soldOnVinted: list[dict] = field(default_factory=list)
    goneFromVinted: list[dict] = field(default_factory=list)
    unmatchable: list[dict] = field(default_factory=list)   # no SKU, no known listing
    ambiguous: list[dict] = field(default_factory=list)     # the code is shared
    filledIn: list[Difference] = field(default_factory=list)
    differences: list[Difference] = field(default_factory=list)
    readAt: str = ""

    def asSentence(self) -> str:
        return (
            f"{len(self.newItems)} new, {len(self.linked)} matched for the first time, "
            f"{len(self.alreadyLinked)} already known, {len(self.soldOnVinted)} sold, "
            f"{len(self.goneFromVinted)} no longer on Vinted, "
            f"{len(self.unmatchable)} could not be matched, "
            f"{len(self.ambiguous)} share a code with another item"
        )


def _clean(value) -> str:
    return "" if value is None else str(value).strip()


def _pence(price) -> int | None:
    try:
        return round(float(price) * 100)
    except (TypeError, ValueError):
        return None


def itemsWithCode(connection, code: str) -> list[sqlite3.Row]:
    """Every garment holding that code, including the ones carrying a suffix.

    639 items share a code, and the importer marks the later one `11-1-26
    #f26f36`. Vinted only ever carries the plain code, so a read matching on
    `sku = ?` alone would miss all 324 suffixed ones and create them again as
    duplicates. Found 2026-09-21 against the real catalogue.
    """
    return list(connection.execute(
        "SELECT * FROM item WHERE sku = ? OR sku LIKE ? ORDER BY sku", (code, f"{code} #%")))


def _findItem(connection, read: dict) -> sqlite3.Row | str | None:
    """The Vinted listing id first, then the SKU. Never the title.

    Returns the row, or the string "ambiguous" when the code belongs to more
    than one garment and nothing else can tell them apart.
    """
    sourceId = _clean(read.get("sourceId"))
    if sourceId:
        row = connection.execute(
            "SELECT i.* FROM item i JOIN listing l ON l.itemId = i.itemId"
            " WHERE l.platform = 'vinted' AND l.externalId = ?", (sourceId,)
        ).fetchone()
        if row is not None:
            return row

    code = _clean(read.get("storageCode"))
    if not code:
        return None

    holders = itemsWithCode(connection, code)
    if len(holders) == 1:
        return holders[0]
    if len(holders) > 1:
        return "ambiguous"
    return None


def planRead(connection: sqlite3.Connection, items: list[dict]) -> Plan:
    """What this read would do. Writes nothing."""
    plan = Plan(readAt=datetime.now().isoformat(timespec="seconds"))
    seen: set[str] = set()

    for read in items:
        sourceId = _clean(read.get("sourceId"))
        code = _clean(read.get("storageCode"))
        sold = _clean(read.get("status")) == "sold"
        row = _findItem(connection, read)

        if row == "ambiguous":
            # Carry the garments that hold the code, so a person can pick one.
            # Typing the code cannot settle it — the code is the ambiguity.
            plan.ambiguous.append({**read, "candidates": [
                {"itemId": holder["itemId"],
                 "sku": formatSku(holder["sku"]) or holder["sku"],
                 "title": holder["title"]}
                for holder in itemsWithCode(connection, _clean(read.get("storageCode")))
            ]})
            continue

        if row is None:
            if code:
                plan.newItems.append(read)
            else:
                plan.unmatchable.append(read)
            continue

        seen.add(row["itemId"])
        listing = connection.execute(
            "SELECT * FROM listing WHERE itemId = ? AND platform = 'vinted'", (row["itemId"],)
        ).fetchone()

        where = plan.alreadyLinked if listing and listing["externalId"] == sourceId \
            else plan.linked
        where.append({**read, "itemId": row["itemId"], "sku": formatSku(row["sku"]) or row["sku"]})

        if sold and row["status"] not in ("sold", "posted", "completed"):
            plan.soldOnVinted.append(
                {**read, "itemId": row["itemId"], "sku": formatSku(row["sku"]) or row["sku"]})

        for name, column in FILLABLE.items():
            theirs = _clean(read.get(name))
            ours = _clean(row[column])
            if name == "description":
                # Vinted carries the SKU on the end and our copy may not, so a
                # plain comparison called every single listing different and
                # buried the real differences under a thousand false ones.
                # Compare what we *would* publish against what is published.
                ours = _clean(withSku(ours, row["sku"])) if ours else ours
            if not theirs or theirs == ours:
                continue
            difference = Difference(row["itemId"], formatSku(row["sku"]) or row["sku"],
                                    name, ours, theirs)
            (plan.filledIn if not ours else plan.differences).append(difference)

    # Anything we believe is live on Vinted that the read did not mention.
    for row in connection.execute(
        "SELECT i.itemId, i.sku, l.externalId, l.url FROM item i"
        " JOIN listing l ON l.itemId = i.itemId"
        " WHERE l.platform = 'vinted' AND l.state = 'live'"
    ):
        if row["itemId"] not in seen:
            plan.goneFromVinted.append({
                "itemId": row["itemId"],
                "sku": formatSku(row["sku"]) or row["sku"],
                "sourceId": row["externalId"],
                "url": row["url"],
            })

    return plan


def _writeListing(connection, itemId: str, read: dict, now: str) -> None:
    sold = _clean(read.get("status")) == "sold"
    connection.execute(
        "INSERT INTO listing (itemId, platform, externalId, url, state, price, listedAt,"
        " lastSyncedAt) VALUES (?, 'vinted', ?, ?, ?, ?, ?, ?)"
        " ON CONFLICT (itemId, platform) DO UPDATE SET"
        " externalId = excluded.externalId, url = excluded.url, state = excluded.state,"
        " price = excluded.price, lastSyncedAt = excluded.lastSyncedAt",
        (itemId, _clean(read.get("sourceId")), _clean(read.get("url")),
         "sold" if sold else "live", _pence(read.get("price")), now, now),
    )


def _record(connection, itemId: str, name: str, before: str, after: str, now: str) -> None:
    connection.execute(
        "INSERT INTO event (happenedAt, actor, action, subject, field, valueBefore, valueAfter)"
        " VALUES (?, 'vinted', 'read', ?, ?, ?, ?)", (now, itemId, name, before, after))


def applyRead(connection: sqlite3.Connection, items: list[dict],
              dryRun: bool = True) -> Plan:
    """Writes the plan. Dry run by default, as everything here is."""
    plan = planRead(connection, items)
    if dryRun:
        return plan

    now = plan.readAt
    connection.execute("BEGIN IMMEDIATE")
    try:
        for read in plan.newItems:
            itemId = str(uuid.uuid4())
            connection.execute(
                "INSERT INTO item (itemId, sku, status, title, description, brand,"
                " conditionNote, price, dateAdded, dateListed) VALUES (?, ?, 'on_sale', ?, ?, ?,"
                " ?, ?, ?, ?)",
                (itemId, _clean(read.get("storageCode")), _clean(read.get("title")),
                 _clean(read.get("description")), _clean(read.get("brand")),
                 _clean(read.get("condition")), _pence(read.get("price")), now, now))
            _writeListing(connection, itemId, read, now)
            _record(connection, itemId, "Found on Vinted", "", _clean(read.get("url")), now)
            reindexItem(connection, itemId)

        for read in plan.linked + plan.alreadyLinked:
            _writeListing(connection, read["itemId"], read, now)

        for read in plan.soldOnVinted:
            connection.execute(
                "UPDATE item SET status = 'sold', dateSold = ? WHERE itemId = ?",
                (now, read["itemId"]))
            _record(connection, read["itemId"], "Status", "on sale", "sold", now)

        for gone in plan.goneFromVinted:
            connection.execute(
                "UPDATE listing SET state = 'ended', endedAt = ?, lastSyncedAt = ?"
                " WHERE itemId = ? AND platform = 'vinted'", (now, now, gone["itemId"]))
            _record(connection, gone["itemId"], "Vinted listing", "live", "no longer there", now)

        # Only blanks. A field that differs is reported, never overwritten.
        for blank in plan.filledIn:
            connection.execute(
                f"UPDATE item SET {FILLABLE[blank.field]} = ? WHERE itemId = ?",
                (blank.theirs, blank.itemId))
            _record(connection, blank.itemId, blank.field, "", blank.theirs, now)
            reindexItem(connection, blank.itemId)

        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise

    return plan
