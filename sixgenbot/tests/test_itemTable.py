"""The Table: every item, one search box, filters, and a page at a time."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.appLogging import setupLogging
from sixgenbot.core.database import reindexItem
from sixgenbot.core.itemQuery import Filters, buildWhere, countItems, describe
from sixgenbot.core.moduleLoader import loadModules
from sixgenbot.core.webApp import Bot


def buildClient(tmp_path):
    setupLogging(level="DEBUG")
    bot = Bot(loadConfig(tmp_path))
    bot.db.migrate()
    bot.modules = loadModules(bot)
    return TestClient(bot.buildApp()), bot


def addItem(connection, itemId, sku, **overrides):
    row = {"title": "Navy floral dress", "brand": "Jacques Vert", "price": 1200,
           "status": "needs_info", "dateListed": None, "dateAdded": "2026-09-20"}
    row.update(overrides)
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, brand, price, dateAdded, dateListed)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (itemId, sku, row["status"], row["title"], row["brand"], row["price"],
         row["dateAdded"], row["dateListed"]),
    )
    reindexItem(connection, itemId)
    return itemId


def addSize(connection, itemId, value, system="UK"):
    connection.execute(
        "INSERT INTO itemAttribute (itemId, attribute, value, system, isPrimary)"
        " VALUES (?, 'size', ?, ?, 1)", (itemId, value, system))
    reindexItem(connection, itemId)


def addPhoto(connection, itemId, imageId, filePath="/data/images/x/001.jpg"):
    connection.execute(
        "INSERT INTO itemImage (imageId, itemId, position, filePath, sourceUrl)"
        " VALUES (?, ?, 1, ?, 'https://example.invalid/p.jpg')", (imageId, itemId, filePath))


# --- finding ----------------------------------------------------------------

def test_the_search_box_reaches_every_field(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", title="Green velvet jacket")
    addItem(connection, "i2", "7-4-21", title="Cotton shirt")

    where, parameters, _ = buildWhere(connection, Filters(q="velvet"))
    assert countItems(connection, where, parameters) == 1


def test_a_box_number_finds_everything_in_that_box(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addItem(connection, "i2", "13-8-25")
    addItem(connection, "i3", "7-4-21")

    where, parameters, _ = buildWhere(connection, Filters(box="13-8"))
    assert countItems(connection, where, parameters) == 2


def test_a_box_written_with_a_space_works_too(tmp_path):
    """The business writes 13-8 24. A person types the box as 13-8, or 13 8."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    where, parameters, _ = buildWhere(connection, Filters(box="13 8"))
    assert countItems(connection, where, parameters) == 1


def test_filters_combine_rather_than_replace_each_other(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", status="on_sale")
    addSize(connection, "i1", "12")
    addItem(connection, "i2", "13-8-25", status="on_sale")
    addSize(connection, "i2", "14")

    where, parameters, _ = buildWhere(connection, Filters(status="on_sale", size="12"))
    assert countItems(connection, where, parameters) == 1


def test_the_photographs_filter_works_both_ways(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addPhoto(connection, "i1", 1)
    addItem(connection, "i2", "13-8-25")

    has, parameters, _ = buildWhere(connection, Filters(photos="yes"))
    none, noneParameters, _ = buildWhere(connection, Filters(photos="no"))
    assert countItems(connection, has, parameters) == 1
    assert countItems(connection, none, noneParameters) == 1


def test_a_photo_row_with_no_file_does_not_count_as_having_one(tmp_path):
    """A row that was imported but never fetched is not a photograph you have."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addPhoto(connection, "i1", 1, filePath="")

    where, parameters, _ = buildWhere(connection, Filters(photos="yes"))
    assert countItems(connection, where, parameters) == 0


def test_the_price_range_is_typed_in_pounds_and_matched_in_pence(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", price=1200)
    addItem(connection, "i2", "13-8-25", price=3000)

    where, parameters, _ = buildWhere(connection, Filters(priceFrom="20"))
    assert countItems(connection, where, parameters) == 1


def test_a_search_that_matches_nothing_matches_nothing(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    where, parameters, _ = buildWhere(connection, Filters(q="zzzzzz"))
    assert countItems(connection, where, parameters) == 0


# --- saying what it is doing ------------------------------------------------

def test_the_filters_are_described_in_words_not_ticked_boxes():
    sentence = describe(Filters(status="on_sale", size="12", photos="yes"), 34)
    assert sentence == "On sale, size 12, with photographs — 34 items."


def test_no_filters_says_everything(tmp_path):
    assert describe(Filters(), 2125) == "Everything — 2,125 items."


def test_one_item_is_not_called_one_items():
    assert describe(Filters(), 1).endswith("1 item.")


# --- the screen -------------------------------------------------------------

def test_the_page_lists_items_with_the_sku_the_business_writes(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    page = client.get("/table").text
    assert "13-8 24" in page
    assert "Navy floral dress" in page
    assert "Everything — 1 item." in page


def test_a_thumbnail_is_shown_when_the_photograph_is_here(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addPhoto(connection, "i1", 7)

    page = client.get("/table").text
    assert '/photos/image/7' in page


def test_the_columns_can_be_chosen(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    page = client.get("/table?show=sku&show=title").text
    assert "Navy floral dress" in page
    assert "<th>Brand</th>" not in page


def test_the_chosen_columns_are_remembered(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    client.get("/table?show=sku&show=title")
    page = client.get("/table").text
    assert "<th>Brand</th>" not in page


def test_paging_keeps_the_search_and_the_filters(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    for n in range(1, 61):
        addItem(connection, f"i{n}", f"1-1-{n}", status="on_sale")

    page = client.get("/table?status=on_sale&sort=title").text
    assert "status=on_sale" in page and "sort=title" in page
    assert "page=2" in page


def test_nothing_matching_is_a_sentence_not_a_blank_table(tmp_path):
    client, _ = buildClient(tmp_path)
    page = client.get("/table?q=zzzzzz").text
    assert "Nothing matches" in page
    assert "Traceback" not in page


def test_a_page_beyond_the_last_one_shows_the_last_one(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    page = client.get("/table?page=999").text
    assert "13-8 24" in page
    assert "Traceback" not in page


def test_typed_punctuation_cannot_break_the_search(tmp_path):
    """A person types a quote or a bracket. That is not search syntax."""
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    reply = client.get('/table?q=" OR (velvet')
    assert reply.status_code == 200
    assert "Traceback" not in reply.text


def test_a_box_code_typed_into_the_search_box_is_not_a_box_search(tmp_path):
    """Full-text search splits 11-1 into two numbers. The Box field is the tool.

    The page says so, because a search that quietly returns the wrong set is
    worse than one that explains itself.
    """
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "11-1-1")
    addItem(connection, "i2", "1-11-1")

    assert client.get("/table?q=11-1").text.count("<tr>") > 2
    page = client.get("/table?box=11-1").text
    assert "Box 11-1 — 1 item." in page
