"""Backups, and the restore that makes them worth taking.

A backup nobody has put back is a hope. The round trip runs on every test run.
"""

from __future__ import annotations

import gzip

import pytest

from sixgenbot.core.backup import (
    listBackups,
    makeBackup,
    pruneBackups,
    restore,
    verifyBackup,
)
from sixgenbot.core.database import Database


def databaseWithItems(tmp_path, howMany=3):
    database = Database(tmp_path / "sixgenbot.sqlite")
    database.migrate()
    connection = database.connection()
    for number in range(1, howMany + 1):
        connection.execute(
            "INSERT INTO item (itemId, sku, status, title, dateAdded)"
            " VALUES (?, ?, 'on_sale', ?, date('now'))",
            (f"item-{number}", f"13-8 {number}", f"Garment {number}"),
        )
    return database


def test_a_backup_can_be_put_back_and_the_data_is_all_there(tmp_path):
    """The whole point of stage 2. Not 'a file appeared' — the data came back."""
    database = databaseWithItems(tmp_path, howMany=5)
    made = makeBackup(database.path, tmp_path)

    # Lose everything.
    database.close()
    database.path.unlink()
    for leftover in tmp_path.glob("sixgenbot.sqlite-*"):
        leftover.unlink()

    counts = restore(made.path, database.path)
    assert counts["items"] == 5

    recovered = Database(database.path).connection()
    titles = [row["title"] for row in recovered.execute("SELECT title FROM item ORDER BY sku")]
    assert titles == [f"Garment {n}" for n in (1, 2, 3, 4, 5)]


def test_restoring_keeps_whatever_it_replaced(tmp_path):
    """A restore is the moment you least want a one-way door."""
    database = databaseWithItems(tmp_path, howMany=2)
    made = makeBackup(database.path, tmp_path)

    connection = database.connection()
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, dateAdded)"
        " VALUES ('item-later', '9-9 9', 'on_sale', 'Added after the backup', date('now'))"
    )
    database.close()

    restore(made.path, database.path)

    kept = database.path.with_suffix(database.path.suffix + ".beforeRestore")
    assert kept.exists(), "the replaced database must be kept"

    import sqlite3
    older = sqlite3.connect(kept)
    assert older.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 3
    older.close()


def test_a_backup_is_checked_when_it_is_taken(tmp_path):
    database = databaseWithItems(tmp_path, howMany=2)
    made = makeBackup(database.path, tmp_path)
    assert verifyBackup(made.path) == {"items": 2, "orders": 0}


def test_a_damaged_backup_is_refused_rather_than_restored(tmp_path):
    database = databaseWithItems(tmp_path, howMany=2)
    made = makeBackup(database.path, tmp_path)

    with gzip.open(made.path, "wb") as broken:
        broken.write(b"this is not a database")

    with pytest.raises(Exception):
        restore(made.path, database.path)

    assert database.path.exists(), "a refused restore must not have touched the live database"


def test_two_backups_in_the_same_second_do_not_overwrite_each_other(tmp_path):
    database = databaseWithItems(tmp_path, howMany=1)
    first = makeBackup(database.path, tmp_path, keep=99)
    second = makeBackup(database.path, tmp_path, keep=99)

    assert first.path != second.path
    assert first.path.exists() and second.path.exists()


def test_old_backups_are_pruned_and_the_newest_are_kept(tmp_path):
    database = databaseWithItems(tmp_path, howMany=1)
    for _ in range(4):
        makeBackup(database.path, tmp_path, keep=99)

    # Make them distinguishable by age.
    for index, file in enumerate(listBackups(tmp_path)):
        import os
        os.utime(file.path, (1_700_000_000 + index, 1_700_000_000 + index))

    newest = listBackups(tmp_path)[0].name
    pruneBackups(tmp_path, keep=2)

    left = listBackups(tmp_path)
    assert len(left) == 2
    assert left[0].name == newest, "pruning must keep the newest"


def test_backups_are_listed_newest_first(tmp_path):
    database = databaseWithItems(tmp_path, howMany=1)
    makeBackup(database.path, tmp_path)
    makeBackup(database.path, tmp_path)

    files = listBackups(tmp_path)
    assert files == sorted(files, key=lambda f: f.takenAt, reverse=True)
