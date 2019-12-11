from asyncio import coroutine

import pytest
from mock import Mock, call

from chitanda.database import database
from chitanda.errors import BotError
from chitanda.listeners import IRCListener
from chitanda.modules.irc_channels import (
    _get_channels_to_rejoin,
    _rejoin_channels,
    join,
    on_join,
    on_part,
    part,
)
from chitanda.util import Message


@pytest.mark.asyncio
async def test_join():
    listener = Mock(
        join=Mock(return_value=coroutine(lambda *args: True)()),
        is_admin=coroutine(lambda *a: True),
        spec=IRCListener,
    )

    await join.call(
        Message(
            bot=None,
            listener=listener,
            target=None,
            author='azul',
            contents='#henlo',
            private=False,
        )
    )
    listener.join.assert_called_with('#henlo')


@pytest.mark.asyncio
async def test_part_no_args():
    listener = Mock(
        part=Mock(return_value=coroutine(lambda *args: True)()),
        is_admin=coroutine(lambda *a: True),
        spec=IRCListener,
    )

    await part.call(
        Message(
            bot=None,
            listener=listener,
            target='#henlo',
            author='azul',
            contents='',
            private=False,
        )
    )
    listener.part.assert_called_with('#henlo')


@pytest.mark.asyncio
async def test_part_channel_arg():
    listener = Mock(
        part=Mock(return_value=coroutine(lambda *args: True)()),
        is_admin=coroutine(lambda *a: True),
        spec=IRCListener,
    )

    await part.call(
        Message(
            bot=None,
            listener=listener,
            target='#henlo',
            author='azul',
            contents='#idontwantthis',
            private=False,
        )
    )
    listener.part.assert_called_with('#idontwantthis')


@pytest.mark.asyncio
async def test_part_no_channel():
    listener = Mock(
        part=Mock(return_value=coroutine(lambda *args: True)()),
        is_admin=coroutine(lambda *a: True),
        spec=IRCListener,
    )

    with pytest.raises(BotError):
        await part.call(
            Message(
                bot=None,
                listener=listener,
                target='azul',
                author='azul',
                contents='',
                private=True,
            )
        )


@pytest.mark.asyncio
async def test_on_join(test_db):
    listener = IRCListener(None, 'chitanda', 'irc.freenode.fake')
    listener.nickname = 'chitanda'
    listener.on_join = coroutine(lambda *args: True)
    await on_join(listener, '#channel', 'chitanda')
    with database() as (conn, cursor):
        cursor.execute(
            """
            SELECT 1 FROM irc_channels WHERE name = "#channel"
            AND server = "irc.freenode.fake" AND active = 1
            """
        )
        assert cursor.fetchone()


@pytest.mark.asyncio
async def test_on_join_other_user(test_db):
    listener = IRCListener(None, 'chitanda', 'irc.freenode.fake')
    listener.nickname = 'chitanda'
    listener.on_join = coroutine(lambda *args: True)
    await on_join(listener, '#channel', 'azul')
    with database() as (conn, cursor):
        cursor.execute(
            """
            SELECT 1 FROM irc_channels WHERE name = "#channel"
            AND server = "irc.freenode.fake" AND active = 1
            """
        )
        assert not cursor.fetchone()


@pytest.mark.asyncio
async def test_on_part(test_db):
    listener = IRCListener(None, 'chitanda', 'irc.freenode.fake')
    listener.nickname = 'chitanda'
    listener.on_part = coroutine(lambda *args: True)
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO irc_channels (name, server, active)
            VALUES ("#channel", "irc.freenode.fake", 1)
            """
        )
        conn.commit()
        await on_part(listener, '#channel', 'chitanda', None)
        cursor.execute(
            """
            SELECT 1 FROM irc_channels WHERE name = "#channel"
            AND server = "irc.freenode.fake" AND active = 0
            """
        )
        assert cursor.fetchone()


@pytest.mark.asyncio
async def test_on_part_other_user(test_db):
    listener = IRCListener(None, 'chitanda', 'irc.freenode.fake')
    listener.nickname = 'chitanda'
    listener.on_part = coroutine(lambda *args: True)
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO irc_channels (name, server)
            VALUES ("#channel", "irc.freenode.fake")
            """
        )
        conn.commit()
        await on_part(listener, '#channel', 'azul', None)
        cursor.execute(
            """
            SELECT 1 FROM irc_channels WHERE name = "#channel"
            AND server = "irc.freenode.fake" AND active = 1
            """
        )
        assert cursor.fetchone()


def test_get_channels_to_rejoin(test_db):
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO irc_channels (name, server) VALUES
            ("#1", "1"), ("#2", "2")
            """
        )
        conn.commit()
        assert _get_channels_to_rejoin() == {'1': ['#1'], '2': ['#2']}


@pytest.mark.asyncio
async def test_rejoin_channels():
    listener1 = Mock(
        performed=True, join=Mock(return_value=coroutine(lambda *args: True)())
    )
    listener2 = Mock(
        performed=True, join=Mock(return_value=coroutine(lambda *args: True)())
    )
    bot = Mock(irc_listeners={'server1': listener1, 'server2': listener2})
    channels = {'server1': ['a', 'b'], 'server2': ['c', 'd']}
    await _rejoin_channels(bot, channels)
    assert not channels
    assert listener1.join.call_args_list == [call('a'), call('b')]
    assert listener2.join.call_args_list == [call('c'), call('d')]


@pytest.mark.asyncio
async def test_rejoin_channels_timeout(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.irc_channels.asyncio',
        Mock(sleep=coroutine(lambda *args: True)),
    )
    bot = Mock(irc_listeners={})
    channels = {'server1': ['a', 'b'], 'server2': ['c', 'd']}
    await _rejoin_channels(bot, channels)
    assert 'server1' in channels and 'server2' in channels
