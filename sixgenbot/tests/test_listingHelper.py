"""Putting one garment back on Vinted, with everything laid out ready to copy."""

from __future__ import annotations

import io
import zipfile

from PIL import Image
from fastapi.testclient import TestClient

from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.appLogging import setupLogging
from sixgenbot.core.database import reindexItem
from sixgenbot.core.listingSheet import sheetFor, waitingToList
from sixgenbot.core.moduleLoader import loadModules
from sixgenbot.core.webApp import Bot


def buildClient(tmp_path):
    setupLogging(level="DEBUG")
    bot = Bot(loadConfig(tmp_path))
    bot.db.migrate()
    bot.modules = loadModules(bot)
    return TestClient(bot.buildApp()), bot


def addItem(connection, itemId, sku, **overrides):
    row = {"title": "Navy floral dress", "description": "A dress.", "brand": "Jacques Vert",
           "price": 1200, "status": "needs_info", "dateListed": None,
           "conditionNote": "Very good", "weightGrams": 405}
    row.update(overrides)
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, description, brand, price, dateAdded,"
        " dateListed, conditionNote, weightGrams) VALUES (?, ?, ?, ?, ?, ?, ?, '2026-09-20',"
        " ?, ?, ?)",
        (itemId, sku, row["status"], row["title"], row["description"], row["brand"],
         row["price"], row["dateListed"], row["conditionNote"], row["weightGrams"]))
    reindexItem(connection, itemId)
    return itemId


def addPhotos(bot, itemId, howMany=3):
    folder = bot.config.dataDir / "images" / itemId
    folder.mkdir(parents=True, exist_ok=True)
    for n in range(1, howMany + 1):
        path = folder / f"{n:03d}.jpg"
        Image.new("RGB", (900, 1200), (80 + n * 20, 100, 120)).save(path, "JPEG")
        bot.db.connection().execute(
            "INSERT INTO itemImage (itemId, position, filePath, sourceUrl)"
            " VALUES (?, ?, ?, 'https://example.invalid/p.jpg')", (itemId, n, str(path)))


# --- the sheet --------------------------------------------------------------

def test_the_sku_is_put_back_on_the_end_of_the_description(tmp_path):
    """A description retyped without it is a garment the system loses."""
    _, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24", description="A navy dress.")

    made = sheetFor(bot.db.connection(), "i1")
    assert made.description.rstrip().endswith("13-8 24")


def test_a_sku_already_in_the_description_is_not_added_twice(tmp_path):
    _, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24", description="A navy dress.\n\n13-8 24")

    made = sheetFor(bot.db.connection(), "i1")
    assert made.description.count("13-8 24") == 1


def test_the_sheet_says_where_the_garment_is_in_the_room(tmp_path):
    _, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    assert sheetFor(bot.db.connection(), "i1").whereItIs == "column 13, box 8, item 24"


def test_the_sheet_says_what_is_still_missing(tmp_path):
    _, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24", brand="")

    made = sheetFor(bot.db.connection(), "i1")
    assert "a brand" in made.missing
    assert "at least one photo" in made.missing


def test_money_is_shown_in_pounds(tmp_path):
    _, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24", price=1850)

    assert sheetFor(bot.db.connection(), "i1").price == "18.50"


def test_an_item_that_is_not_there_gives_nothing_rather_than_an_error(tmp_path):
    _, bot = buildClient(tmp_path)
    assert sheetFor(bot.db.connection(), "nosuchitem") is None


# --- the photographs --------------------------------------------------------

def test_the_photographs_download_numbered_in_order(tmp_path):
    """A listing form uploads them in the order they are picked. 01 before 02."""
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")
    addPhotos(bot, "i1", 3)

    reply = client.get("/list/i1/photos.zip")

    assert reply.headers["content-disposition"] == 'attachment; filename="13-8-24.zip"'
    inside = zipfile.ZipFile(io.BytesIO(reply.content)).namelist()
    assert inside == ["13-8-24_01.jpg", "13-8-24_02.jpg", "13-8-24_03.jpg"]


def test_a_photograph_that_is_not_on_disk_is_left_out_rather_than_breaking(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")
    addPhotos(bot, "i1", 1)
    bot.db.connection().execute(
        "INSERT INTO itemImage (itemId, position, filePath, sourceUrl)"
        " VALUES ('i1', 9, '/nowhere/gone.jpg', '')")

    reply = client.get("/list/i1/photos.zip")
    assert len(zipfile.ZipFile(io.BytesIO(reply.content)).namelist()) == 1


# --- the queue --------------------------------------------------------------

def test_only_items_with_photographs_here_are_offered(tmp_path):
    """An item with no photographs cannot be listed at all."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1")
    addPhotos(bot, "i1", 1)
    addItem(connection, "i2", "1-1-2")

    assert [row["itemId"] for row in waitingToList(connection)] == ["i1"]


def test_an_item_already_listed_is_not_offered_again(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", dateListed="2026-04-21 10:00:00")
    addPhotos(bot, "i1", 1)

    assert waitingToList(connection) == []


def test_the_queue_is_in_the_order_the_room_is_walked(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    for itemId, sku in [("i1", "13-8-24"), ("i2", "7-4-21"), ("i3", "7-4-3")]:
        addItem(connection, itemId, sku)
        addPhotos(bot, itemId, 1)

    assert [row["itemId"] for row in waitingToList(connection)] == ["i3", "i2", "i1"]


def test_the_page_says_how_many_have_no_photographs_yet(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "1-1-1")

    page = client.get("/list").text
    assert "have no photographs here yet" in page
    assert "/photos" in page


# --- recording that it is up ------------------------------------------------

def test_saying_it_is_up_records_the_date_and_the_listing(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addPhotos(bot, "i1", 1)

    client.post("/list/i1/listed", data={"url": "https://www.vinted.co.uk/items/1", "price": "18"},
                follow_redirects=False)

    item = connection.execute("SELECT dateListed, status FROM item WHERE itemId='i1'").fetchone()
    listing = connection.execute("SELECT * FROM listing WHERE itemId='i1'").fetchone()
    assert item["dateListed"] is not None
    assert item["status"] == "on_sale"
    assert listing["platform"] == "vinted"
    assert listing["state"] == "live"
    assert listing["price"] == 1800
    assert listing["url"] == "https://www.vinted.co.uk/items/1"


def test_saying_it_is_up_twice_does_not_make_two_listings(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addPhotos(bot, "i1", 1)

    client.post("/list/i1/listed", data={"url": "https://a"}, follow_redirects=False)
    client.post("/list/i1/listed", data={"url": "https://b"}, follow_redirects=False)

    rows = connection.execute("SELECT url FROM listing WHERE itemId='i1'").fetchall()
    assert len(rows) == 1
    assert rows[0]["url"] == "https://b"


def test_no_price_typed_keeps_the_price_the_item_already_has(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", price=1200)
    addPhotos(bot, "i1", 1)

    client.post("/list/i1/listed", data={"url": ""}, follow_redirects=False)

    assert connection.execute(
        "SELECT price FROM listing WHERE itemId='i1'").fetchone()["price"] == 1200


def test_listing_it_is_written_into_the_history(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addPhotos(bot, "i1", 1)

    client.post("/list/i1/listed", data={"url": ""}, follow_redirects=False)

    row = connection.execute(
        "SELECT action, field FROM event WHERE subject='i1' AND action='listed'").fetchone()
    assert (row["action"], row["field"]) == ("listed", "Vinted")


def test_an_item_that_goes_up_leaves_the_waiting_list(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addPhotos(bot, "i1", 1)

    assert len(waitingToList(connection)) == 1
    client.post("/list/i1/listed", data={"url": ""}, follow_redirects=False)
    assert waitingToList(connection) == []


# --- the screen -------------------------------------------------------------

def test_the_sheet_page_shows_everything_the_form_asks_for(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addPhotos(bot, "i1", 2)
    connection.execute("INSERT INTO itemAttribute (itemId, attribute, value, system, isPrimary)"
                       " VALUES ('i1', 'size', '20', 'UK', 1)")

    page = client.get("/list/i1").text
    assert "Navy floral dress" in page
    assert "13-8 24" in page
    assert "column 13, box 8, item 24" in page
    assert "Jacques Vert" in page
    assert "UK 20" in page
    assert "Very good" in page
    assert "/list/i1/photos.zip" in page


def test_the_boxes_are_for_copying_out_of_not_typing_into(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    page = client.get("/list/i1").text
    assert 'id="title" readonly' in page
    assert 'id="description" readonly' in page


def test_an_item_that_is_not_ready_says_so_rather_than_pretending(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24", brand="")

    page = client.get("/list/i1").text
    assert "Not ready yet" in page
    assert "Traceback" not in page


def test_asking_for_an_item_that_is_gone_is_a_sentence(tmp_path):
    client, _ = buildClient(tmp_path)
    reply = client.get("/list/nosuchitem", follow_redirects=True)
    assert "There is no such item" in reply.text
    assert "Traceback" not in reply.text


def test_the_page_does_not_claim_tab_picks_out_a_tall_box(tmp_path):
    """Measured in Chromium: Tab selects an <input>, never a <textarea>.

    Saying otherwise is worse than saying nothing — it sends somebody to type
    over text that is still there.
    """
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    page = client.get("/list/i1").text
    assert "A one-line box is picked out" in page
    assert "Ctrl and A" in page, "the tall box needs Ctrl and A first"


def test_a_size_with_no_system_is_shown_plainly(tmp_path):
    """"XL", not "size XL". The row is already labelled Size."""
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    connection.execute("INSERT INTO itemAttribute (itemId, attribute, value, system, isPrimary)"
                       " VALUES ('i1', 'size', 'XL', '', 1)")

    page = client.get("/list/i1").text
    assert ">XL<" in page.replace("\n", "").replace("        ", "") or "XL" in page
    assert "size XL" not in page
