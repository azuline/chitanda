from pathlib import Path

import pytest
from click.testing import CliRunner

from chitanda.config import Config

SAMPLE_CONFIG = Path(__file__).parent / "config.json"


def test_config_lazy_load(monkeypatch):
    monkeypatch.setattr("chitanda.config.CONFIG_PATH", SAMPLE_CONFIG)
    config = Config()
    assert config._config is None
    assert config["trigger_character"] == "."
    assert config._config is not None


def test_config_reload(monkeypatch):
    with CliRunner().isolated_filesystem():
        monkeypatch.setattr("chitanda.config.CONFIG_PATH", SAMPLE_CONFIG)
        config = Config()
        config._config = {"trigger_character": "!"}
        config.reload()
        assert config["trigger_character"] == "."


def test_load_empty_config(monkeypatch):
    with CliRunner().isolated_filesystem():
        config = Config()
        cfg_path = Path.cwd() / "tmp.json"
        cfg_path.touch()
        monkeypatch.setattr("chitanda.config.CONFIG_PATH", cfg_path)
        with pytest.raises(SystemExit):
            config._load_config()


def test_load_nonexistent_config(monkeypatch):
    with CliRunner().isolated_filesystem():
        config = Config()
        cfg_path = Path.cwd() / "tmp.json"
        monkeypatch.setattr("chitanda.config.CONFIG_PATH", cfg_path)
        with pytest.raises(SystemExit):
            config._load_config()


def test_load_config_invalid_json(monkeypatch):
    with CliRunner().isolated_filesystem():
        config = Config()
        cfg_path = Path.cwd() / "tmp.json"
        with cfg_path.open("w") as f:
            f.write("not json!")

        monkeypatch.setattr("chitanda.config.CONFIG_PATH", cfg_path)
        with pytest.raises(SystemExit):
            config._load_config()
