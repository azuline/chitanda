from asyncio import Future, coroutine

import pytest
from mock import Mock, call, patch

from chitanda.listeners import IRCListener


def test_repr():
    listener = IRCListener(None, 'a', 'irc.freenode.fake')
    assert 'IRCListener@irc.freenode.fake' == repr(listener)


@pytest.mark.asyncio
async def test_perform(monkeypatch):
    listener = IRCListener(None, 'a', 'irc.freenode.fake')
    monkeypatch.setattr(
        'chitanda.listeners.irc.config',
        {'irc_servers': {listener.hostname: {'perform': ['per1', 'per2']}}},
    )

    with patch.object(listener, 'raw', return_value=Future()) as raw:
        raw.return_value.set_result(123)
        await listener._perform()
        assert raw.call_args_list == [call('per1\r\n'), call('per2\r\n')]
        assert listener.performed is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'method', ['on_channel_message', 'on_private_message']
)
async def test_on_message(method):
    bot = Mock()
    bot.handle_message.return_value = coroutine(lambda **kwargs: None)()
    listener = IRCListener(bot, 'zad', 'irc.freenode.fake')

    await getattr(listener, method)(1, 'azul', 2)
    bot.handle_message.assert_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'method', ['on_channel_message', 'on_private_message']
)
async def test_on_message_self_message(method):
    bot = Mock()
    bot.handle_message.return_value = coroutine(lambda **kwargs: None)()
    listener = IRCListener(bot, 'zad', 'irc.freenode.fake')
    listener.nickname = 'zad'

    await getattr(listener, method)(1, 'zad', 2)
    bot.handle_message.assert_not_called()


@pytest.mark.asyncio
async def test_is_admin(monkeypatch):
    listener = IRCListener(None, 'chitanda', 'irc.freenode.fake')
    monkeypatch.setattr(
        'chitanda.listeners.irc.config', {'admins': {str(listener): ['azul']}}
    )

    with patch.object(listener, 'whois', return_value=Future()) as whois:
        whois.return_value.set_result({'identified': True, 'account': 'azul'})
        assert await listener.is_admin('azul')


@pytest.mark.asyncio
async def test_is_not_admin(monkeypatch):
    listener = IRCListener(None, 'chitanda', 'irc.freenode.fake')
    monkeypatch.setattr(
        'chitanda.listeners.irc.config', {'admins': {str(listener): ['azul']}}
    )

    with patch.object(listener, 'whois', return_value=Future()) as whois:
        whois.return_value.set_result({'identified': True, 'account': 'zad'})
        assert not await listener.is_admin('zad')


@pytest.mark.asyncio
async def test_is_admin_not_authenticated(monkeypatch):
    listener = IRCListener(None, 'chitanda', 'irc.freenode.fake')
    monkeypatch.setattr(
        'chitanda.listeners.irc.config', {'admins': {str(listener): ['azul']}}
    )

    with patch.object(listener, 'whois', return_value=Future()) as whois:
        whois.return_value.set_result({'identified': False, 'account': None})
        assert not await listener.is_admin('azul')


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'identified, account, authed', [(True, 'zad', True), (False, None, False)]
)
async def test_is_authed(identified, account, authed, monkeypatch):
    listener = IRCListener(None, 'chitanda', 'irc.freenode.fake')
    monkeypatch.setattr(
        'chitanda.listeners.irc.config', {'admins': {str(listener): ['azul']}}
    )

    with patch.object(listener, 'whois', return_value=Future()) as whois:
        whois.return_value.set_result(
            {'identified': identified, 'account': account}
        )
        if authed:
            assert await listener.is_authed('azul')
        else:
            assert not await listener.is_authed('azul')
