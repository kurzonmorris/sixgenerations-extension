"""Small copies of the photographs, and the stylesheet reaching the browser."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.appLogging import setupLogging
from sixgenbot.core.moduleLoader import loadModules
from sixgenbot.core.thumbnails import SIZE, removeAll, thumbnailFor, thumbnailsFolder
from sixgenbot.core.webApp import Bot, styleVersion


def buildClient(tmp_path):
    setupLogging(level="DEBUG")
    bot = Bot(loadConfig(tmp_path))
    bot.db.migrate()
    bot.modules = loadModules(bot)
    return TestClient(bot.buildApp()), bot


def aBigPhotograph(folder: Path, name="001.jpg", size=(2400, 1800)) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    Image.new("RGB", size, (90, 110, 130)).save(path, "JPEG", quality=90)
    return path


def addPhoto(connection, imageId, itemId, filePath):
    connection.execute(
        "INSERT OR IGNORE INTO item (itemId, sku, dateAdded) VALUES (?, ?, '2026-09-20')",
        (itemId, f"1-1 {imageId}"))
    connection.execute(
        "INSERT INTO itemImage (imageId, itemId, position, filePath, sourceUrl)"
        " VALUES (?, ?, 1, ?, 'https://example.invalid/p.jpg')", (imageId, itemId, str(filePath)))


# --- the small copies -------------------------------------------------------

def test_a_small_copy_fits_inside_the_size(tmp_path):
    big = aBigPhotograph(tmp_path / "images" / "i1")

    small = thumbnailFor(tmp_path, 1, big)

    assert small is not None
    with Image.open(small) as made:
        assert max(made.size) == SIZE


def test_a_small_copy_is_very_much_smaller(tmp_path):
    big = aBigPhotograph(tmp_path / "images" / "i1")

    small = thumbnailFor(tmp_path, 1, big)

    assert small.stat().st_size < big.stat().st_size / 4


def test_a_small_copy_is_made_once_and_kept(tmp_path):
    big = aBigPhotograph(tmp_path / "images" / "i1")

    first = thumbnailFor(tmp_path, 1, big)
    stamp = first.stat().st_mtime_ns
    second = thumbnailFor(tmp_path, 1, big)

    assert second == first
    assert second.stat().st_mtime_ns == stamp, "it was made a second time"


def test_the_size_is_in_the_name_so_a_change_does_not_serve_the_old_one(tmp_path):
    big = aBigPhotograph(tmp_path / "images" / "i1")
    assert thumbnailFor(tmp_path, 1, big).name == f"1_{SIZE}.jpg"


def test_a_photograph_that_is_not_there_gives_nothing_rather_than_an_error(tmp_path):
    assert thumbnailFor(tmp_path, 1, tmp_path / "gone.jpg") is None


def test_a_file_that_is_not_a_photograph_gives_nothing(tmp_path):
    notAPhoto = tmp_path / "notes.txt"
    notAPhoto.write_text("this is not a photograph")

    assert thumbnailFor(tmp_path, 1, notAPhoto) is None


def test_the_small_copies_can_be_thrown_away(tmp_path):
    big = aBigPhotograph(tmp_path / "images" / "i1")
    thumbnailFor(tmp_path, 1, big)

    assert removeAll(tmp_path) == 1
    assert not list(thumbnailsFolder(tmp_path).glob("*.jpg"))


# --- the screen -------------------------------------------------------------

def test_the_table_asks_for_the_small_copy(tmp_path):
    client, bot = buildClient(tmp_path)
    big = aBigPhotograph(bot.config.dataDir / "images" / "i1")
    addPhoto(bot.db.connection(), 7, "i1", big)

    page = client.get("/table").text
    assert "/photos/image/7?small=yes" in page


def test_the_small_copy_is_served_and_is_smaller_than_the_photograph(tmp_path):
    client, bot = buildClient(tmp_path)
    big = aBigPhotograph(bot.config.dataDir / "images" / "i1")
    addPhoto(bot.db.connection(), 7, "i1", big)

    small = client.get("/photos/image/7?small=yes")
    full = client.get("/photos/image/7")

    assert small.status_code == 200
    assert len(small.content) < len(full.content) / 4


def test_the_full_photograph_is_still_available(tmp_path):
    client, bot = buildClient(tmp_path)
    big = aBigPhotograph(bot.config.dataDir / "images" / "i1")
    addPhoto(bot.db.connection(), 7, "i1", big)

    full = client.get("/photos/image/7")
    assert full.status_code == 200
    assert len(full.content) == big.stat().st_size


# --- the stylesheet reaching the browser ------------------------------------

def test_the_stylesheet_address_carries_a_stamp(tmp_path):
    """Without it a browser keeps the old stylesheet, and a screen change never
    arrives. That is what made the photographs show at full size."""
    client, _ = buildClient(tmp_path)
    page = client.get("/table").text
    assert f"/static/sixgenbot.css?v={styleVersion()}" in page


def test_the_stamp_changes_when_the_stylesheet_changes(tmp_path, monkeypatch):
    import sixgenbot.core.webApp as webApp

    before = webApp.styleVersion()
    sheet = webApp.HERE / "static" / "sixgenbot.css"
    original = sheet.read_bytes()
    try:
        sheet.write_bytes(original + b"\n/* a change */\n")
        assert webApp.styleVersion() != before
    finally:
        sheet.write_bytes(original)
