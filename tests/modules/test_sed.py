from asyncio import Future
from collections import deque
from unittest.mock import Mock, patch

import pytest

from chitanda.listeners import DiscordListener, IRCListener
from chitanda.modules.sed import _get_author, call, on_message, on_response
from chitanda.util import Message, Response


@pytest.mark.asyncio
async def test_on_message_match():
    with patch("chitanda.modules.sed._substitute", return_value=Future()) as sub:
        with patch("chitanda.modules.sed._attach_message_log"):
            sub.return_value.set_result(123)
            listener = Mock(message_log={"#chan": []})
            await on_message(
                Message(
                    bot=None,
                    listener=listener,
                    target="#chan",
                    author=None,
                    contents="s/from/to",
                    private=False,
                )
            )
            sub.assert_called()


@pytest.mark.asyncio
async def test_on_message_no_match():
    with patch("chitanda.modules.sed._attach_message_log"):
        with patch("chitanda.modules.sed._format_message"):
            message_log = Mock(spec=deque)
            listener = Mock(message_log={"#chan": message_log})
            await on_message(
                Message(
                    bot=None,
                    listener=listener,
                    target="#chan",
                    author=None,
                    contents="f/from/to",
                    private=False,
                )
            )
            message_log.appendleft.assert_called()


@pytest.mark.asyncio
async def test_on_message_no_channel():
    with patch("chitanda.modules.sed._attach_message_log") as attach:
        await on_message(
            Message(
                bot=None,
                listener=None,
                target=None,
                author=None,
                contents=None,
                private=True,
            )
        )
        attach.assert_not_called()


@pytest.mark.asyncio
async def test_on_response():
    # Tests on_response, _attach_message_log, and _get_author for IRC
    listener = IRCListener(None, "chitanda", "irc.freenode.fake")
    listener.nickname = "chitanda"

    await on_response(Response(None, listener, "#chan", "hello"))
    assert listener.message_log["#chan"].popleft() == "<chitanda> hello"


def test_get_author_discord():
    listener = Mock(spec=DiscordListener)
    listener.user = Mock(id=12345)
    assert "12345" == _get_author(listener)


@pytest.mark.asyncio
async def test_call_substitution():
    listener = Mock(message_log={"#chan": deque(["<a> hello", "<a> i like dardaR"])})
    assert "<a> i like azulazul" == await call(
        Message(
            bot=None,
            listener=listener,
            target="#chan",
            author=None,
            contents="s/dar/azul/gi",
            private=False,
        )
    )
