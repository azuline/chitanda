from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from chitanda.errors import InvalidListener, NoCommandFound
from chitanda.util import (
    Message,
    create_app_dirs,
    get_listener,
    irc_unstyle,
    trim_message,
)

TEST_PARSE_CONFIG = {
    "webserver": {"enable": True},
    "trigger_character": ".",
    "modules": {
        "global": ["cmd", "multi_word", "henlo"],
        "BananaListener": ["ramwolf"],
    },
}


def test_parse_command(monkeypatch):
    monkeypatch.setattr("chitanda.util.config", TEST_PARSE_CONFIG)
    cmd = Mock(__name__="cmd", call=Mock(return_value=123))
    bot = Mock(commands={"cmd": cmd})

    message = Message(bot, "TestListener", 2, 3, ".cmd", 5)
    assert 123 == message.call_command()
    assert cmd.call.call_args[0][0].contents == ""


def test_parse_command_multi_word(monkeypatch):
    monkeypatch.setattr("chitanda.util.config", TEST_PARSE_CONFIG)
    cmd = Mock(__name__="multi_word", call=Mock(return_value=123))
    bot = Mock(commands={"multi word": cmd})

    message = Message(bot, "TestListener", 2, 3, ".multi word command", 5)
    assert 123 == message.call_command()
    assert cmd.call.call_args[0][0].contents == "command"


def test_parse_command_not_enabled(monkeypatch):
    monkeypatch.setattr("chitanda.util.config", TEST_PARSE_CONFIG)
    cmd = Mock(__name__="ramwolf", call=Mock(return_value=123))
    bot = Mock(commands={"ramwolf": cmd})

    message = Message(bot, "AppleListener", 2, 3, ".ramwolf", 5)
    with pytest.raises(NoCommandFound):
        message.call_command()


def test_parse_command_trigger_match(monkeypatch):
    monkeypatch.setattr("chitanda.util.config", TEST_PARSE_CONFIG)
    cmd = Mock(__name__="henlo", call=Mock(return_value=123))
    bot = Mock(commands={"henlo ": cmd})
    message = Message(bot, "TestListener", 2, 3, ".not henlo", 5)
    with pytest.raises(NoCommandFound):
        message.call_command()


def test_parse_command_no_trigger_match(monkeypatch):
    monkeypatch.setattr("chitanda.util.config", TEST_PARSE_CONFIG)
    bot = Mock(commands={"henlo ": 1})
    message = Message(bot, "TestListener", 2, 3, "henlo", 5)
    with pytest.raises(NoCommandFound):
        message.call_command()


def test_create_app_dirs(monkeypatch):
    with CliRunner().isolated_filesystem():
        config_dir = Path.cwd() / "config"
        data_dir = Path.cwd() / "data"
        monkeypatch.setattr("chitanda.util.CONFIG_DIR", config_dir / "subdir")
        monkeypatch.setattr("chitanda.util.DATA_DIR", data_dir)

        create_app_dirs()

        assert config_dir.is_dir()
        assert data_dir.is_dir()


def test_create_app_dirs_no_perms(monkeypatch):
    with CliRunner().isolated_filesystem():
        config_dir = Path.cwd() / "config"
        monkeypatch.setattr("chitanda.util.CONFIG_DIR", config_dir / "subdir")
        monkeypatch.setattr("chitanda.util.DATA_DIR", Path.cwd() / "data")

        config_dir.mkdir(mode=0o000)

        with pytest.raises(SystemExit):
            create_app_dirs()


def test_get_listener_discord():
    bot = Mock(discord_listener=1, irc_listeners={"a": 2, "b": 3})
    assert 1 == get_listener(bot, "DiscordListener")


def test_get_listener_irc():
    bot = Mock(discord_listener=1, irc_listeners={"a": 2, "b": 3})
    assert 2 == get_listener(bot, "IRCListener@a")


def test_get_listener_irc_nonexistent():
    bot = Mock(discord_listener=1, irc_listeners={"a": 2, "b": 3})
    with pytest.raises(InvalidListener):
        get_listener(bot, "IRCListener@c")


def test_get_listener_nonexistent():
    with pytest.raises(InvalidListener):
        get_listener(Mock(), "AppleListener")


def test_irc_unstyle():
    assert "abcdefghij" == irc_unstyle("\x02abcdefg\x1Dhij\x02")


@pytest.mark.parametrize(
    "input_, output", [("hello", "hello"), ("longertext", "longer...")]
)
def test_trim_message(input_, output):
    assert output == trim_message(input_, length=9)
