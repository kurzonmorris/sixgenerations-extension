"""Small copies of the photographs, made once and kept.

A table of 50 rows that sends 50 full-size photographs is a slow table. The
browser makes them small, but only after it has downloaded every one of them.
So the small copy is made here, written next to the database, and served
instead.

**Pillow is optional.** If it is not installed the caller is told so and serves
the full-size photograph, which is slow but correct. A missing library must not
empty the screen.
"""

from __future__ import annotations

from pathlib import Path

from .appLogging import getLogger

log = getLogger("thumbnails")

SIZE = 320          # twice the width shown, so it stays sharp on a good screen
QUALITY = 78

try:
    from PIL import Image
    canResize = True
except ImportError:                                  # pragma: no cover
    Image = None
    canResize = False
    log.warning("Pillow is not installed — the full-size photographs will be served")


def thumbnailsFolder(dataDir: Path) -> Path:
    folder = Path(dataDir) / "thumbnails"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def thumbnailFor(dataDir: Path, imageId: int, source: Path) -> Path | None:
    """The small copy, made if it is not there yet. None means serve the original.

    The name carries the size, so changing SIZE later makes new files rather
    than serving stale ones at the wrong size.
    """
    if not canResize or not source.is_file():
        return None

    target = thumbnailsFolder(dataDir) / f"{imageId}_{SIZE}.jpg"
    if target.is_file() and target.stat().st_size > 0:
        return target

    try:
        with Image.open(source) as picture:
            picture = picture.convert("RGB")
            picture.thumbnail((SIZE, SIZE))
            picture.save(target, "JPEG", quality=QUALITY, optimize=True)
    except Exception as problem:
        log.warning(f"could not make a small copy of image {imageId}: {problem}")
        return None

    return target


def removeAll(dataDir: Path) -> int:
    """Throws the small copies away. They are made again on demand."""
    folder = thumbnailsFolder(dataDir)
    gone = 0
    for file in folder.glob("*.jpg"):
        file.unlink()
        gone += 1
    return gone
