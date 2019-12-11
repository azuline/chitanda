from asyncio import coroutine

import pytest
from mock import Mock, patch

from chitanda.database import database
from chitanda.errors import BotError
from chitanda.listeners import DiscordListener
from chitanda.modules.quotes import add, delete, fetch, find
from chitanda.util import Message


@pytest.mark.asyncio
async def test_add_quote(test_db):
    with patch('chitanda.modules.quotes.add._get_quote_id') as get_id:
        get_id.return_value = 7
        await add.call(
            Message(
                bot=None,
                listener=Mock(
                    is_authed=coroutine(lambda *a: 'azuline'),
                    spec=DiscordListener,
                ),
                target='#chan',
                author='azul',
                contents='<newuser> im new',
                private=False,
            )
        )
    with database() as (conn, cursor):
        cursor.execute('SELECT channel, quote, adder FROM quotes WHERE id = 7')
        row = cursor.fetchone()
        assert row['channel'] == '#chan'
        assert row['quote'] == '<newuser> im new'
        assert row['adder'] == 'azuline'


def test_get_quote_id(test_db):
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO quotes (id, channel, listener, quote, adder)
            VALUES (20, 'a', 'b', 'c', 'd'), (59, 'a', 'b', 'c', 'd')
            """
        )
        conn.commit()
        assert 60 == add._get_quote_id(cursor, 'b', 'a')


def test_get_quote_id_nonexistent(test_db):
    with database() as (conn, cursor):
        assert 1 == add._get_quote_id(cursor, 'a', 'b')


@pytest.mark.asyncio
async def test_delete_quote(test_db):
    with patch('chitanda.modules.quotes.delete.fetch.fetch_quotes') as f:
        f.return_value = []
        with database() as (conn, cursor):
            cursor.execute(
                """
                INSERT INTO quotes (id, channel, listener, quote, adder)
                VALUES
                (1, '#chan', 'DiscordListener', 'hi', 'azul'),
                (2, '#chan', 'DiscordListener', 'hi again', 'azul'),
                (1, '#notchan', 'DiscordListener', 'bye', 'azul'),
                (3, '#chan', 'IRCListener', 'bye again', 'azul')
                """
            )
            conn.commit()

            async for r in delete.call(
                Message(
                    bot=None,
                    listener=Mock(
                        is_admin=coroutine(lambda *a: True),
                        spec=DiscordListener,
                        __str__=lambda *a: 'DiscordListener',
                    ),
                    target='#chan',
                    author='azul',
                    contents='1 2 3',
                    private=False,
                )
            ):
                pass

            cursor.execute('SELECT COUNT(1) FROM quotes')
            assert 2 == cursor.fetchone()[0]


def test_parse_quote_ids():
    assert [1, 3, 5] == delete._parse_quote_ids('1 3 5')


def test_parse_quote_ids_error():
    with pytest.raises(BotError):
        delete._parse_quote_ids('1 3 ???')


@pytest.mark.asyncio
async def test_fetch_random_quote_nonexistent(test_db):
    assert ['This channel has no quotes saved.'] == [
        r
        async for r in fetch.call(
            Message(
                bot=None,
                listener='DiscordListener',
                target='#chan',
                author='azul',
                contents='',
                private=False,
            )
        )
    ]


@pytest.mark.asyncio
async def test_fetch_random_quote(test_db):
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO quotes (id, channel, listener, quote, adder)
            VALUES
            (1, '#chan', 'DiscordListener', 'hi', 'azul'),
            (2, '#chan', 'DiscordListener', 'hi again', 'azul')
            """
        )
        conn.commit()

    response = [
        r
        async for r in fetch.call(
            Message(
                bot=None,
                listener='DiscordListener',
                target='#chan',
                author='azul',
                contents='',
                private=False,
            )
        )
    ]

    assert response
    assert 'This channel has no quotes saved.' not in response


@pytest.mark.asyncio
async def test_fetch_quotes(test_db):
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO quotes (id, channel, listener, quote, adder)
            VALUES
            (1, '#chan', 'DiscordListener', 'hi', 'azul'),
            (2, '#chan', 'DiscordListener', 'hi again', 'azul')
            """
        )
        conn.commit()

    response = [
        r
        async for r in fetch.call(
            Message(
                bot=None,
                listener='DiscordListener',
                target='#chan',
                author='azul',
                contents='1 2 3',
                private=False,
            )
        )
    ]

    assert len(response) == 3
    assert 'Quote(s) 3 do not exist.' in response


@pytest.mark.asyncio
async def test_fetch_quotes_overfetch(test_db):
    with pytest.raises(BotError):
        async for r in fetch.call(
            Message(
                bot=None,
                listener='DiscordListener',
                target='#chan',
                author='azul',
                contents='1 2 3 4 5',
                private=False,
            )
        ):
            pass


@pytest.mark.asyncio
async def test_find_quote(test_db):
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO quotes (id, channel, listener, quote, adder)
            VALUES
            (1, '#chan', 'DiscordListener', 'hi zgign', 'azul'),
            (2, '#chan', 'DiscordListener', 'hi again', 'azul')
            """
        )
        conn.commit()

    response = [
        r
        async for r in find.call(
            Message(
                bot=None,
                listener='DiscordListener',
                target='#chan',
                author='azul',
                contents='hi a%',
                private=False,
            )
        )
    ]

    assert len(response) == 1
    assert response[0] == '#2 by azul: hi again'


@pytest.mark.asyncio
async def test_find_quote_doesnt_exist(test_db):
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO quotes (id, channel, listener, quote, adder)
            VALUES
            (2, '#chan', 'DiscordListener', 'hi again', 'azul')
            """
        )
        conn.commit()

    response = [
        r
        async for r in find.call(
            Message(
                bot=None,
                listener='DiscordListener',
                target='#chan',
                author='azul',
                contents='hi a%z',
                private=False,
            )
        )
    ]

    assert len(response) == 1
    assert response[0] == 'No quotes found.'
