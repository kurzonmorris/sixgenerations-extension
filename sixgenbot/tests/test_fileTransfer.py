"""Uploading a spreadsheet and downloading a copy, without a terminal."""

from __future__ import annotations

import csv
import io

from fastapi.testclient import TestClient

from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.appLogging import setupLogging
from sixgenbot.core.moduleLoader import loadModules
from sixgenbot.core.webApp import Bot

HEADER = (
    "Id,Title,Description,Price,OriginalPrice,CostOfGoods,Brand,CategoryId,CategoryLabel,"
    "SizeId,SizeLabel,Condition,Color,Color2,Quantity,ShippingWeight,ShippingWeightUnit,"
    "ShippingHeight,ShippingWidth,ShippingLength,DomesticShippingPrice,WorldwideShippingPrice,"
    "FreeDomesticShipping,FreeWorldwideShipping,Tags,SKU,WhoMade,WhenMade,SmartPricing,"
    "SmartPricingPrice,AcceptOffers,IsAuction,AuctionStartingPrice,InternalNote,LastListedOn,"
    "Sold,Created,Labels,Photos"
)
ROW = (
    'a1,Navy floral dress UK20,"A dress.\n\nW405g\nB10-2 24",12.00,,,Jacques Vert,c1,'
    '"Clothing > Womenswear > Dresses",s1,XL,VeryGood,Navy,Teal,1,500.00,Grams,,,,,,,,,,,,'
    'False,,False,False,,,,,2026-04-21 13:11:27,,https://example.invalid/p1.jpg'
)
EXPORT = (HEADER + "\n" + ROW + "\n").encode("utf-8")


def buildClient(tmp_path):
    setupLogging(level="DEBUG")
    bot = Bot(loadConfig(tmp_path))
    bot.db.migrate()
    bot.modules = loadModules(bot)
    return TestClient(bot.buildApp()), bot


def test_the_page_offers_an_upload_and_a_download(tmp_path):
    client, _ = buildClient(tmp_path)
    page = client.get("/files").text
    assert 'type="file"' in page
    assert "/files/items.csv" in page
    assert "Files" in page


def test_uploading_a_spreadsheet_shows_what_it_would_do_first(tmp_path):
    """Nothing is imported by uploading — INTERFACE_PRINCIPLES and D-093."""
    client, bot = buildClient(tmp_path)

    reply = client.post(
        "/files/upload",
        files={"spreadsheet": ("listings.csv", EXPORT, "text/csv")},
        follow_redirects=True,
    )

    assert reply.status_code == 200
    assert "Nothing has been written" in reply.text
    assert "Import it" in reply.text
    assert bot.db.connection().execute("SELECT COUNT(*) FROM item").fetchone()[0] == 0


def test_the_import_button_actually_imports(tmp_path):
    client, bot = buildClient(tmp_path)
    client.post("/files/upload", files={"spreadsheet": ("listings.csv", EXPORT, "text/csv")})

    done = client.post("/files/import/listings.csv", follow_redirects=True)

    assert "1 new" in done.text
    assert bot.db.connection().execute("SELECT COUNT(*) FROM item").fetchone()[0] == 1


def test_a_file_that_is_not_a_csv_is_refused(tmp_path):
    client, bot = buildClient(tmp_path)
    reply = client.post(
        "/files/upload",
        files={"spreadsheet": ("photo.jpg", b"\xff\xd8\xff", "image/jpeg")},
        follow_redirects=True,
    )
    assert "not a CSV" in reply.text
    assert not list((tmp_path / "imports").glob("*")) if (tmp_path / "imports").exists() else True


def test_a_broken_spreadsheet_says_so_instead_of_breaking(tmp_path):
    client, _ = buildClient(tmp_path)
    reply = client.post(
        "/files/upload",
        files={"spreadsheet": ("rubbish.csv", b"this,is,not,an,export\n1,2,3,4,5\n", "text/csv")},
        follow_redirects=True,
    )
    assert reply.status_code == 200
    assert "could not be read" in reply.text
    assert "Traceback" not in reply.text


def test_a_filename_cannot_escape_the_imports_folder(tmp_path):
    client, _ = buildClient(tmp_path)
    client.post(
        "/files/upload",
        files={"spreadsheet": ("../../escape.csv", EXPORT, "text/csv")},
        follow_redirects=False,
    )
    assert (tmp_path / "imports" / "escape.csv").exists()
    assert not (tmp_path.parent / "escape.csv").exists()


def test_a_path_cannot_reach_outside_its_folder(tmp_path):
    """The guard itself, rather than one URL that happens to be rejected."""
    from sixgenbot.modules.fileTransfer.routes import insideFolder

    folder = tmp_path / "imports"
    folder.mkdir()
    (folder / "real.csv").write_text("Id\n", encoding="utf-8")
    (tmp_path / "secret.sqlite").write_text("not yours", encoding="utf-8")

    assert insideFolder(folder, "real.csv") is not None
    for attempt in ("../secret.sqlite", "../../etc/passwd", "/etc/passwd", "sub/../../secret.sqlite"):
        assert insideFolder(folder, attempt) is None, attempt


def test_the_database_is_never_served_as_a_download(tmp_path):
    client, _ = buildClient(tmp_path)
    for attempt in (
        "/files/preview/..%2Fsixgenbot.sqlite",
        "/files/backup/..%2Fsixgenbot.sqlite",
        "/files/preview/sixgenbot.sqlite",
    ):
        reply = client.get(attempt, follow_redirects=True)
        assert b"SQLite format" not in reply.content


def test_downloading_every_item_gives_a_spreadsheet(tmp_path):
    client, _ = buildClient(tmp_path)
    client.post("/files/upload", files={"spreadsheet": ("listings.csv", EXPORT, "text/csv")})
    client.post("/files/import/listings.csv")

    reply = client.get("/files/items.csv")

    assert reply.status_code == 200
    assert "attachment" in reply.headers["content-disposition"]
    rows = list(csv.DictReader(io.StringIO(reply.text)))
    assert len(rows) == 1
    assert rows[0]["sku"] == "10-2-24"
    assert rows[0]["price"] == "12.00", "pounds on the way out, pence inside"
    assert rows[0]["weightGrams"] == "405"
    assert rows[0]["colours"] == "Navy;Teal"
    assert rows[0]["colourMain"] == "Navy"


def test_the_download_can_be_narrowed_to_one_status(tmp_path):
    client, _ = buildClient(tmp_path)
    client.post("/files/upload", files={"spreadsheet": ("listings.csv", EXPORT, "text/csv")})
    client.post("/files/import/listings.csv")

    everything = list(csv.DictReader(io.StringIO(client.get("/files/items.csv").text)))
    sold = list(csv.DictReader(io.StringIO(client.get("/files/items.csv?status=sold").text)))

    assert len(everything) == 1 and len(sold) == 0


def test_nothing_in_the_export_hides_a_comma(tmp_path):
    """A comma inside a multi-value cell survives quoting and nothing else."""
    from sixgenbot.core.csvExport import _joined

    assert _joined(["Navy, dark", "White"]) == "Navy dark;White"
