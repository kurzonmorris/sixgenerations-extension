from fastapi.testclient import TestClient

from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.appLogging import setupLogging
from sixgenbot.core.moduleLoader import loadModules
from sixgenbot.core.webApp import Bot


def buildClient(tmp_path, disabled=None):
    setupLogging(level="DEBUG")
    bot = Bot(loadConfig(tmp_path))
    bot.modules = loadModules(bot, disabled=disabled)
    return TestClient(bot.buildApp()), bot


def test_the_status_page_says_it_is_running(tmp_path):
    client, _ = buildClient(tmp_path)
    page = client.get("/")
    assert page.status_code == 200
    assert "sixgenbot is running" in page.text
    assert "Nothing needs fixing" in page.text
    assert "systemStatus" in page.text


def test_the_status_page_admits_there_is_no_database_yet(tmp_path):
    client, _ = buildClient(tmp_path)
    assert "No database yet" in client.get("/").text


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
    for path in ("/", "/console"):
        body = client.get(path).text
        assert "Status" in body and "Console" in body
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
