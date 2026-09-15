"""Fetching the photographs.

Served from a local HTTP server rather than mocked, so the download path itself
is exercised — reading, writing, hashing, retrying and recording.
"""

from __future__ import annotations

import http.server
import threading

import pytest

from sixgenbot.core.database import Database
from sixgenbot.core.photoStore import (
    FetchCounts,
    duplicateImages,
    fetchAll,
    outstanding,
)

REAL_JPEG = bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"\xff\xd9"
OTHER_JPEG = bytes.fromhex("ffd8ffe000104a46494600010100000100010000") + b"different\xff\xd9"


class Serve(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/missing"):
            self.send_error(404)
            return
        body = OTHER_JPEG if self.path.startswith("/other") else REAL_JPEG
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


@pytest.fixture
def photoServer():
    server = http.server.HTTPServer(("127.0.0.1", 0), Serve)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def databaseWithPhotos(tmp_path, *urls, itemId="i1"):
    database = Database(tmp_path / "db.sqlite")
    database.migrate()
    connection = database.connection()
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, dateAdded)"
        " VALUES (?, '13-8 24', 'needs_info', 'Navy coat', date('now'))",
        (itemId,),
    )
    for position, url in enumerate(urls, start=1):
        connection.execute(
            "INSERT INTO itemImage (itemId, position, filePath, sourceUrl, orderSource)"
            " VALUES (?, ?, '', ?, 'crosslist')",
            (itemId, position, url),
        )
    return database


def test_photos_are_fetched_and_recorded(tmp_path, photoServer):
    database = databaseWithPhotos(tmp_path, f"{photoServer}/p1.jpg", f"{photoServer}/p2.jpg")
    connection = database.connection()

    counts = fetchAll(connection, tmp_path)

    assert counts.fetched == 2 and counts.failed == 0
    rows = list(connection.execute("SELECT filePath, sha256, bytes, fetchedAt FROM itemImage ORDER BY position"))
    for row in rows:
        assert row["filePath"] and row["sha256"] and row["bytes"] > 0 and row["fetchedAt"]
        from pathlib import Path
        assert Path(row["filePath"]).read_bytes() == REAL_JPEG


def test_photos_keep_the_position_they_arrived_in(tmp_path, photoServer):
    database = databaseWithPhotos(tmp_path, f"{photoServer}/a.jpg", f"{photoServer}/b.jpg", f"{photoServer}/c.jpg")
    fetchAll(database.connection(), tmp_path)

    names = [
        row["filePath"].rsplit("/", 1)[-1]
        for row in database.connection().execute("SELECT filePath FROM itemImage ORDER BY position")
    ]
    assert names == ["001.jpg", "002.jpg", "003.jpg"]


def test_the_order_is_recorded_as_a_guess_not_the_truth(tmp_path, photoServer):
    """Vinted holds the seller's order. Crosslist kept its own. This says which."""
    database = databaseWithPhotos(tmp_path, f"{photoServer}/a.jpg")
    fetchAll(database.connection(), tmp_path)

    assert database.connection().execute(
        "SELECT orderSource FROM itemImage"
    ).fetchone()["orderSource"] == "crosslist"


def test_running_it_again_fetches_nothing(tmp_path, photoServer):
    database = databaseWithPhotos(tmp_path, f"{photoServer}/a.jpg", f"{photoServer}/b.jpg")
    connection = database.connection()

    fetchAll(connection, tmp_path)
    second = fetchAll(connection, tmp_path)

    assert second.wanted == 0 and second.fetched == 0


def test_one_dead_url_does_not_stop_the_others(tmp_path, photoServer):
    database = databaseWithPhotos(tmp_path, f"{photoServer}/missing.jpg", f"{photoServer}/good.jpg")
    connection = database.connection()

    counts = fetchAll(connection, tmp_path)

    assert counts.fetched == 1 and counts.failed == 1
    failed = connection.execute("SELECT fetchError FROM itemImage WHERE fetchError != ''").fetchone()
    assert "404" in failed["fetchError"]


def test_a_failure_can_be_retried_later(tmp_path, photoServer):
    """A dead URL today may be a working one tomorrow — nothing is given up on."""
    database = databaseWithPhotos(tmp_path, f"{photoServer}/missing.jpg")
    connection = database.connection()
    fetchAll(connection, tmp_path)

    assert len(outstanding(connection)) == 1, "a failed photo stays on the list"


def test_identical_photographs_across_items_are_findable(tmp_path, photoServer):
    """A garment returned and relisted appears twice with the same photographs
    under different URLs. Content is the only way to tell."""
    database = databaseWithPhotos(tmp_path, f"{photoServer}/a.jpg", itemId="i1")
    connection = database.connection()
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, dateAdded)"
        " VALUES ('i2', '13-8 25', 'needs_info', 'Navy coat again', date('now'))"
    )
    connection.execute(
        "INSERT INTO itemImage (itemId, position, filePath, sourceUrl, orderSource)"
        " VALUES ('i2', 1, '', ?, 'crosslist')",
        (f"{photoServer}/b.jpg",),   # a different URL, the same bytes
    )

    fetchAll(connection, tmp_path)

    duplicates = duplicateImages(connection)
    assert duplicates and duplicates[0][1] == 2


def test_different_photographs_are_not_reported_as_duplicates(tmp_path, photoServer):
    database = databaseWithPhotos(tmp_path, f"{photoServer}/a.jpg", itemId="i1")
    connection = database.connection()
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, dateAdded)"
        " VALUES ('i2', '13-8 25', 'needs_info', 'A different coat', date('now'))"
    )
    connection.execute(
        "INSERT INTO itemImage (itemId, position, filePath, sourceUrl, orderSource)"
        " VALUES ('i2', 1, '', ?, 'crosslist')",
        (f"{photoServer}/other.jpg",),
    )

    fetchAll(connection, tmp_path)
    assert duplicateImages(connection) == []


def test_a_file_already_on_disk_is_not_fetched_again(tmp_path, photoServer):
    database = databaseWithPhotos(tmp_path, f"{photoServer}/a.jpg")
    connection = database.connection()
    fetchAll(connection, tmp_path)

    connection.execute("UPDATE itemImage SET filePath = ''")   # as if the record was lost
    counts = fetchAll(connection, tmp_path)

    assert counts.fetched == 1, "it is re-recorded"
    assert counts.bytes == len(REAL_JPEG)


def test_nothing_to_do_is_not_an_error(tmp_path):
    database = Database(tmp_path / "db.sqlite")
    database.migrate()
    assert fetchAll(database.connection(), tmp_path) == FetchCounts()
