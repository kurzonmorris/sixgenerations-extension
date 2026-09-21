"""Reading the Vinted wardrobe into the database, without undoing corrections."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.appLogging import setupLogging
from sixgenbot.core.database import reindexItem
from sixgenbot.core.moduleLoader import loadModules
from sixgenbot.core.vintedRead import applyRead, planRead
from sixgenbot.core.webApp import Bot


def buildClient(tmp_path):
    setupLogging(level="DEBUG")
    bot = Bot(loadConfig(tmp_path))
    bot.db.migrate()
    bot.modules = loadModules(bot)
    return TestClient(bot.buildApp()), bot


def addItem(connection, itemId, sku, **overrides):
    row = {"title": "Navy floral dress", "description": "A dress.", "brand": "Jacques Vert",
           "price": 1200, "status": "draft", "conditionNote": "Very good"}
    row.update(overrides)
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, description, brand, price, dateAdded,"
        " conditionNote) VALUES (?, ?, ?, ?, ?, ?, ?, '2026-09-21', ?)",
        (itemId, sku, row["status"], row["title"], row["description"], row["brand"],
         row["price"], row["conditionNote"]))
    reindexItem(connection, itemId)
    return itemId


def listing(sku="13-8-24", **overrides):
    read = {"sourceId": "900001", "storageCode": sku, "title": "Navy floral dress",
            "description": f"A dress. {sku}", "price": 12.0, "brand": "Jacques Vert",
            "size": "UK 20", "condition": "Very good", "status": "active",
            "url": "https://www.vinted.co.uk/items/900001"}
    read.update(overrides)
    return read


# --- matching ---------------------------------------------------------------

def test_a_listing_is_matched_by_the_sku_in_its_description(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    plan = planRead(connection, [listing()])
    assert len(plan.linked) == 1
    assert plan.linked[0]["itemId"] == "i1"


def test_a_listing_already_known_is_matched_by_its_vinted_id(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    connection.execute(
        "INSERT INTO listing (itemId, platform, externalId, state)"
        " VALUES ('i1', 'vinted', '900001', 'live')")

    plan = planRead(connection, [listing(sku="")])
    assert len(plan.alreadyLinked) == 1


def test_a_listing_with_no_sku_is_never_matched_by_its_title(tmp_path):
    """Two garments with the same title are common here. A wrong match is worse."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", title="Navy floral dress")

    plan = planRead(connection, [listing(sku="", sourceId="", title="Navy floral dress")])
    assert plan.linked == [] and plan.newItems == []
    assert len(plan.unmatchable) == 1


def test_a_listing_with_a_sku_we_do_not_hold_is_a_new_item(tmp_path):
    _, bot = buildClient(tmp_path)
    plan = planRead(bot.db.connection(), [listing(sku="7-4-21")])
    assert len(plan.newItems) == 1


# --- the rule that matters --------------------------------------------------

def test_a_read_never_writes_over_a_field_we_already_have(tmp_path):
    """The catalogue came down because Vinted showed sizes wrongly."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", brand="Whistles")

    applyRead(connection, [listing(brand="Jacques Vert")], dryRun=False)

    assert connection.execute(
        "SELECT brand FROM item WHERE itemId='i1'").fetchone()["brand"] == "Whistles"


def test_a_difference_is_reported_rather_than_hidden(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", brand="Whistles")

    plan = planRead(connection, [listing(brand="Jacques Vert")])
    brands = [d for d in plan.differences if d.field == "brand"]
    assert len(brands) == 1
    assert (brands[0].ours, brands[0].theirs) == ("Whistles", "Jacques Vert")


def test_the_sku_on_the_end_is_not_counted_as_a_difference(tmp_path):
    """Vinted carries the SKU and our copy may not.

    Comparing plainly called every listing different and buried the real
    differences under a thousand false ones.
    """
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", description="A navy dress.")

    plan = planRead(connection, [listing(description="A navy dress.\n\n13-8 24")])

    assert [d.field for d in plan.differences] == []


def test_a_blank_is_filled_in_because_nothing_is_lost(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", brand="")

    applyRead(connection, [listing(brand="Jacques Vert")], dryRun=False)

    assert connection.execute(
        "SELECT brand FROM item WHERE itemId='i1'").fetchone()["brand"] == "Jacques Vert"


# --- what it writes ---------------------------------------------------------

def test_a_dry_run_writes_nothing(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", brand="")

    applyRead(connection, [listing()], dryRun=True)

    assert connection.execute("SELECT COUNT(*) AS n FROM listing").fetchone()["n"] == 0
    assert connection.execute(
        "SELECT brand FROM item WHERE itemId='i1'").fetchone()["brand"] == ""


def test_the_listing_address_and_price_are_written(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    applyRead(connection, [listing(price=18.5)], dryRun=False)

    row = connection.execute("SELECT * FROM listing WHERE itemId='i1'").fetchone()
    assert row["externalId"] == "900001"
    assert row["url"] == "https://www.vinted.co.uk/items/900001"
    assert row["price"] == 1850
    assert row["state"] == "live"


def test_a_sale_on_vinted_is_carried_across(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", status="on_sale")

    applyRead(connection, [listing(status="sold")], dryRun=False)

    row = connection.execute("SELECT status, dateSold FROM item WHERE itemId='i1'").fetchone()
    assert row["status"] == "sold"
    assert row["dateSold"] is not None


def test_a_listing_that_has_gone_is_marked_ended_not_deleted(tmp_path):
    """Nothing is ever deleted. Rows change state."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    connection.execute(
        "INSERT INTO listing (itemId, platform, externalId, state)"
        " VALUES ('i1', 'vinted', '900001', 'live')")

    applyRead(connection, [], dryRun=False)

    row = connection.execute("SELECT state, endedAt FROM listing WHERE itemId='i1'").fetchone()
    assert row["state"] == "ended"
    assert row["endedAt"] is not None


def test_a_new_item_is_created_with_its_listing(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()

    applyRead(connection, [listing(sku="7-4-21")], dryRun=False)

    item = connection.execute("SELECT * FROM item WHERE sku='7-4-21'").fetchone()
    assert item is not None
    assert item["status"] == "on_sale"
    assert connection.execute(
        "SELECT COUNT(*) AS n FROM listing WHERE itemId=?", (item["itemId"],)
    ).fetchone()["n"] == 1


def test_reading_twice_does_not_make_two_listings(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    applyRead(connection, [listing()], dryRun=False)
    applyRead(connection, [listing(price=15.0)], dryRun=False)

    rows = connection.execute("SELECT price FROM listing WHERE itemId='i1'").fetchall()
    assert len(rows) == 1 and rows[0]["price"] == 1500


def test_every_change_a_read_makes_is_written_down(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24", brand="")

    applyRead(connection, [listing()], dryRun=False)

    assert connection.execute(
        "SELECT COUNT(*) AS n FROM event WHERE actor='vinted'").fetchone()["n"] >= 1


# --- the screens ------------------------------------------------------------

def test_a_read_that_arrives_changes_nothing(tmp_path):
    """The dry-run rule doing double duty: an unexpected POST cannot alter data."""
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24", brand="")

    reply = client.post("/vinted/read", json={"items": [listing()]})

    assert reply.status_code == 200
    assert reply.json()["nothingWritten"] is True
    assert bot.db.connection().execute(
        "SELECT COUNT(*) AS n FROM listing").fetchone()["n"] == 0


def test_the_read_is_kept_so_it_can_be_looked_at(tmp_path):
    client, bot = buildClient(tmp_path)
    reply = client.post("/vinted/read", json={"items": [listing()]})

    stored = reply.json()["stored"]
    assert (bot.config.dataDir / "reads" / stored).is_file()
    assert "See what it would do" in client.get("/vinted").text


def test_a_read_that_cannot_be_understood_is_a_sentence_not_a_traceback(tmp_path):
    client, _ = buildClient(tmp_path)
    reply = client.post("/vinted/read", content=b"this is not json")

    assert reply.status_code == 400
    assert "could not be understood" in reply.json()["error"]


def test_the_plan_page_says_nothing_has_been_written(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24", brand="Whistles")
    stored = client.post("/vinted/read", json={"items": [listing(brand="Other")]}).json()["stored"]

    page = client.get(f"/vinted/plan/{stored}").text
    assert "Nothing has been written" in page
    assert "kept" in page
    assert "Whistles" in page


def test_applying_from_the_page_writes_it(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")
    stored = client.post("/vinted/read", json={"items": [listing()]}).json()["stored"]

    client.post(f"/vinted/apply/{stored}", follow_redirects=False)

    assert connection.execute("SELECT COUNT(*) AS n FROM listing").fetchone()["n"] == 1


def test_a_read_name_cannot_escape_its_folder(tmp_path):
    """Two guards. The framework rejects a path with slashes in it before the
    handler runs; `insideFolder` catches anything that does reach the handler."""
    from sixgenbot.modules.vintedSync.routes import insideFolder, readsFolder

    client, bot = buildClient(tmp_path)
    secret = bot.config.dataDir / "secrets.toml"
    secret.write_text("token = 'nobody should see this'")
    folder = readsFolder(bot)

    assert insideFolder(folder, "../secrets.toml") is None
    assert insideFolder(folder, "/etc/passwd") is None

    reply = client.get("/vinted/plan/..%2Fsecrets.toml", follow_redirects=True)
    assert "nobody should see this" not in reply.text


def test_a_saved_file_can_be_uploaded_instead(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")
    raw = json.dumps({"items": [listing()]}).encode()

    reply = client.post("/vinted/upload", files={"wardrobe": ("read.json", raw, "application/json")},
                        follow_redirects=True)

    assert "Nothing has been written" in reply.text


# --- shared codes -----------------------------------------------------------
#
# 639 items share a code. The importer marks the later one "11-1-26 #f26f36",
# and Vinted only ever carries the plain code. Found 2026-09-21 against the real
# catalogue: matching on `sku = ?` alone missed every suffixed item and would
# have created all 324 of them again as duplicates.

def test_a_suffixed_item_is_matched_by_its_plain_code(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "11-1-26 #f26f36")

    plan = planRead(connection, [listing(sku="11-1-26")])

    assert plan.newItems == [], "it must not be created again"
    assert len(plan.linked) == 1
    assert plan.linked[0]["itemId"] == "i1"


def test_a_code_held_by_two_garments_is_never_guessed(tmp_path):
    """Nothing can tell them apart, so a person decides. A wrong match is worse."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "11-1-26")
    addItem(connection, "i2", "11-1-26 #f26f36")

    plan = planRead(connection, [listing(sku="11-1-26")])

    assert len(plan.ambiguous) == 1
    assert plan.linked == [] and plan.newItems == []


def test_an_ambiguous_listing_writes_nothing(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "11-1-26")
    addItem(connection, "i2", "11-1-26 #f26f36")

    applyRead(connection, [listing(sku="11-1-26")], dryRun=False)

    assert connection.execute("SELECT COUNT(*) AS n FROM listing").fetchone()["n"] == 0
    assert connection.execute("SELECT COUNT(*) AS n FROM item").fetchone()["n"] == 2


def test_one_already_known_listing_settles_a_shared_code(tmp_path):
    """The Vinted id is checked first, so a pair sorts itself out once linked."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "11-1-26")
    addItem(connection, "i2", "11-1-26 #f26f36")
    connection.execute("INSERT INTO listing (itemId, platform, externalId, state)"
                       " VALUES ('i2', 'vinted', '900001', 'live')")

    plan = planRead(connection, [listing(sku="11-1-26")])

    assert plan.ambiguous == []
    assert len(plan.alreadyLinked) == 1
    assert plan.alreadyLinked[0]["itemId"] == "i2"
    assert plan.alreadyLinked[0]["itemId"] == "i2"


# --- linking by hand --------------------------------------------------------
#
# Measured on the real catalogue: of 1,137 listed items, only 139 match on the
# code alone. 377 have no code at the end and 621 carry a code two garments
# share. Linking is therefore the main job of the first read — and each one is
# done once, because the Vinted listing id settles it for good.

def test_a_listing_can_be_linked_to_an_item_by_hand(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "13-8-24")

    client.post("/vinted/link", data={"sourceId": "900001", "sku": "13-8 24",
                                      "url": "https://www.vinted.co.uk/items/900001"},
                follow_redirects=False)

    row = connection.execute("SELECT * FROM listing WHERE itemId='i1'").fetchone()
    assert row["externalId"] == "900001"
    assert row["state"] == "live"


def test_a_hand_link_settles_it_so_a_later_read_never_asks_again(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "11-1-26")
    addItem(connection, "i2", "11-1-26 #f26f36")

    ambiguous = planRead(connection, [listing(sku="11-1-26")]).ambiguous
    assert len(ambiguous) == 1
    assert [c["itemId"] for c in ambiguous[0]["candidates"]] == ["i1", "i2"], (
        "the page must offer both garments, because the code cannot settle it")

    client.post("/vinted/link", data={"sourceId": "900001", "itemId": "i2"},
                follow_redirects=False)

    plan = planRead(connection, [listing(sku="11-1-26")])
    assert plan.ambiguous == []
    assert len(plan.alreadyLinked) == 1
    assert plan.alreadyLinked[0]["itemId"] == "i2"


def test_linking_to_a_sku_that_does_not_exist_says_so(tmp_path):
    client, _ = buildClient(tmp_path)
    reply = client.post("/vinted/link", data={"sourceId": "900001", "sku": "99-9 9"},
                        follow_redirects=True)
    assert "No item has that SKU" in reply.text


def test_linking_to_a_shared_sku_refuses_rather_than_guessing(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "11-1-26")
    addItem(connection, "i2", "11-1-26 #f26f36")

    reply = client.post("/vinted/link", data={"sourceId": "900001", "sku": "11-1 26"},
                        follow_redirects=True)
    assert "Two items share that SKU" in reply.text


def test_nonsense_typed_as_a_sku_is_a_sentence(tmp_path):
    client, _ = buildClient(tmp_path)
    reply = client.post("/vinted/link", data={"sourceId": "900001", "sku": "not a code"},
                        follow_redirects=True)
    assert "Type a SKU" in reply.text
    assert "Traceback" not in reply.text


def test_the_confirmation_uses_the_sku_the_business_writes(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    reply = client.post("/vinted/link", data={"sourceId": "900001", "itemId": "i1"},
                        follow_redirects=True)
    assert "13-8 24" in reply.text
    assert "13-8-24" not in reply.text
