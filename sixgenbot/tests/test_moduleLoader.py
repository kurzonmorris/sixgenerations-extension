from sixgenbot.core.appConfig import loadConfig
from sixgenbot.core.moduleLoader import loadModules
from sixgenbot.core.webApp import Bot


def test_finds_the_real_modules_and_registers_them(tmp_path):
    bot = Bot(loadConfig(tmp_path))
    loaded = loadModules(bot)

    names = {entry.name for entry in loaded if entry.ok}
    assert {"systemStatus", "activityLog"} <= names
    assert all(entry.version.startswith("v_") for entry in loaded if entry.ok)
    assert bot.menu, "a module registered no menu item"


def test_a_module_can_be_switched_off_in_the_settings(tmp_path):
    bot = Bot(loadConfig(tmp_path))
    loaded = loadModules(bot, disabled=["activityLog"])

    off = [entry for entry in loaded if entry.problem == "switched off"]
    assert [entry.folder for entry in off] == ["activityLog"]
    assert "activityLog" not in {entry.name for entry in loaded if entry.ok}
    assert "Console" not in [item.label for item in bot.menu]


def test_menu_items_are_grouped_in_a_fixed_order(tmp_path):
    bot = Bot(loadConfig(tmp_path))
    bot.currentModule = "test"
    bot.addMenuItem("Money thing", "/money", group="MONEY")
    bot.addMenuItem("Item thing", "/items", group="ITEMS")
    bot.addMenuItem("Made up", "/other", group="SOMETHINGELSE")

    groups = [name for name, _ in bot.groupedMenu()]
    assert groups.index("ITEMS") < groups.index("MONEY"), "known groups keep their order"
    assert groups[-1] == "SOMETHINGELSE", "an unknown group is appended, not rejected"


FIXTURES = "sixgenbot.tests.fixtureModules"


def test_a_broken_module_is_reported_and_the_rest_still_load(tmp_path):
    """The central claim of the module system, proved rather than trusted."""
    bot = Bot(loadConfig(tmp_path))
    loaded = loadModules(bot, package=FIXTURES)
    byFolder = {entry.folder: entry for entry in loaded}

    assert byFolder["goodOne"].ok, "a healthy module must still load"
    assert [item.label for item in bot.menu] == ["Good One"]

    assert not byFolder["throwsOnRegister"].ok
    assert "broken on purpose" in byFolder["throwsOnRegister"].problem

    assert not byFolder["missingContract"].ok
    assert "NAME, VERSION and register" in byFolder["missingContract"].problem

    assert bot.currentModule is None, "currentModule must be cleared even after a failure"
