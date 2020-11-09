from unittest.mock import Mock, patch

import pytest

from chitanda.listeners import DiscordListener
from chitanda.modules.help import _applicable_listener, _generate_help_text, call
from chitanda.util import Message


def a():
    """function a"""


def b():
    """function b"""


@pytest.mark.asyncio
@patch("chitanda.modules.help._applicable_listener")
async def test_help(applicable_listener, monkeypatch):
    monkeypatch.setattr("chitanda.modules.help.config", {"trigger_character": "."})

    applicable_listener.return_value = True
    bot = Mock(commands={"aaa": Mock(call=a), "b": Mock(call=b)})
    response = [
        r
        async for r in call(
            Message(
                bot=bot,
                listener=None,
                target="azul",
                author="azul",
                contents="",
                private=False,
            )
        )
    ]

    assert response == [
        {"target": "azul", "message": "Help:"},
        {"target": "azul", "message": ".aaa | function a"},
        {"target": "azul", "message": ".b   | function b"},
    ]


@pytest.mark.asyncio
@patch("chitanda.modules.help._applicable_listener")
async def test_help_discord(applicable_listener, monkeypatch):
    monkeypatch.setattr("chitanda.modules.help.config", {"trigger_character": "."})

    applicable_listener.return_value = True
    bot = Mock(commands={"aaa": Mock(call=a), "b": Mock(call=b)})
    response = [
        r
        async for r in call(
            Message(
                bot=bot,
                listener=Mock(spec=DiscordListener),
                target="azul",
                author="azul",
                contents="",
                private=False,
            )
        )
    ][0]

    assert response["message"].title == "Help!"
    assert response["message"].fields[0].name == ".aaa"
    assert response["message"].fields[0].value == "function a"
    assert response["message"].fields[1].name == ".b"
    assert response["message"].fields[1].value == "function b"


def test_applicable_listeners():
    call = Mock(listeners={DiscordListener})
    assert _applicable_listener(DiscordListener(None), call)


def test_applicable_listeners_accept_all():
    call = a  # A function without a listeners attribute.
    assert _applicable_listener(Mock(), call)


def test_applicable_listeners_failure():
    call = Mock(listeners={DiscordListener})
    assert not _applicable_listener(Mock(), call)


def test_generate_help_text_everything():
    def test_func():
        """Sample help text."""

    test_func.admin_only = True
    test_func.auth_only = True
    test_func.channel_only = True
    test_func.private_message_only = True

    assert _generate_help_text(test_func) == (
        "Sample help text. (admin only) (requires authentication) "
        "(channel only) (PM only)"
    )


def test_generate_help_text_nothing():
    def test_func():
        """Sample help text."""

    assert _generate_help_text(test_func) == "Sample help text."
