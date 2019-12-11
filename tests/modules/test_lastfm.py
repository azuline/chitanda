from asyncio import coroutine
from datetime import datetime, timedelta

import pytest
from mock import Mock

from chitanda.database import database
from chitanda.errors import BotError
from chitanda.listeners import DiscordListener
from chitanda.modules.lastfm import lastfm, set, unset
from chitanda.util import Message


@pytest.mark.asyncio
async def test_lastfm(test_db, monkeypatch):
    requests = Mock()
    requests.get.side_effect = [
        Mock(json=lambda d=d: d) for d in DEMO_RESPONSES
    ]
    monkeypatch.setattr('chitanda.modules.lastfm.lastfm.requests', requests)

    monkeypatch.setattr(
        'chitanda.modules.lastfm.lastfm.config',
        {'user_agent': 'chitanda', 'lastfm': {'api_key': 'abc'}},
    )

    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO lastfm (user, listener, lastfm)
            VALUES ('azuline', 'DiscordListener', 'azulfm')
            """
        )
        conn.commit()

    response = await lastfm.call(
        Message(
            bot=None,
            listener=Mock(
                is_authed=coroutine(lambda *a: 'azuline'),
                spec=DiscordListener,
                __str__=lambda *a: 'DiscordListener',
            ),
            target='#chan',
            author='azul',
            contents='',
            private=False,
        )
    )

    assert response == (
        'azul is now playing Forgotten Love (Claptone Remix) by Aurora '
        'from Forgotten Love (Claptone Remix) '
        '[tags: trance / Melodic Death Metal / dance]'  # lol nice tag
    )


def test_calculate_time_since_last_played():
    time = datetime.utcnow() - timedelta(days=1, hours=1, minutes=1)
    with pytest.raises(BotError) as e:
        lastfm._calculate_time_since_played(
            {'date': {'#text': time.strftime('%d %b %Y, %H:%M')}}, 'azul'
        )
    assert e.value.args[0] == (
        'azul is not playing anything (last seen: 1 day(s) '
        '1 hour(s) 1 minute(s) ago)'
    )


@pytest.mark.asyncio
async def test_set(test_db):
    await set.call(
        Message(
            bot=None,
            listener=Mock(
                is_authed=coroutine(lambda *a: 'azuline'),
                spec=DiscordListener,
                __str__=lambda *a: 'DiscordListener',
            ),
            target='#chan',
            author='azul',
            contents='azulfm',
            private=True,
        )
    )
    with database() as (conn, cursor):
        cursor.execute(
            """
            SELECT lastfm FROM lastfm
            WHERE user = 'azuline' and listener = 'DiscordListener'
            """
        )
        assert cursor.fetchone()['lastfm'] == 'azulfm'


@pytest.mark.asyncio
async def test_unset(test_db):
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO lastfm (user, listener, lastfm)
            VALUES ('azuline', 'DiscordListener', 'azulfm')
            """
        )
        conn.commit()

    await unset.call(
        Message(
            bot=None,
            listener=Mock(
                is_authed=coroutine(lambda *a: 'azuline'),
                spec=DiscordListener,
                __str__=lambda *a: 'DiscordListener',
            ),
            target='#chan',
            author='azul',
            contents='',
            private=True,
        )
    )

    with database() as (conn, cursor):
        cursor.execute(
            """
            SELECT lastfm FROM lastfm
            WHERE user = 'azuline' and listener = 'DiscordListener'
            """
        )
        assert not cursor.fetchone()


DEMO_RESPONSES = [
    {
        'recenttracks': {
            '@attr': {
                'page': '1',
                'perPage': '1',
                'total': '928',
                'totalPages': '928',
                'user': 'azuline',
            },
            'track': [
                {
                    '@attr': {'nowplaying': 'true'},
                    'album': {
                        '#text': 'Forgotten Love (Claptone Remix)',
                        'mbid': '',
                    },
                    'artist': {'#text': 'Aurora', 'mbid': ''},
                    'image': [
                        {'#text': '', 'size': 'small'},
                        {'#text': '', 'size': 'medium'},
                        {'#text': '', 'size': 'large'},
                        {'#text': '', 'size': 'extralarge'},
                    ],
                    'mbid': '',
                    'name': 'Forgotten Love (Claptone Remix)',
                    'streamable': '0',
                    'url': (
                        'https://www.last.fm/music/Aurora/_/Forgotten+'
                        'Love+(Claptone+Remix)'
                    ),
                },
                {
                    'album': {'#text': '', 'mbid': ''},
                    'artist': {
                        '#text': 'Bungle',
                        'mbid': 'ee63ef60-6cd3-4950-900a-c7cbcf4de517',
                    },
                    'date': {
                        '#text': '09 Aug 2019, 02:21',
                        'uts': '1565317289',
                    },
                    'image': [
                        {'#text': '', 'size': 'small'},
                        {'#text': '', 'size': 'medium'},
                        {'#text': '', 'size': 'large'},
                        {'#text': '', 'size': 'extralarge'},
                    ],
                    'mbid': 'ba45ed45-9634-4613-8f03-33d0d42bed8c',
                    'name': 'Alone',
                    'streamable': '0',
                    'url': 'https://www.last.fm/music/Bungle/_/Alone',
                },
            ],
        }
    },
    {
        'toptags': {
            '@attr': {
                'artist': 'AURORA',
                'track': 'Forgotten Love (Claptone Remix)',
            },
            'tag': [],
        }
    },
    {},
    {
        'toptags': {
            '@attr': {'artist': 'Aurora'},
            'tag': [
                {
                    'count': 100,
                    'name': 'trance',
                    'url': 'https://www.last.fm/tag/trance',
                },
                {
                    'count': 82,
                    'name': 'Melodic Death Metal',
                    'url': 'https://www.last.fm/tag/Melodic+Death+Metal',
                },
                {
                    'count': 70,
                    'name': 'dance',
                    'url': 'https://www.last.fm/tag/dance',
                },
                {
                    'count': 64,
                    'name': 'vocal trance',
                    'url': 'https://www.last.fm/tag/vocal+trance',
                },
            ],
        }
    },
]
