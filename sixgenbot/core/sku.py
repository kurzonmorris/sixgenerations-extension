"""The SKU — this project's identity for a garment.

    13-8 24     column 13, box 8 high, item 24
    5-6 17735   column 5, box 6, item 17735

The business calls it the SKU, and it sits at the **end of every listing
description** on every platform. It is permanent: a returned garment keeps its
number and goes back in the same box, so the same listing can be re-uploaded
unchanged. Item numbers are never recycled, which is why they run to five
digits — each box has room for 99,999 over its life.

This is the Python twin of `source/core/storageCode.js`. The two must agree, or
the extension and the server will disagree about which garment is which —
`tests/test_sku.py` checks the pattern against the same cases the JavaScript
tests use.
"""

from __future__ import annotations

import re

# Anchored to the end of the text, which is where the code always sits. The
# anchor is what stops a size range like "fits 10-12" being read as a location.
TRAILING_SKU = re.compile(
    r"(\d{1,3})\s*[-–—]\s*(\d{1,3})\s*[-–—\s]\s*(\d{1,5})[\s.,;:]*$"
)


def parseSku(text: str | None) -> str:
    """The normalised form used as a key: "13-8-24". Empty string if there is none."""
    if not text:
        return ""
    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    found = TRAILING_SKU.search(cleaned)
    if not found:
        return ""
    column, box, item = found.groups()
    return f"{int(column)}-{int(box)}-{int(item)}"


def formatSku(sku: str | None) -> str:
    """The form written into a listing description: "13-8 24"."""
    parts = str(sku or "").split("-")
    return f"{parts[0]}-{parts[1]} {parts[2]}" if len(parts) == 3 else ""


def describeSku(sku: str | None) -> str:
    """Human readable, for a screen: "column 13, box 8, item 24"."""
    parts = str(sku or "").split("-")
    if len(parts) != 3:
        return ""
    column, box, item = parts
    return f"column {column}, box {box}, item {item}"


def withSku(description: str | None, sku: str) -> str:
    """Replaces the trailing SKU, or adds one if there is none.

    The Vinted write path will need this: editing a description must never lose
    the SKU, because the SKU is how the garment is recognised next time.
    """
    written = formatSku(sku)
    if not written:
        return description or ""

    body = str(description or "").rstrip()
    if parseSku(body):
        return TRAILING_SKU.sub(written, body)
    return f"{body}\n\n{written}" if body else written


def skuParts(sku: str) -> tuple[int, int, int] | None:
    """(column, box, item), for sorting a picking list into walking order."""
    parts = str(sku or "").split("-")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return None
    return int(parts[0]), int(parts[1]), int(parts[2])
