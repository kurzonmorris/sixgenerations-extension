"""What is still missing before a garment can go on a platform.

This is what splits the two lists. An item that came off a live listing already
has everything; an item that has never been online usually does not, and
somebody has to go through it. Both live in the same table — the difference is
what this module says about them.

Two different things are being asked, and they are not the same:

  * **missing** — a field has no value at all.
  * **unchecked** — the fields have values, but no person has confirmed them.
    An item imported from a spreadsheet is unchecked even when it looks complete.

`item.verifiedAt` records the second. Null means nobody has looked.

⚠ The Vinted list below is written from the listing form as understood today and
is **not yet confirmed against the live site** — that is Task 1 in
`docs/CLAUDE_BROWSER_TASKS.md`. eBay's and Shopify's lists are deliberately
absent rather than guessed: eBay's required item specifics vary by category and
nothing is known yet (Q16).
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Plain words, because these end up on screen. "a size", not "size_uk missing".
REQUIRED = {
    "internal": ["a SKU", "a title", "a price"],
    "vinted": [
        "at least one photo",
        "a title",
        "a description",
        "a category",
        "a brand",
        "a size",
        "a condition",
        "a price",
    ],
}

RECOMMENDED = {
    "internal": [],
    "vinted": ["a colour", "measurements"],
}


@dataclass
class ItemFacts:
    """Everything needed to judge an item, gathered once so this stays pure."""

    sku: str = ""
    title: str = ""
    description: str = ""
    brand: str = ""
    conditionNote: str = ""
    price: int | None = None
    imageCount: int = 0
    verifiedAt: str | None = None
    attributes: set[str] = field(default_factory=set)   # "size", "colour", "measurement"
    categories: set[str] = field(default_factory=set)   # platform names


def factsFor(connection, itemId: str) -> ItemFacts:
    """Reads one item and everything hanging off it."""
    row = connection.execute(
        "SELECT sku, title, description, brand, conditionNote, price, verifiedAt"
        " FROM item WHERE itemId = ?",
        (itemId,),
    ).fetchone()
    if row is None:
        return ItemFacts()

    return ItemFacts(
        sku=row["sku"],
        title=row["title"],
        description=row["description"],
        brand=row["brand"],
        conditionNote=row["conditionNote"],
        price=row["price"],
        verifiedAt=row["verifiedAt"],
        imageCount=connection.execute(
            "SELECT COUNT(*) AS total FROM itemImage WHERE itemId = ?", (itemId,)
        ).fetchone()["total"],
        attributes={
            r["attribute"]
            for r in connection.execute(
                "SELECT DISTINCT attribute FROM itemAttribute WHERE itemId = ?", (itemId,)
            )
        },
        categories={
            r["platform"]
            for r in connection.execute(
                "SELECT DISTINCT platform FROM itemCategory WHERE itemId = ?", (itemId,)
            )
        },
    )


def _has(facts: ItemFacts, requirement: str, platform: str) -> bool:
    return {
        "a SKU": bool(facts.sku),
        "a title": bool(facts.title.strip()),
        "a description": bool(facts.description.strip()),
        "a brand": bool(facts.brand.strip()),
        "a condition": bool(facts.conditionNote.strip()),
        "a price": facts.price is not None and facts.price > 0,
        "at least one photo": facts.imageCount > 0,
        "a size": "size" in facts.attributes,
        "a colour": "colour" in facts.attributes,
        "measurements": "measurement" in facts.attributes,
        "a category": platform in facts.categories or "internal" in facts.categories,
    }.get(requirement, True)


def missingFor(facts: ItemFacts, platform: str = "vinted") -> list[str]:
    """What has to be filled in before this can go on that platform."""
    return [need for need in REQUIRED.get(platform, []) if not _has(facts, need, platform)]


def recommendedFor(facts: ItemFacts, platform: str = "vinted") -> list[str]:
    """Worth having, never a reason to hold an item back (D-103)."""
    return [need for need in RECOMMENDED.get(platform, []) if not _has(facts, need, platform)]


def needsChecking(facts: ItemFacts) -> bool:
    """True until a person has confirmed the details are right."""
    return not facts.verifiedAt


def suggestedStatus(facts: ItemFacts, platform: str = "vinted") -> str:
    """Where an imported item belongs.

    Never `on_sale` — that is decided by whether a listing actually exists, not
    by whether the details look complete.
    """
    if missingFor(facts, platform) or needsChecking(facts):
        return "needs_info"
    return "draft"


def summarise(facts: ItemFacts, platform: str = "vinted") -> str:
    """One sentence for the screen, in words rather than counts of nothing."""
    missing = missingFor(facts, platform)
    if missing:
        if len(missing) == 1:
            return f"Needs {missing[0]}."
        return f"Needs {', '.join(missing[:-1])} and {missing[-1]}."
    if needsChecking(facts):
        return "Everything is filled in, but nobody has checked it yet."
    return "Ready."
