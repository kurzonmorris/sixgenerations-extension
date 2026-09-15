"""Reading the Crosslist export. Shapes taken from the real file.

docs/CROSSLIST_EXPORT.md has the analysis these cases come from.
"""

from __future__ import annotations

import pytest

from sixgenbot.core.crosslistImport import (
    importExport,
    planRow,
    price,
    readRawCode,
    readWeight,
    statusFor,
)
from sixgenbot.core.database import Database

HEADER = (
    "Id,Title,Description,Price,OriginalPrice,CostOfGoods,Brand,CategoryId,CategoryLabel,"
    "SizeId,SizeLabel,Condition,Color,Color2,Quantity,ShippingWeight,ShippingWeightUnit,"
    "ShippingHeight,ShippingWidth,ShippingLength,DomesticShippingPrice,WorldwideShippingPrice,"
    "FreeDomesticShipping,FreeWorldwideShipping,Tags,SKU,WhoMade,WhenMade,SmartPricing,"
    "SmartPricingPrice,AcceptOffers,IsAuction,AuctionStartingPrice,InternalNote,LastListedOn,"
    "Sold,Created,Labels,Photos"
)


def exportFile(tmp_path, *rows) -> "Path":
    path = tmp_path / "listings.csv"
    path.write_text(HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


def row(id="a1", title="Navy floral dress UK20", description="A dress.\n\nW405g\nB10-2 24",
        price="12.00", brand="Jacques Vert", category="Clothing > Womenswear > Dresses",
        size="XL", condition="VeryGood", colour="Navy", colour2="", listed="", sold="",
        created="2026-04-21 13:11:27", photos="https://example.invalid/p1.jpg"):
    quoted = description.replace('"', '""')
    return (
        f'{id},{title},"{quoted}",{price},,,{brand},cat-id,"{category}",size-id,{size},'
        f'{condition},{colour},{colour2},1,500.00,Grams,,,,,,,,,,,,False,,False,False,,,'
        f'{listed},{sold},{created},,{photos}'
    )


# --- the bits hidden in the description ------------------------------------

def test_the_weight_comes_out_of_the_description():
    """The ShippingWeight column is defaults nobody set — 16.00 on 847 rows."""
    assert readWeight("A dress.\n\nW405g\nB10-2 24") == 405
    assert readWeight("W65g") == 65
    assert readWeight("W 220 g.") == 220
    assert readWeight("no weight here") is None


def test_the_raw_code_is_kept_exactly_as_written():
    """B just means box. Kept for continuity, ignored when matching."""
    assert readRawCode("A dress.\n\nW405g\nB10-2 24") == "B10-2 24"
    assert readRawCode("A toy.\n\nW200g\nC01") == "C01"
    assert readRawCode("A file.\n\nW90g\nB2-1") == "B2-1"


def test_a_description_ending_in_prose_has_no_code():
    """405 items have none — jackets, toys and books that do not fit a box."""
    assert readRawCode("Dan Dare Annual 1979. Hardback, some foxing to the pages.") == ""
    assert readRawCode("A dress.\n\nW490g") == ""


def test_a_size_range_in_the_text_is_never_read_as_a_location():
    assert readRawCode("Stretchy, fits 10-12 nicely") == ""


def test_money_is_converted_to_pence():
    assert price("12.00") == 1200
    assert price("1.50") == 150
    assert price("") is None


# --- what a row becomes -----------------------------------------------------

def test_a_row_becomes_an_item():
    planned = planRow({
        "Id": "a1", "Title": "Navy floral dress UK20",
        "Description": "Beautiful navy dress.\n\nW405g\nB10-2 24",
        "Price": "12.00", "Brand": "Jacques Vert", "Condition": "VeryGood",
        "CategoryLabel": "Clothing > Womenswear > Dresses", "SizeLabel": "XL",
        "Color": "Navy", "Color2": "Teal", "Created": "2026-04-21 13:11:27",
        "LastListedOn": "", "Sold": "", "Photos": "https://example.invalid/1.jpg|https://example.invalid/2.jpg",
    })
    assert planned.sku == "10-2-24"
    assert planned.legacyCode == "B10-2 24"
    assert planned.price == 1200
    assert planned.weightGrams == 405
    assert planned.colours == ["Navy", "Teal"]
    assert len(planned.photos) == 2
    assert planned.conditionNote == "Very good"


def test_nothing_is_ever_imported_as_on_sale():
    """What is live is Vinted's to say. A CSV is out of date the moment it is written."""
    assert statusFor({"Sold": "", "LastListedOn": "2026-03-16 13:10:51"}) == "needs_info"
    assert statusFor({"Sold": "2026-05-10 11:45:43"}) == "sold"


# --- importing ---------------------------------------------------------------

def freshDatabase(tmp_path):
    database = Database(tmp_path / "db.sqlite")
    database.migrate()
    return database


def test_a_dry_run_writes_nothing(tmp_path):
    database = freshDatabase(tmp_path)
    counts = importExport(database.connection(), exportFile(tmp_path, row()), dryRun=True)

    assert counts.read == 1 and counts.created == 1
    assert database.connection().execute("SELECT COUNT(*) FROM item").fetchone()[0] == 0


def test_applying_it_creates_the_item_and_everything_under_it(tmp_path):
    database = freshDatabase(tmp_path)
    connection = database.connection()
    importExport(connection, exportFile(tmp_path, row(colour2="Teal")), dryRun=False)

    item = connection.execute("SELECT * FROM item").fetchone()
    assert item["sku"] == "10-2-24"
    assert item["legacyCode"] == "B10-2 24"
    assert item["weightGrams"] == 405
    assert item["price"] == 1200
    assert item["status"] == "needs_info"
    assert item["verifiedAt"] is None, "nothing imported is checked until someone checks it"

    colours = [r["value"] for r in connection.execute(
        "SELECT value FROM itemAttribute WHERE attribute='colour' ORDER BY position")]
    assert colours == ["Navy", "Teal"]
    assert connection.execute("SELECT COUNT(*) FROM itemCategory").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM itemImage").fetchone()[0] == 1


def test_running_it_twice_changes_nothing(tmp_path):
    database = freshDatabase(tmp_path)
    connection = database.connection()
    path = exportFile(tmp_path, row(), row(id="a2", title="Another dress"))

    importExport(connection, path, dryRun=False)
    second = importExport(connection, path, dryRun=False)

    assert second.created == 0
    assert second.unchanged == 2
    assert connection.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 2


def test_a_changed_title_updates_rather_than_duplicates(tmp_path):
    database = freshDatabase(tmp_path)
    connection = database.connection()

    importExport(connection, exportFile(tmp_path, row()), dryRun=False)
    importExport(connection, exportFile(tmp_path, row(title="Navy floral dress UK22")), dryRun=False)

    assert connection.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 1
    assert connection.execute("SELECT title FROM item").fetchone()[0] == "Navy floral dress UK22"


def test_an_item_with_no_code_is_imported_and_flagged_not_skipped(tmp_path):
    """Jackets, toys and books that do not fit a box. A real state, not a mistake."""
    database = freshDatabase(tmp_path)
    connection = database.connection()
    counts = importExport(
        connection,
        exportFile(tmp_path, row(description="Dan Dare Annual 1979. Hardback.")),
        dryRun=False,
    )

    assert counts.withoutCode == 1
    item = connection.execute("SELECT sku, importNote FROM item").fetchone()
    assert "no SKU" in item["importNote"]
    assert item["sku"], "it still needs something unique to be stored under"


def test_two_items_sharing_a_code_both_survive(tmp_path):
    """Usually a garment returned and relisted. Neither row is merged away."""
    database = freshDatabase(tmp_path)
    connection = database.connection()
    counts = importExport(
        connection,
        exportFile(
            tmp_path,
            row(id="a1", title="Black triangle brief"),
            row(id="a2", title="Black joggers size S"),
        ),
        dryRun=False,
    )

    assert counts.sharedCode == 2
    assert connection.execute("SELECT COUNT(*) FROM item").fetchone()[0] == 2
    notes = [r["importNote"] for r in connection.execute("SELECT importNote FROM item")]
    assert all("more than one item" in note for note in notes)


def test_every_import_leaves_a_trace_in_the_item_history(tmp_path):
    """Kurzon asked for a date against every action on an item."""
    database = freshDatabase(tmp_path)
    connection = database.connection()
    importExport(connection, exportFile(tmp_path, row()), dryRun=False)

    events = list(connection.execute("SELECT actor, action, happenedAt FROM event"))
    assert len(events) == 1
    assert events[0]["actor"] == "import"
    assert events[0]["action"] == "imported"
    assert events[0]["happenedAt"]


def test_an_imported_item_can_be_found_by_searching(tmp_path):
    from sixgenbot.core.database import searchItems

    database = freshDatabase(tmp_path)
    connection = database.connection()
    importExport(connection, exportFile(tmp_path, row(description="Crushed velvet.\n\nW405g\nB10-2 24")), dryRun=False)

    assert searchItems(connection, "velvet")
    assert searchItems(connection, "10-2")
