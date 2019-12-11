import asyncio
import logging
import re
from json import JSONDecodeError

import requests

from chitanda.config import config
from chitanda.decorators import args, register
from chitanda.errors import BotError
from chitanda.util import trim_message

logger = logging.getLogger(__name__)


@register('urbandictionary')
@args(r'(\d+) (.+)', r'(.+)')
async def call(message):
    """Queries the UrbanDictionary API and relays the response."""
    entry, search = _parse_args(message.args)
    response = await _make_request(search)
    if response['list']:
        return trim_message(_get_definition(response, entry), length=400)
    raise BotError(f'Could not find a definition for {search.rstrip(".")}.')


def _parse_args(args):
    entry = int(args[0]) if len(args) == 2 else 1
    search = args[-1]
    return entry, search


async def _make_request(search):
    future = asyncio.get_event_loop().run_in_executor(
        None,
        lambda: requests.get(
            'https://api.urbandictionary.com/v0/define',
            headers={'User-Agent': config['user_agent']},
            params={'term': search},
            timeout=15,
        ),
    )

    try:
        return (await future).json()
    except (requests.RequestException, JSONDecodeError) as e:
        logger.error(f'Failed to query UrbanDictionary: {e}')
        raise BotError('Failed to query UrbanDictionary.')


def _get_definition(response, entry):
    return (
        re.sub(
            r'\[(.*?)\]',
            r'\1',
            sorted(
                response['list'],
                key=lambda x: int(x['thumbs_up']) - int(x['thumbs_down']),
                reverse=True,
            )[entry - 1]['definition'],
        )
        .strip()
        .replace('\n', ' ')
    )
