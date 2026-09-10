from sixgenbot.core.appConfig import loadConfig


def test_defaults_apply_when_there_is_no_config_file(tmp_path):
    config = loadConfig(tmp_path)
    assert config.port == 8770
    assert config.title == "Six Generations"
    assert config.dataDir == tmp_path
    assert config.disabledModules == []


def test_a_setting_can_be_changed_without_repeating_the_rest(tmp_path):
    (tmp_path / "config.toml").write_text('[web]\nport = 9001\n', encoding="utf-8")
    config = loadConfig(tmp_path)
    assert config.port == 9001
    assert config.title == "Six Generations"  # untouched default survives


def test_secrets_live_in_their_own_file(tmp_path):
    (tmp_path / "secrets.toml").write_text('shopifyToken = "shpat_example"\n', encoding="utf-8")
    config = loadConfig(tmp_path)
    assert config.secret("shopifyToken") == "shpat_example"
    assert "shopifyToken" not in config.settings


def test_the_environment_wins_so_docker_can_inject(tmp_path, monkeypatch):
    (tmp_path / "secrets.toml").write_text('ebayKey = "from-file"\n', encoding="utf-8")
    monkeypatch.setenv("SIXGENBOT_EBAYKEY", "from-environment")
    assert loadConfig(tmp_path).secret("ebayKey") == "from-environment"


def test_a_missing_secret_is_empty_not_an_error(tmp_path):
    assert loadConfig(tmp_path).secret("neverSet") == ""
