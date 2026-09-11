from fastapi.testclient import TestClient

from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.appLogging import setupLogging
from sixgenbot.core.moduleLoader import loadModules
from sixgenbot.core.webApp import Bot


def buildClient(tmp_path, disabled=None):
    setupLogging(level="DEBUG")
    bot = Bot(loadConfig(tmp_path))
    bot.db.migrate()
    bot.modules = loadModules(bot, disabled=disabled)
    return TestClient(bot.buildApp()), bot


def test_the_status_page_says_it_is_running(tmp_path):
    client, _ = buildClient(tmp_path)
    page = client.get("/")
    assert page.status_code == 200
    assert "sixgenbot is running" in page.text
    assert "Nothing needs fixing" in page.text
    assert "systemStatus" in page.text


def test_the_status_page_says_the_database_is_ready_and_empty(tmp_path):
    client, _ = buildClient(tmp_path)
    body = client.get("/").text
    assert "ready and empty" in body
    assert "schema v1" in body


def test_the_status_page_counts_what_is_actually_there(tmp_path):
    client, bot = buildClient(tmp_path)
    bot.db.connection().execute(
        "INSERT INTO item (itemId, sku, status, title, dateAdded)"
        " VALUES ('i1', '13-8 24', 'on_sale', 'Navy wool coat', date('now'))"
    )
    body = client.get("/").text
    assert "ready and empty" not in body
    assert "On sale" in body


def test_the_nightly_backup_is_scheduled(tmp_path):
    _, bot = buildClient(tmp_path)
    assert [job.name for job in bot.scheduler.jobs] == ["nightlyBackup"]
    assert bot.scheduler.jobs[0].when == "30 2 * * *"


def test_a_backup_can_be_taken_from_the_page(tmp_path):
    client, bot = buildClient(tmp_path)
    assert "No backup has been taken yet" in client.get("/backups").text

    reply = client.post("/backups/now", follow_redirects=False)
    assert reply.status_code == 303

    from sixgenbot.core.backup import listBackups
    assert len(listBackups(bot.config.dataDir)) == 1
    assert "newest backup was taken" in client.get("/backups").text


def test_the_console_shows_what_was_logged(tmp_path):
    client, _ = buildClient(tmp_path)
    page = client.get("/console")
    assert page.status_code == 200
    assert "modules loaded" in page.text, "the loader's own log lines should be visible"


def test_the_console_can_show_problems_only(tmp_path):
    client, _ = buildClient(tmp_path)
    page = client.get("/console?only=problems")
    assert page.status_code == 200
    assert "show everything" in page.text


def test_health_is_ok_when_every_module_loaded(tmp_path):
    client, _ = buildClient(tmp_path)
    reply = client.get("/health")
    assert reply.status_code == 200
    assert reply.text == "ok"


def test_the_menu_is_drawn_on_every_page(tmp_path):
    client, _ = buildClient(tmp_path)
    for path in ("/", "/console", "/backups"):
        body = client.get(path).text
        assert "Status" in body and "Console" in body and "Backups" in body
        assert "SYSTEM" in body


def test_nothing_in_the_stylesheet_moves_or_reacts_to_hover(tmp_path):
    """INTERFACE_PRINCIPLES U-03 and U-04, checked rather than trusted.

    Comments are stripped first — the stylesheet explains *why* there is no
    hover rule, and the explanation is not a rule.
    """
    import re

    client, _ = buildClient(tmp_path)
    css = client.get("/static/sixgenbot.css").text
    rules = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    assert "transition: none !important" in rules
    assert "animation: none !important" in rules
    assert ":hover" not in rules, "a hover rule breaks U-04 — nothing happens on hover"

    lower = rules.lower()
    for banned in ("#fff", "#ffffff", "#000", "#000000", ": white", ": black"):
        assert banned not in lower, f"{banned} breaks U-03 — off-white and dark grey, never pure"
