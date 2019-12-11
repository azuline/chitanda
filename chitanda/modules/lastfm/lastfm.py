import asyncio
import logging
from datetime import datetime
from json import JSONDecodeError

import requests

from chitanda.config import config
from chitanda.database import database
from chitanda.decorators import args, auth_only, register
from chitanda.errors import BotError

logger = logging.getLogger(__name__)
API_URL = 'https://ws.audioscrobbler.com/2.0/'


@register('lastfm')
@args(r'$')
@auth_only
async def call(message):
    """Relay your currently playing Last.FM track."""
    lastfm = _get_lastfm_nick(message.username, message.listener)
    response = await _get_now_playing(lastfm, message.author)
    track, album, artist = (
        response['name'],
        response['album']['#text'],
        response['artist']['#text'],
    )
    time_since = _calculate_time_since_played(response, message.author)
    tags = await _get_track_tags(track, album, artist)
    return _format_response(
        message.author, track, album, artist, tags, time_since
    )


def _get_lastfm_nick(username, listener):
    with database() as (conn, cursor):
        cursor.execute(
            """
            SELECT lastfm
            FROM lastfm
            WHERE user = ?  AND listener = ?
            """,
            (username, str(listener)),
        )
        row = cursor.fetchone()
        if not row:
            raise BotError('No Last.FM name set.')
        return row['lastfm']


async def _get_now_playing(lastfm, author=None):
    try:
        response = (
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: requests.get(
                    API_URL,
                    headers={'User-Agent': config['user_agent']},
                    params={
                        'method': 'user.getrecenttracks',
                        'api_key': config['lastfm']['api_key'],
                        'user': lastfm,
                        'limit': 1,
                        'format': 'json',
                    },
                    timeout=5,
                ),
            )
        ).json()
    except JSONDecodeError as e:
        logger.error(f'Failed to query Last.FM API: {e}.')
        raise BotError(f'Failed to query Last.FM API.')
    if 'error' in response:
        message = (
            f'Failed to query Last.FM API: {response["error"]} '
            f'{response["message"]}.'
        )
        logger.error(message)
        raise BotError(message)
    if not response['recenttracks']['track']:
        raise BotError(f'{author} has never scrobbled before.')
    return response['recenttracks']['track'][0]


def _calculate_time_since_played(track, author=None):
    if '@attr' in track:
        return

    scrobble_time = datetime.strptime(
        track['date']['#text'], '%d %b %Y, %H:%M'
    )
    diff = datetime.utcnow() - scrobble_time
    hours, seconds = divmod(diff.seconds, 3600)
    minutes = divmod(seconds, 60)[0]

    time_since = []

    if diff.days > 0:
        time_since.append(f'{diff.days} day(s)')
    if hours > 0:
        time_since.append(f'{hours} hour(s)')
    if minutes > 0:
        time_since.append(f'{minutes} minute(s)')

    if diff.days > 0 or hours > 0:
        raise BotError(
            f'{author} is not playing anything (last seen: '
            f'{" ".join(time_since)} ago)'
        )

    return f'{minutes} minutes'


async def _get_track_tags(track, album, artist):
    params = [
        {'method': 'track.gettoptags', 'track': track, 'artist': artist},
        {'method': 'album.gettoptags', 'album': album, 'artist': artist},
        {'method': 'artist.gettoptags', 'artist': artist},
    ]

    executors = [
        asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.get(
                API_URL,
                headers={'User-Agent': config['user_agent']},
                params={
                    'api_key': config['lastfm']['api_key'],
                    'format': 'json',
                    **p,
                },
                timeout=5,
            ),
        )
        for p in params
    ]

    tags = []
    for response in await asyncio.gather(*executors):
        data = response.json()
        try:
            tags += [t['name'] for t in data['toptags']['tag']]
        except KeyError:
            pass

    return tags[:3]


def _format_response(author, track, album, artist, tags, time_since):
    response = f'{author} is now playing {track}'
    if artist:
        response += f' by {artist}'
    if album:
        response += f' from {album}'
    if tags:
        response += f' [tags: {" / ".join(tags)}]'
    if time_since:
        response += f' (scrobbled {time_since} ago)'
    return response
