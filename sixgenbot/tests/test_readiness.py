"""What is missing, and what nobody has checked — the two different questions."""

from __future__ import annotations

import pytest

from sixgenbot.core.database import Database
from sixgenbot.core.readiness import (
    ItemFacts,
    factsFor,
    missingFor,
    needsChecking,
    recommendedFor,
    suggestedStatus,
    summarise,
)


def completeItem(**changes) -> ItemFacts:
    facts = ItemFacts(
        sku="13-8-24",
        title="Navy wool coat",
        description="Warm, barely worn.",
        brand="M&S",
        conditionNote="Very good",
        price=1250,
        imageCount=3,
        attributes={"size", "colour"},
        categories={"vinted"},
        verifiedAt="2026-09-15T10:00:00",
    )
    for name, value in changes.items():
        setattr(facts, name, value)
    return facts


def test_a_complete_checked_item_needs_nothing():
    facts = completeItem()
    assert missingFor(facts) == []
    assert not needsChecking(facts)
    assert summarise(facts) == "Ready."


def test_an_empty_item_needs_everything():
    missing = missingFor(ItemFacts())
    assert "a title" in missing
    assert "at least one photo" in missing
    assert "a price" in missing
    assert "a size" in missing


def test_one_missing_field_reads_as_a_sentence():
    assert summarise(completeItem(imageCount=0)) == "Needs at least one photo."


def test_several_missing_fields_read_as_a_sentence():
    facts = completeItem(imageCount=0, brand="")
    assert summarise(facts) == "Needs at least one photo and a brand."


def test_a_complete_but_unchecked_item_says_so():
    """The whole point of the second list: complete is not the same as checked."""
    facts = completeItem(verifiedAt=None)
    assert missingFor(facts) == []
    assert needsChecking(facts)
    assert summarise(facts) == "Everything is filled in, but nobody has checked it yet."


def test_a_price_of_zero_is_not_a_price():
    assert "a price" in missingFor(completeItem(price=0))
    assert "a price" in missingFor(completeItem(price=None))


def test_whitespace_is_not_a_title():
    assert "a title" in missingFor(completeItem(title="   "))


def test_recommendations_never_appear_as_missing():
    """D-103: never block an item for something that is only nice to have."""
    facts = completeItem(attributes={"size"})       # no colour, no measurements
    assert missingFor(facts) == []
    assert recommendedFor(facts) == ["a colour", "measurements"]


def test_an_internal_item_needs_far_less_than_a_vinted_listing():
    facts = ItemFacts(sku="13-8-24", title="Navy wool coat", price=1250)
    assert missingFor(facts, "internal") == []
    assert missingFor(facts, "vinted") != []


def test_an_unknown_platform_asks_for_nothing_rather_than_guessing():
    """eBay's rules are not known yet (Q16) — better silent than invented."""
    assert missingFor(completeItem(), "ebay") == []


def test_an_imported_item_is_never_put_straight_on_sale():
    """Whether something is on sale depends on a listing existing, not on looking tidy."""
    assert suggestedStatus(completeItem()) == "draft"
    assert suggestedStatus(completeItem(verifiedAt=None)) == "needs_info"
    assert suggestedStatus(ItemFacts()) == "needs_info"


def test_facts_are_read_back_from_the_database(tmp_path):
    database = Database(tmp_path / "db.sqlite")
    database.migrate()
    connection = database.connection()

    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, description, brand,"
        " conditionNote, price, dateAdded)"
        " VALUES ('i1', '13-8 24', 'needs_info', 'Navy wool coat', 'Warm.',"
        " 'M&S', 'Very good', 1250, date('now'))"
    )
    connection.execute(
        "INSERT INTO itemAttribute (itemId, attribute, value, system)"
        " VALUES ('i1', 'size', '12', 'UK')"
    )
    connection.execute(
        "INSERT INTO itemCategory (itemId, platform, categoryPath)"
        " VALUES ('i1', 'vinted', 'Women / Coats')"
    )

    facts = factsFor(connection, "i1")
    assert facts.title == "Navy wool coat"
    assert facts.attributes == {"size"}
    assert facts.categories == {"vinted"}
    assert missingFor(facts) == ["at least one photo"]
    assert needsChecking(facts), "nothing imported is checked until someone checks it"


def test_marking_an_item_checked_is_what_clears_it(tmp_path):
    database = Database(tmp_path / "db.sqlite")
    database.migrate()
    connection = database.connection()
    connection.execute(
        "INSERT INTO item (itemId, sku, status, title, description, brand,"
        " conditionNote, price, dateAdded)"
        " VALUES ('i1', '13-8 24', 'needs_info', 'Coat', 'Warm.', 'M&S',"
        " 'Very good', 1250, date('now'))"
    )
    connection.execute("INSERT INTO itemImage (itemId, position, filePath) VALUES ('i1', 1, 'a.jpg')")
    connection.execute("INSERT INTO itemAttribute (itemId, attribute, value) VALUES ('i1','size','12')")
    connection.execute("INSERT INTO itemCategory (itemId, platform, categoryPath) VALUES ('i1','vinted','x')")

    assert needsChecking(factsFor(connection, "i1"))

    connection.execute("UPDATE item SET verifiedAt = datetime('now') WHERE itemId = 'i1'")

    facts = factsFor(connection, "i1")
    assert not needsChecking(facts)
    assert summarise(facts) == "Ready."


def test_a_missing_item_is_not_an_error(tmp_path):
    database = Database(tmp_path / "db.sqlite")
    database.migrate()
    assert factsFor(database.connection(), "nothing-like-this") == ItemFacts()
