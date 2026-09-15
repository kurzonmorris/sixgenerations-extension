"""Getting the photographs off Crosslist and onto the server, for good.

**Why this is urgent.** Every one of the 9,098 photo URLs in the export points at
`media-na.crosslist.com` — the tool being paid for, not a marketplace. When that
subscription ends those URLs very likely stop resolving, and for the items that
have never been listed anywhere it is the only copy that exists.

**About the order they arrive in.** Vinted keeps photos in the order the seller
chose. Crosslist downloaded them and kept its own order. So the position that
comes with the import is a guess, recorded as `orderSource = 'crosslist'`, and it
must not be treated as the seller's intention. Reading Vinted later replaces it
with the real order; a person dragging them into place beats both.

Resumable by design: only rows with no file yet are fetched, so it can be stopped
and started as often as needed.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from .appLogging import getLogger

log = getLogger("photos")

TIMEOUT = 30
RETRIES = 3
WORKERS = 5          # polite: their servers, and nothing here is in a hurry
PAUSE = 0.05


@dataclass
class FetchCounts:
    wanted: int = 0
    fetched: int = 0
    alreadyHad: int = 0
    failed: int = 0
    bytes: int = 0

    def asSentence(self) -> str:
        megabytes = self.bytes / 1_000_000
        return (
            f"{self.fetched} fetched, {self.alreadyHad} already here, "
            f"{self.failed} failed, {megabytes:,.0f} MB"
        )


def imagesFolder(dataDir: Path) -> Path:
    folder = Path(dataDir) / "images"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def outstanding(connection: sqlite3.Connection, limit: int | None = None) -> list[sqlite3.Row]:
    """Photos recorded but not yet on disk. Failures are included so a retry works."""
    sql = (
        "SELECT imageId, itemId, position, sourceUrl FROM itemImage"
        " WHERE filePath = '' AND sourceUrl != '' ORDER BY itemId, position"
    )
    if limit:
        sql += f" LIMIT {int(limit)}"
    return list(connection.execute(sql))


def _extensionFor(url: str) -> str:
    tail = url.rsplit(".", 1)[-1].lower().split("?")[0]
    return tail if tail in {"jpg", "jpeg", "png", "webp", "gif"} else "jpg"


def _download(url: str) -> bytes:
    """Retries a connection that failed, never a server that said no.

    A 404 is an answer: the photo is gone. Asking three more times wastes
    everyone's time and, across 9,098 photos, a great deal of it.
    """
    lastProblem: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "sixgenbot"})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as reply:
                return reply.read()
        except urllib.error.HTTPError as problem:
            if 400 <= problem.code < 500:
                raise                      # a definite no
            lastProblem = problem
        except (urllib.error.URLError, TimeoutError, OSError) as problem:
            lastProblem = problem
        if attempt < RETRIES:
            time.sleep(attempt * 2)        # 2s, then 4s
    raise lastProblem or RuntimeError("download failed")


def fetchOne(row: sqlite3.Row, dataDir: Path) -> tuple[int, str, str, int, str]:
    """(imageId, filePath, sha256, bytes, error). Never raises — the caller records."""
    folder = imagesFolder(dataDir) / row["itemId"]
    target = folder / f"{row['position']:03d}.{_extensionFor(row['sourceUrl'])}"

    if target.exists() and target.stat().st_size > 0:
        raw = target.read_bytes()
        return row["imageId"], str(target), hashlib.sha256(raw).hexdigest(), len(raw), ""

    try:
        raw = _download(row["sourceUrl"])
    except Exception as problem:
        return row["imageId"], "", "", 0, str(problem)[:200]

    if not raw:
        return row["imageId"], "", "", 0, "the server returned nothing"

    folder.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    time.sleep(PAUSE)
    return row["imageId"], str(target), hashlib.sha256(raw).hexdigest(), len(raw), ""


def fetchAll(
    connection: sqlite3.Connection,
    dataDir: Path,
    limit: int | None = None,
    onProgress=None,
) -> FetchCounts:
    """Downloads everything still missing. Safe to stop and run again."""
    jobs = outstanding(connection, limit)
    counts = FetchCounts(wanted=len(jobs))
    if not jobs:
        log.info("every photo is already here")
        return counts

    log.info(f"fetching {len(jobs)} photos")

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for done, (imageId, filePath, digest, size, error) in enumerate(
            pool.map(lambda row: fetchOne(row, dataDir), jobs), start=1
        ):
            if error:
                counts.failed += 1
                connection.execute(
                    "UPDATE itemImage SET fetchError = ? WHERE imageId = ?", (error, imageId)
                )
            else:
                counts.fetched += 1
                counts.bytes += size
                connection.execute(
                    "UPDATE itemImage SET filePath = ?, sha256 = ?, bytes = ?,"
                    " fetchedAt = datetime('now'), fetchError = '' WHERE imageId = ?",
                    (filePath, digest, size, imageId),
                )

            if onProgress and done % 100 == 0:
                onProgress(done, len(jobs))
            if done % 500 == 0:
                log.info(f"  {done} of {len(jobs)} — {counts.asSentence()}")

    log.info("photos: " + counts.asSentence())
    return counts


def duplicateImages(connection: sqlite3.Connection) -> list[tuple[str, int]]:
    """Identical photographs held against more than one item, by content.

    Worth knowing: a garment returned and relisted appears twice in the export
    with different URLs but the same photographs, and this is the only way to
    tell that from two genuinely different garments.
    """
    return [
        (row["sha256"], row["items"])
        for row in connection.execute(
            "SELECT sha256, COUNT(DISTINCT itemId) AS items FROM itemImage"
            " WHERE sha256 != '' GROUP BY sha256 HAVING items > 1 ORDER BY items DESC"
        )
    ]
