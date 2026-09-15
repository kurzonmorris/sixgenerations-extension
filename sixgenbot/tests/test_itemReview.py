"""The screen the backlog is cleared on: pick a batch, fix it, save the lot."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.appLogging import setupLogging
from sixgenbot.core.itemEdit import applyEdits, currentValues, markChecked, readMoney
from sixgenbot.core.moduleLoader import loadModules
from sixgenbot.core.webApp import Bot


def buildClient(tmp_path):
    setupLogging(level="DEBUG")
    bot = Bot(loadConfig(tmp_path))
    bot.db.migrate()
    bot.modules = loadModules(bot)
    return TestClient(bot.buildApp()), bot


def addItem(connection, itemId, sku, **overrides) -> str:
    row = {
        "title": "Navy floral dress",
        "brand": "Jacques Vert",
        "price": 1200,
        "dateListed": None,
        "status": "needs_info",
    }
    row.update(overrides)
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, brand, price, dateAdded, dateListed)"
        " VALUES (?, ?, ?, ?, ?, ?, '2026-09-15', ?)",
        (itemId, sku, row["status"], row["title"], row["brand"], row["price"], row["dateListed"]),
    )
    return itemId


# --- the values behind the boxes --------------------------------------------

def test_money_is_read_as_pounds_and_stored_as_pence():
    assert readMoney("12.50") == 1250
    assert readMoney("£12.50") == 1250
    assert readMoney("12") == 1200
    assert readMoney("") is None


def test_a_size_is_written_as_an_attribute_not_a_column(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    applyEdits(connection, "i1", {"sizeUk": "20"})

    row = connection.execute(
        "SELECT value, system, source, isPrimary FROM itemAttribute"
        " WHERE itemId = 'i1' AND attribute = 'size'"
    ).fetchone()
    assert (row["value"], row["system"], row["source"]) == ("20", "UK", "manual")
    assert row["isPrimary"] == 1


def test_clearing_a_size_removes_it(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    applyEdits(connection, "i1", {"sizeUk": "20"})
    applyEdits(connection, "i1", {"sizeUk": ""})

    assert currentValues(connection, "i1")["sizeUk"] == ""


def test_only_fields_that_actually_differ_are_written(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    made = applyEdits(connection, "i1", {"title": "Navy floral dress", "brand": "Whistles"})

    assert [field for field, _, _ in made] == ["Brand"]


def test_every_change_is_recorded_with_before_and_after(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    applyEdits(connection, "i1", {"price": "18.00"})

    row = connection.execute(
        "SELECT field, valueBefore, valueAfter FROM event WHERE subject = 'i1' AND action = 'edit'"
    ).fetchone()
    assert (row["field"], row["valueBefore"], row["valueAfter"]) == ("Price", "12.00", "18.00")


def test_an_edit_reaches_the_search_index(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    applyEdits(connection, "i1", {"sizeUk": "20", "colours": "Teal; Navy"})

    from sixgenbot.core.database import searchItems
    assert searchItems(connection, "teal") == ["i1"]


def test_checking_an_item_moves_it_off_the_list_and_never_puts_it_on_sale(tmp_path):
    """suggestedStatus never returns on_sale — being ready is not being listed."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    assert markChecked(connection, "i1") is True
    assert markChecked(connection, "i1") is False, "checking twice is not a second event"

    status = connection.execute("SELECT status FROM item WHERE itemId = 'i1'").fetchone()["status"]
    assert status != "on_sale"


def test_checking_does_not_disturb_an_item_that_is_already_sold(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", status="sold")

    markChecked(connection, "i1")

    status = connection.execute("SELECT status FROM item WHERE itemId = 'i1'").fetchone()["status"]
    assert status == "sold"


# --- the screens ------------------------------------------------------------

def test_the_list_shows_what_is_waiting_and_what_each_item_needs(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    page = client.get("/review").text
    assert "13-8 24" in page
    assert "1 items" in page or "1 item" in page
    assert "Needs" in page, "the row should say what is missing, in words"


def test_never_listed_is_its_own_list_because_that_is_the_backlog(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", dateListed=None)
    addItem(connection, "i2", "7-4-21", dateListed="2026-04-21")

    offline = client.get("/review?which=offline").text
    assert "13-8 24" in offline
    assert "7-4 21" not in offline


def test_items_are_listed_in_the_order_the_room_is_walked(tmp_path):
    """Column, then box, then item — not the order the characters fall in."""
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addItem(connection, "i2", "7-4-21")
    addItem(connection, "i3", "7-4-3")
    addItem(connection, "i4", "(no code) abc12345")

    page = client.get("/review").text
    order = [page.index(sku) for sku in ("7-4 3", "7-4 21", "13-8 24", "(no code) abc12345")]
    assert order == sorted(order)


def test_the_sku_is_shown_the_way_the_business_writes_it(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    page = client.get("/review").text
    assert "13-8 24" in page
    assert "13-8-24" not in page


def test_the_search_box_finds_an_item_by_its_sku(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addItem(connection, "i2", "7-4-21", title="Green wool coat")
    from sixgenbot.core.database import reindexItem
    reindexItem(connection, "i1")
    reindexItem(connection, "i2")

    page = client.get("/review?q=7-4").text
    assert "7-4 21" in page
    assert "13-8 24" not in page


def test_choosing_what_is_shown_decides_what_can_be_changed(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    reply = client.post(
        "/review/edit", data={"pick": "i1", "columns": "sku,sizeUk,price"}
    )
    assert "Size UK" in reply.text
    assert "Private notes" not in reply.text
    assert 'name="f:i1:sizeUk"' in reply.text


def test_saving_a_batch_writes_every_item(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    addItem(connection, "i2", "7-4-21")

    client.post("/review/save", data={
        "f:i1:sizeUk": "20",
        "f:i2:sizeUk": "12",
        "checked:i1": "yes",
        "checked:i2": "yes",
    }, follow_redirects=False)

    assert currentValues(connection, "i1")["sizeUk"] == "20"
    assert currentValues(connection, "i2")["sizeUk"] == "12"
    assert connection.execute(
        "SELECT COUNT(*) AS total FROM item WHERE verifiedAt IS NOT NULL"
    ).fetchone()["total"] == 2


def test_an_item_left_unticked_stays_on_the_list(tmp_path):
    """Saving a correction is not the same as saying it has been checked."""
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    client.post("/review/save", data={"f:i1:sizeUk": "20"}, follow_redirects=False)

    verified = connection.execute(
        "SELECT verifiedAt FROM item WHERE itemId = 'i1'"
    ).fetchone()["verifiedAt"]
    assert verified is None
    assert currentValues(connection, "i1")["sizeUk"] == "20"


def test_saving_nothing_ticked_says_so_rather_than_showing_an_empty_screen(tmp_path):
    client, _ = buildClient(tmp_path)
    reply = client.post("/review/edit", data={"columns": "sku,sizeUk"}, follow_redirects=True)
    assert "Tick the items" in reply.text


def test_an_empty_database_is_a_sentence_not_a_blank_table(tmp_path):
    client, _ = buildClient(tmp_path)
    page = client.get("/review").text
    assert "no items have been imported yet" in page
    assert "Traceback" not in page


def test_the_edit_screen_says_nothing_goes_live_from_it(tmp_path):
    """Rule 8: nothing writes to a live store from here."""
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    reply = client.post("/review/edit", data={"pick": "i1", "columns": "sizeUk"})
    assert "nothing goes on Vinted" in reply.text
