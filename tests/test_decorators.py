import re
from asyncio import coroutine

import pytest
from mock import Mock, patch

from chitanda.decorators import (
    admin_only,
    allowed_listeners,
    args,
    auth_only,
    channel_only,
    private_message_only,
    register,
)
from chitanda.errors import BotError
from chitanda.listeners import DiscordListener, IRCListener
from chitanda.util import Message


@patch('chitanda.decorators.sys')
@patch('chitanda.bot.Chitanda')
def test_register_decorator(chitanda, sys):
    chitanda.commands = {}
    sys.modules = {'hello': 12345}
    register('trigger')(Mock(__module__='hello'))
    assert chitanda.commands['trigger'] == 12345


def test_args_decorator():
    func = Mock()
    message = Message(None, 1, 2, 3, 'abc', 5)
    args(re.compile('a(bc)$'), ' meow')(func)(message)
    assert func.call_args[0][0].args == ('bc',)


def test_args_decorator_error():
    with pytest.raises(BotError):
        args('a$')(Mock())(Message(None, 1, 2, 3, 'bark', 5))


@pytest.mark.asyncio
async def test_admin_only_decorator_generator():
    async def func(*args, **kwargs):
        for n in [1, 2, 3]:
            yield n

    listener = Mock()
    listener.is_admin.side_effect = coroutine(lambda *args, **kwargs: True)
    assert [1, 2, 3] == [
        n
        async for n in admin_only(func)(
            Message(None, listener, 2, 'azul', 4, 5)
        )
    ]


@pytest.mark.asyncio
async def test_admin_only_decorator_not_generator():
    listener = Mock()
    listener.is_admin.side_effect = coroutine(lambda *args, **kwargs: True)
    func = Mock(side_effect=coroutine(lambda *args, **kwargs: 'hello'))
    assert 'hello' == await admin_only(func)(
        Message(None, listener, 2, 'azul', 4, 5)
    )


@pytest.mark.asyncio
async def test_admin_only_decorator_error():
    listener = Mock()
    listener.is_admin.side_effect = coroutine(lambda *args, **kwargs: False)
    with pytest.raises(BotError):
        await admin_only(Mock())(Message(None, listener, 2, 'azul', 4, 5))


@pytest.mark.asyncio
async def test_auth_only_decorator_generator():
    async def func(*args, **kwargs):
        for n in [1, 2, 3]:
            yield n

    listener = Mock()
    listener.is_authed.side_effect = coroutine(lambda *args, **kwargs: True)
    assert [1, 2, 3] == [
        n
        async for n in auth_only(func)(Message(None, listener, 2, 'azul', 4, 5))
    ]


@pytest.mark.asyncio
async def test_auth_only_decorator_not_generator():
    listener = Mock()
    listener.is_authed.side_effect = coroutine(lambda *args, **kwargs: True)
    func = Mock(side_effect=coroutine(lambda *args, **kwargs: 'hello'))
    assert 'hello' == await auth_only(func)(
        Message(None, listener, 2, 'azul', 4, 5)
    )


@pytest.mark.asyncio
async def test_auth_only_decorator_error():
    listener = Mock()
    listener.is_authed.side_effect = coroutine(lambda *args, **kwargs: False)
    with pytest.raises(BotError):
        await auth_only(Mock())(Message(None, listener, 2, 'azul', 4, 5))


def test_channel_only_decorator():
    func = Mock(return_value='hello')
    assert 'hello' == channel_only(func)(Message(None, 1, 2, 3, 4, False))


def test_channel_only_decorator_error():
    with pytest.raises(BotError):
        channel_only(Mock())(Message(None, 1, 2, 3, 4, True))


def test_private_message_only_decorator():
    func = Mock(return_value='hello')
    assert 'hello' == private_message_only(func)(
        Message(None, 1, 2, 3, 4, True)
    )


def test_private_message_only_decorator_error():
    with pytest.raises(BotError):
        private_message_only(Mock())(Message(None, 1, 2, 3, 4, False))


def test_allowed_listeners_decorator_one():
    assert 'hello' == allowed_listeners(IRCListener)(
        Mock(return_value='hello')
    )(Message(None, Mock(spec=IRCListener), 2, 3, 4, 5))


def test_allowed_listeners_decorator_fail():
    with pytest.raises(BotError):
        allowed_listeners(IRCListener)(Mock(return_value='hello'))(
            Message(None, Mock(spec=DiscordListener), 2, 3, 4, 5)
        )
