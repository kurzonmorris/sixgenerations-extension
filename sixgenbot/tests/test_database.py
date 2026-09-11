"""The database: migrations, search, and the rule that nothing is deleted."""

from __future__ import annotations

import sqlite3

import pytest

from sixgenbot.core.database import (
    Database,
    connect,
    counts,
    migrate,
    reindexItem,
    schemaVersion,
    searchItems,
)


def freshDatabase(tmp_path):
    database = Database(tmp_path / "sixgenbot.sqlite")
    database.migrate()
    return database


def addItem(connection, sku, title="", brand="", description="", status="on_sale", **columns):
    itemId = f"item-{sku.replace(' ', '-')}"
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, brand, description, dateAdded)"
        " VALUES (?, ?, ?, ?, ?, ?, date('now'))",
        (itemId, sku, status, title, brand, description),
    )
    for attribute, value, system in columns.get("attributes", []):
        connection.execute(
            "INSERT INTO itemAttribute (itemId, attribute, value, system) VALUES (?, ?, ?, ?)",
            (itemId, attribute, value, system),
        )
    reindexItem(connection, itemId)
    return itemId


def test_migrations_run_once_and_are_safe_to_repeat(tmp_path):
    database = Database(tmp_path / "db.sqlite")
    first = database.migrate()
    assert first, "the first run must apply something"
    assert database.version == 1

    second = database.migrate()
    assert second == [], "a second run must apply nothing"
    assert database.version == 1


def test_the_schema_matches_the_data_model(tmp_path):
    connection = freshDatabase(tmp_path).connection()
    tables = {
        row["name"]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    for expected in (
        "item", "itemAttribute", "itemCategory", "listing", "itemImage",
        "salesOrder", "message", "lot", "purchase", "postingTrip", "event",
    ):
        assert expected in tables, f"{expected} is in docs/DATA_MODEL.md but not in the schema"


def test_a_sku_cannot_be_used_twice(tmp_path):
    connection = freshDatabase(tmp_path).connection()
    addItem(connection, "13-8 24")
    with pytest.raises(sqlite3.IntegrityError):
        addItem(connection, "13-8 24")


def test_five_digit_item_numbers_are_ordinary(tmp_path):
    """Item numbers are never recycled, so they climb — EXPLAINED section 7.7."""
    connection = freshDatabase(tmp_path).connection()
    addItem(connection, "5-6 17735", title="Vintage silk blouse")
    assert searchItems(connection, "17735")


def test_a_broken_status_is_refused(tmp_path):
    connection = freshDatabase(tmp_path).connection()
    with pytest.raises(sqlite3.IntegrityError):
        addItem(connection, "1-1 1", status="somethingMadeUp")


def test_nothing_is_deleted_when_an_item_sells(tmp_path):
    connection = freshDatabase(tmp_path).connection()
    itemId = addItem(connection, "13-8 24", title="Navy wool coat")

    connection.execute("UPDATE item SET status = 'sold', dateSold = date('now') WHERE itemId = ?", (itemId,))

    row = connection.execute("SELECT status, title FROM item WHERE itemId = ?", (itemId,)).fetchone()
    assert row["status"] == "sold"
    assert row["title"] == "Navy wool coat", "selling must not lose the item's details"


def test_search_finds_a_word_from_anywhere_in_the_item(tmp_path):
    """The question this answers is 'do you have anything with velvet in it?'"""
    connection = freshDatabase(tmp_path).connection()
    inDescription = addItem(connection, "1-1 1", title="Evening gown",
                            description="Deep green velvet, full length")
    inTitle = addItem(connection, "2-2 2", title="Velvet jacket")
    addItem(connection, "3-3 3", title="Cotton shirt", description="Plain white")

    found = set(searchItems(connection, "velvet"))
    assert found == {inDescription, inTitle}


def test_search_covers_attributes_and_the_sku(tmp_path):
    connection = freshDatabase(tmp_path).connection()
    itemId = addItem(connection, "13-8 24", title="Midi dress",
                     attributes=[("size", "12", "UK"), ("colour", "Navy", "")])

    assert searchItems(connection, "navy") == [itemId]
    assert searchItems(connection, "13-8") == [itemId]


def test_search_survives_whatever_someone_types(tmp_path):
    """FTS has its own syntax. A person typing quotes or a star must not hit it."""
    connection = freshDatabase(tmp_path).connection()
    addItem(connection, "1-1 1", title="Silk scarf")

    for typed in ['"', "*", "AND", "NOT велвет", "  ", "'quoted'", "50% wool"]:
        searchItems(connection, typed)  # must not raise


def test_reindexing_keeps_up_with_a_change(tmp_path):
    connection = freshDatabase(tmp_path).connection()
    itemId = addItem(connection, "1-1 1", title="Plain coat")
    assert searchItems(connection, "velvet") == []

    connection.execute("UPDATE item SET description = 'crushed velvet lining' WHERE itemId = ?", (itemId,))
    reindexItem(connection, itemId)
    assert searchItems(connection, "velvet") == [itemId]


def test_counts_are_zero_on_an_empty_database(tmp_path):
    assert freshDatabase(tmp_path).counts() == {
        "items": 0, "onSale": 0, "needsInfo": 0, "sold": 0,
        "posted": 0, "archived": 0, "orders": 0, "images": 0,
    }


def test_counts_split_by_status(tmp_path):
    database = freshDatabase(tmp_path)
    connection = database.connection()
    addItem(connection, "1-1 1", status="on_sale")
    addItem(connection, "1-1 2", status="on_sale")
    addItem(connection, "1-1 3", status="needs_info")
    addItem(connection, "1-1 4", status="sold")

    totals = database.counts()
    assert totals["items"] == 4
    assert totals["onSale"] == 2
    assert totals["needsInfo"] == 1
    assert totals["sold"] == 1


def test_money_is_kept_in_pence(tmp_path):
    """£12.50 is 1250. Floats and money do not mix — garmentItem.js learned this."""
    connection = freshDatabase(tmp_path).connection()
    itemId = addItem(connection, "1-1 1")
    connection.execute("UPDATE item SET price = 1250 WHERE itemId = ?", (itemId,))
    assert connection.execute("SELECT price FROM item WHERE itemId = ?", (itemId,)).fetchone()["price"] == 1250


def test_a_reference_to_something_missing_is_refused(tmp_path):
    connection = freshDatabase(tmp_path).connection()
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO listing (itemId, platform) VALUES ('nothing-like-this', 'vinted')"
        )


def test_a_failing_migration_leaves_nothing_behind(tmp_path):
    """The claim that a half-applied schema cannot happen, checked rather than said."""
    folder = tmp_path / "migrations"
    folder.mkdir()
    (folder / "0001_good.sql").write_text("CREATE TABLE good (id INTEGER PRIMARY KEY);")
    (folder / "0002_bad.sql").write_text(
        "CREATE TABLE halfway (id INTEGER PRIMARY KEY);\n"
        "CREATE TABLE halfway (id INTEGER PRIMARY KEY);"  # same name twice — fails
    )

    connection = connect(tmp_path / "db.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        migrate(connection, folder)

    tables = {r["name"] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "good" in tables, "the migration that worked should stay applied"
    assert "halfway" not in tables, "the failed migration must leave no trace"
    assert schemaVersion(connection) == 1, "only the good migration counts as applied"


def test_migrations_must_be_named_properly(tmp_path):
    folder = tmp_path / "migrations"
    folder.mkdir()
    (folder / "addSomeTable.sql").write_text("SELECT 1;")

    connection = connect(tmp_path / "db.sqlite")
    with pytest.raises(ValueError, match="0001_someName"):
        migrate(connection, folder)


def test_two_migrations_cannot_share_a_number(tmp_path):
    folder = tmp_path / "migrations"
    folder.mkdir()
    (folder / "0001_one.sql").write_text("SELECT 1;")
    (folder / "0001_two.sql").write_text("SELECT 1;")

    with pytest.raises(ValueError, match="share a number"):
        migrate(connect(tmp_path / "db.sqlite"), folder)
