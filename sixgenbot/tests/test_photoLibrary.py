"""The Photos page: bringing the photographs here before the subscription ends."""

from __future__ import annotations


from fastapi.testclient import TestClient

from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.appLogging import setupLogging
from sixgenbot.core.moduleLoader import loadModules
from sixgenbot.core.photoStore import fetchAll, storedCounts
from sixgenbot.core.webApp import Bot
from sixgenbot.modules.photoLibrary import routes


def buildClient(tmp_path):
    setupLogging(level="DEBUG")
    routes.run.__init__()
    bot = Bot(loadConfig(tmp_path))
    bot.db.migrate()
    bot.modules = loadModules(bot)
    return TestClient(bot.buildApp()), bot


def addPhoto(connection, imageId, itemId="i1", filePath="", error=""):
    connection.execute(
        "INSERT OR IGNORE INTO item (itemId, sku, dateAdded) VALUES (?, ?, '2026-09-20')",
        (itemId, f"1-1 {imageId}"),
    )
    connection.execute(
        "INSERT INTO itemImage (imageId, itemId, position, filePath, sourceUrl, fetchError,"
        " bytes) VALUES (?, ?, ?, ?, 'https://example.invalid/p.jpg', ?, ?)",
        (imageId, itemId, imageId, filePath, error, 1000 if filePath else 0),
    )


def test_the_page_says_how_many_are_safe_and_how_many_are_not(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addPhoto(connection, 1, filePath="/data/images/i1/001.jpg")
    addPhoto(connection, 2)

    page = client.get("/photos").text
    assert "Safely here" in page
    assert "Still only on Crosslist" in page


def test_counts_separate_here_from_still_to_come(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addPhoto(connection, 1, filePath="/data/images/i1/001.jpg")
    addPhoto(connection, 2)
    addPhoto(connection, 3, error="HTTP Error 404: Not Found")

    counts = storedCounts(connection)
    assert (counts["total"], counts["here"], counts["toGo"], counts["failed"]) == (3, 1, 2, 1)


def test_failures_are_grouped_and_named_rather_than_hidden(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addPhoto(connection, 1, error="HTTP Error 404: Not Found")
    addPhoto(connection, 2, error="HTTP Error 404: Not Found")

    page = client.get("/photos").text
    assert "HTTP Error 404: Not Found" in page
    assert "did not come" in page
    assert "Traceback" not in page


def test_an_empty_library_says_everything_is_here_rather_than_nothing(tmp_path):
    client, _ = buildClient(tmp_path)
    page = client.get("/photos").text
    assert "All here" in page
    assert "Traceback" not in page


def test_only_one_fetch_runs_at_a_time(tmp_path):
    client, bot = buildClient(tmp_path)
    addPhoto(bot.db.connection(), 1)

    routes.run.running = True
    reply = client.post("/photos/fetch", data={"howMany": "1"}, follow_redirects=True)
    assert "already running" in reply.text


def test_a_fetch_can_be_asked_to_stop(tmp_path):
    client, _ = buildClient(tmp_path)
    routes.run.running = True

    client.post("/photos/stop", follow_redirects=False)
    assert routes.run.stopping is True


def test_stopping_is_noticed_partway_through_not_at_the_end(tmp_path):
    """A Stop that only takes effect in an hour is not a Stop button."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    for imageId in range(1, 501):
        addPhoto(connection, imageId, itemId=f"i{imageId}")

    counts = fetchAll(connection, bot.config.dataDir, shouldStop=lambda: True)

    assert counts.wanted == 500
    assert counts.fetched == 0 and counts.failed == 0, "it should not have started at all"


def test_a_photo_that_is_not_here_is_not_served(tmp_path):
    client, bot = buildClient(tmp_path)
    addPhoto(bot.db.connection(), 1)

    reply = client.get("/photos/image/1", follow_redirects=True)
    assert "not here yet" in reply.text


def test_a_file_outside_the_images_folder_is_never_served(tmp_path):
    """The row holds a path; a path in the database is not permission to read it."""
    client, bot = buildClient(tmp_path)
    secret = tmp_path / "secrets.toml"
    secret.write_text("token = 'nobody should see this'")
    addPhoto(bot.db.connection(), 1, filePath=str(secret))

    reply = client.get("/photos/image/1", follow_redirects=True)
    assert "nobody should see this" not in reply.text
    assert "not here yet" in reply.text


def test_a_real_stored_photo_is_served(tmp_path):
    client, bot = buildClient(tmp_path)
    folder = bot.config.dataDir / "images" / "i1"
    folder.mkdir(parents=True)
    (folder / "001.jpg").write_bytes(b"\xff\xd8\xff pretend jpeg")
    addPhoto(bot.db.connection(), 1, filePath=str(folder / "001.jpg"))

    reply = client.get("/photos/image/1")
    assert reply.status_code == 200
    assert reply.content == b"\xff\xd8\xff pretend jpeg"


def test_duplicates_are_compared_by_content_not_by_address(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addPhoto(connection, 1, itemId="i1", filePath="/data/images/i1/001.jpg")
    addPhoto(connection, 2, itemId="i2", filePath="/data/images/i2/001.jpg")
    connection.execute("UPDATE itemImage SET sha256 = 'samebytes'")

    page = client.get("/photos/duplicates").text
    assert "samebytes"[:16] in page
    assert "not their addresses" in page
