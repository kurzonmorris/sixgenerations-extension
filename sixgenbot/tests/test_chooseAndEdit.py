"""Choosing items many ways, then editing them down one column.

Asked for on 2026-09-20: pick items by ticking them, or by what they are
missing, or by what a field contains, or by when they were added — and combine
those. Then change one thing on all of them without touching the mouse.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient

from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.appLogging import setupLogging
from sixgenbot.core.database import reindexItem
from sixgenbot.core.itemEdit import currentValues
from sixgenbot.core.itemQuery import MISSING, Filters, buildWhere, countItems, describe
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
           "price": 1200, "status": "needs_info", "dateAdded": "2026-09-20 11:00:00",
           "weightGrams": 400, "notes": ""}
    row.update(overrides)
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, description, brand, price,"
        " dateAdded, weightGrams, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (itemId, sku, row["status"], row["title"], row["description"], row["brand"],
         row["price"], row["dateAdded"], row["weightGrams"], row["notes"]))
    reindexItem(connection, itemId)
    return itemId


def addSize(connection, itemId, value="12"):
    connection.execute(
        "INSERT INTO itemAttribute (itemId, attribute, value, system, isPrimary)"
        " VALUES (?, 'size', ?, 'UK', 1)", (itemId, value))


def matching(connection, **kwargs) -> int:
    where, parameters, _ = buildWhere(connection, Filters(**kwargs))
    return countItems(connection, where, parameters)


# --- choosing by what is missing --------------------------------------------

def test_every_missing_choice_is_a_real_query(tmp_path):
    """Each one must run. A filter that throws is worse than one that finds nothing."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1")

    for name in MISSING:
        assert matching(connection, missing=name) >= 0


def test_items_with_no_brand_are_found(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", brand="")
    addItem(connection, "i2", "1-1-2", brand="Whistles")

    assert matching(connection, missing="brand") == 1


def test_items_with_no_size_are_found(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1")
    addItem(connection, "i2", "1-1-2")
    addSize(connection, "i2")

    assert matching(connection, missing="size") == 1


def test_a_price_of_zero_counts_as_no_price(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", price=0)
    addItem(connection, "i2", "1-1-2", price=None)
    addItem(connection, "i3", "1-1-3", price=1200)

    assert matching(connection, missing="price") == 2


# --- choosing by what a field contains --------------------------------------

def test_a_word_in_the_title(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", title="Green velvet jacket")
    addItem(connection, "i2", "1-1-2", title="Cotton shirt")

    assert matching(connection, titleHas="velvet") == 1


def test_a_word_in_the_title_ignores_capital_letters(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", title="Green Velvet jacket")

    assert matching(connection, titleHas="velvet") == 1


def test_a_word_in_the_private_notes(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", notes="small hole in the hem")
    addItem(connection, "i2", "1-1-2")

    assert matching(connection, notesHas="hole") == 1


def test_a_colour_is_matched_in_part_because_colours_are_free_text(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1")
    connection.execute(
        "INSERT INTO itemAttribute (itemId, attribute, value, isPrimary)"
        " VALUES ('i1', 'colour', 'Navy blue', 1)")

    assert matching(connection, colour="navy") == 1


# --- choosing by when an item arrived ---------------------------------------

def test_added_between_two_dates_includes_the_whole_last_day(tmp_path):
    """dateAdded holds a time. "up to the 21st" must not drop the 21st."""
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", dateAdded="2026-04-21 13:11:32")
    addItem(connection, "i2", "1-1-2", dateAdded="2026-04-22 09:00:00")

    assert matching(connection, addedFrom="2026-04-21", addedTo="2026-04-21") == 1


def test_a_time_can_be_given_as_well_as_a_date(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", dateAdded="2026-04-21 09:00:00")
    addItem(connection, "i2", "1-1-2", dateAdded="2026-04-21 18:00:00")

    assert matching(connection, addedFrom="2026-04-21 12:00:00") == 1


def test_added_in_the_last_so_many_days(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    recent = (date.today() - timedelta(days=2)).isoformat()
    old = (date.today() - timedelta(days=40)).isoformat()
    addItem(connection, "i1", "1-1-1", dateAdded=f"{recent} 10:00:00")
    addItem(connection, "i2", "1-1-2", dateAdded=f"{old} 10:00:00")

    assert matching(connection, addedDays="7") == 1


def test_a_days_box_with_words_in_it_is_ignored_rather_than_breaking(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1")

    assert matching(connection, addedDays="last week") == 1


# --- the other choices ------------------------------------------------------

def test_items_nobody_has_checked(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1")
    addItem(connection, "i2", "1-1-2")
    connection.execute("UPDATE item SET verifiedAt = '2026-09-20' WHERE itemId = 'i2'")

    assert matching(connection, checked="no") == 1
    assert matching(connection, checked="yes") == 1


def test_items_that_share_a_code_with_another_item(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1")
    addItem(connection, "i2", "1-1-1 #055f63")

    assert matching(connection, sharedCode="yes") == 1


# --- combining them ---------------------------------------------------------

def test_several_choices_narrow_the_set_together(tmp_path):
    _, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", brand="", title="Velvet jacket")
    addItem(connection, "i2", "1-1-2", brand="", title="Cotton shirt")
    addItem(connection, "i3", "1-1-3", brand="Whistles", title="Velvet coat")

    assert matching(connection, missing="brand", titleHas="velvet") == 1


def test_the_sentence_names_every_choice_in_words():
    sentence = describe(
        Filters(missing="brand", titleHas="velvet", addedDays="7", checked="no"), 12)
    assert sentence.startswith("With no brand"), "the first phrase is capitalised"
    assert "title containing “velvet”" in sentence
    assert "added in the last 7 days" in sentence
    assert "not checked yet" in sentence
    assert sentence.endswith("12 items.")


# --- the screens ------------------------------------------------------------

def test_the_table_offers_a_box_on_every_row_and_a_button_for_all_of_them(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "1-1-1")

    page = client.get("/table").text
    assert 'name="pick" value="i1"' in page
    assert "Work on the ticked items" in page
    assert 'name="useFilters" value="yes"' in page


def test_working_on_everything_that_matches_takes_the_filters_not_the_page(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    for n in range(1, 9):
        addItem(connection, f"i{n}", f"1-1-{n}", brand="" if n <= 5 else "Whistles")

    reply = client.post("/review/edit",
                        data={"useFilters": "yes", "missing": "brand", "only": "brand"})

    assert reply.text.count('name="f:') == 5, "only the five with no brand"


def test_a_batch_bigger_than_the_limit_says_so_plainly(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    for n in range(1, 46):
        addItem(connection, f"i{n}", f"1-1-{n}", brand="")

    reply = client.post("/review/edit", data={"useFilters": "yes", "missing": "brand"})

    assert "first 40 of 45" in reply.text


def test_one_column_holds_more_than_one_card_at_a_time_does(tmp_path):
    """A column is one box an item, so many more fit before it becomes a wall."""
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    for n in range(1, 61):
        addItem(connection, f"i{n}", f"1-1-{n}", brand="")

    cards = client.post("/review/edit", data={"useFilters": "yes", "missing": "brand"})
    column = client.post("/review/edit",
                         data={"useFilters": "yes", "missing": "brand", "only": "brand"})

    assert "first 40 of 60" in cards.text
    assert column.text.count('name="f:') == 60, "all sixty fit in one column"


def test_a_column_shows_that_one_thing_and_nothing_else(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "1-1-1")

    reply = client.post("/review/edit",
                        data={"pick": "i1", "columns": "brand,price,title", "only": "brand"})

    assert 'name="f:i1:brand"' in reply.text
    assert 'name="f:i1:price"' not in reply.text
    assert 'name="f:i1:title"' not in reply.text


def test_the_boxes_in_a_column_are_in_item_order_so_tab_walks_down_them(tmp_path):
    """Tab follows the order the page is written in. Nothing else is needed."""
    import re

    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    for n in (3, 1, 2):
        addItem(connection, f"i{n}", f"1-1-{n}", brand="")

    reply = client.post("/review/edit",
                        data={"useFilters": "yes", "missing": "brand", "only": "brand"})

    order = re.findall(r'name="f:(i\d):brand"', reply.text)
    assert order == ["i1", "i2", "i3"], "storage order, one after another"


def test_every_box_in_a_column_says_which_item_it_is_for(tmp_path):
    """Forty boxes all labelled "Brand" tell a screen reader nothing."""
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "13-8-24")

    reply = client.post("/review/edit", data={"pick": "i1", "only": "brand"})
    assert "Brand for 13-8 24" in reply.text


def test_a_column_can_be_changed_without_losing_the_chosen_items(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1")
    addItem(connection, "i2", "1-1-2")

    reply = client.post("/review/edit", data={"pick": ["i1", "i2"], "only": "brand"})
    assert 'name="pick" value="i1"' in reply.text
    assert 'name="pick" value="i2"' in reply.text


def test_saving_returns_to_the_screen_you_came_from(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "1-1-1")

    save = client.post("/review/save",
                       data={"f:i1:brand": "Whistles", "back": "/table?missing=brand"},
                       follow_redirects=False)

    assert save.headers["location"].startswith("/table?missing=brand&message=")


def test_saving_a_column_changes_only_that_column(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", brand="", price=1200)
    addItem(connection, "i2", "1-1-2", brand="", price=1200)

    client.post("/review/save", data={"f:i1:brand": "Whistles", "f:i2:brand": "Jigsaw"},
                follow_redirects=False)

    assert currentValues(connection, "i1")["brand"] == "Whistles"
    assert currentValues(connection, "i2")["brand"] == "Jigsaw"
    assert currentValues(connection, "i1")["price"] == "12.00", "the price was not touched"


def test_an_item_leaves_the_batch_once_it_is_no_longer_missing_anything(tmp_path):
    """The list shrinks as you work. That is what makes a big batch finishable."""
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", brand="")
    addItem(connection, "i2", "1-1-2", brand="")

    assert matching(connection, missing="brand") == 2
    client.post("/review/save", data={"f:i1:brand": "Whistles"}, follow_redirects=False)
    assert matching(connection, missing="brand") == 1


def test_nothing_sits_between_two_boxes_in_a_column(tmp_path):
    """One press of Tab per item, not two.

    A tick box on each row would be a keyboard stop between the two boxes Tab is
    meant to join, so the whole batch is marked together at the bottom instead.
    """
    import re

    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    for n in range(1, 5):
        addItem(connection, f"i{n}", f"1-1-{n}", brand="")

    reply = client.post("/review/edit",
                        data={"useFilters": "yes", "missing": "brand", "only": "brand"})
    body = reply.text[reply.text.index('action="/review/save"'):]

    # Everything a keyboard can land on, not only the boxes. A <details> fold
    # and a link are both stops, and a browser proved that the hard way.
    stops = re.findall(
        r"<(input|textarea|select|button|a|summary)\b([^>]*)>", body)
    landable = []
    for tag, rest in stops:
        if 'type="hidden"' in rest or "disabled" in rest:
            continue
        name = re.search(r'name="([^"]+)"', rest)
        landable.append(name.group(1) if name else tag)

    assert landable[:4] == [f"f:i{n}:brand" for n in range(1, 5)], (
        f"something sits between two boxes: {landable[:6]}")


def test_a_card_still_has_its_own_checked_box(tmp_path):
    """One item at a time is different: there you have looked at the whole thing."""
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "1-1-1")

    reply = client.post("/review/edit", data={"pick": "i1", "columns": "brand"})
    assert 'name="checked:i1"' in reply.text


def test_a_column_can_mark_the_whole_batch_as_checked_in_one_go(tmp_path):
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", brand="")
    addItem(connection, "i2", "1-1-2", brand="")

    client.post("/review/save", data={"f:i1:brand": "Whistles", "f:i2:brand": "Jigsaw",
                                      "checkAll": "yes"}, follow_redirects=False)

    assert connection.execute(
        "SELECT COUNT(*) AS total FROM item WHERE verifiedAt IS NOT NULL"
    ).fetchone()["total"] == 2


def test_a_column_does_not_mark_anything_checked_unless_asked(tmp_path):
    """Correcting one thing is not the same as checking the whole item."""
    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", brand="")

    client.post("/review/save", data={"f:i1:brand": "Whistles"}, follow_redirects=False)

    assert connection.execute(
        "SELECT verifiedAt FROM item WHERE itemId = 'i1'").fetchone()["verifiedAt"] is None


# --- what the boxes actually contain ----------------------------------------
#
# Found 2026-09-20 in a real browser. Every box on the edit screen was empty,
# because `item.values` in Jinja is the dictionary's own `.values` method, not
# the key called "values". Saving an untouched form would have written an empty
# string over every field on screen. These tests read the rendered HTML, which
# is the only place the fault was visible.

def test_a_box_holds_the_value_the_item_already_has(tmp_path):
    import re

    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "1-1-1", brand="Marks & Spencer")

    reply = client.post("/review/edit", data={"pick": "i1", "columns": "brand"})
    box = re.search(r'name="f:i1:brand"\s+value="([^"]*)"', reply.text)

    assert box is not None, "there should be a brand box"
    assert box.group(1) == "Marks &amp; Spencer", "the box must not be empty"


def test_every_box_on_a_card_holds_its_value(tmp_path):
    import re

    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "1-1-1", brand="Whistles", title="Velvet coat")

    reply = client.post("/review/edit", data={"pick": "i1", "columns": "brand,title,price"})

    assert re.search(r'name="f:i1:brand"\s+value="Whistles"', reply.text)
    assert re.search(r'name="f:i1:title"\s+value="Velvet coat"', reply.text)
    assert re.search(r'name="f:i1:price"\s+value="12.00"', reply.text)


def test_saving_the_page_untouched_changes_nothing(tmp_path):
    """The test that would have caught it. Open the editor, save, change nothing."""
    import html as htmlLib
    import re

    client, bot = buildClient(tmp_path)
    connection = bot.db.connection()
    addItem(connection, "i1", "1-1-1", brand="Marks & Spencer", title="Velvet coat")
    before = currentValues(connection, "i1")

    page = client.post("/review/edit", data={"pick": "i1", "columns": "brand,title,price"}).text
    sending = {htmlLib.unescape(name): htmlLib.unescape(value) for name, value in
               re.findall(r'name="(f:[^"]+)"\s+value="([^"]*)"', page)}
    client.post("/review/save", data=sending, follow_redirects=False)

    assert currentValues(connection, "i1") == before
    assert connection.execute(
        "SELECT COUNT(*) AS total FROM event WHERE action = 'edit'"
    ).fetchone()["total"] == 0, "an untouched save must write no history either"


def test_the_column_says_what_the_value_was(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "1-1-1", brand="Whistles")

    reply = client.post("/review/edit", data={"pick": "i1", "only": "brand"})
    assert "was Whistles" in reply.text


def test_a_column_row_says_what_else_the_item_holds(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "1-1-1", brand="Whistles", title="Velvet coat")

    reply = client.post("/review/edit", data={"pick": "i1", "only": "price"})
    assert "Velvet coat" in reply.text
    assert "Whistles" in reply.text, "the other fields are readable while you type"


def test_one_item_is_not_called_one_items(tmp_path):
    client, bot = buildClient(tmp_path)
    addItem(bot.db.connection(), "i1", "1-1-1")

    reply = client.post("/review/edit", data={"pick": "i1", "columns": "brand"})
    assert "Working on 1 item" in reply.text
    assert "1 items" not in reply.text
    assert "Save it" in reply.text, "not \"Save all 1\""
