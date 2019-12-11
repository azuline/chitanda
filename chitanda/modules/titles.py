import asyncio
import html
import logging
import re

import requests

from chitanda.config import config
from chitanda.listeners import IRCListener
from chitanda.util import trim_message

logger = logging.getLogger(__name__)

URL_REGEX = re.compile(r'.*(https?:\/\/[^ ]+)')
TITLE_REGEX = re.compile(r'<title>(.*?)<\\?/title>')
LB_REGEX = re.compile(r'\r|\n')


def setup(bot):  # pragma: no cover
    bot.message_handlers.append(title_handler)


async def title_handler(message):
    if isinstance(message.listener, IRCListener) and not message.private:
        matches = URL_REGEX.search(message.contents)
        if not matches:
            return

        for match in matches.groups():
            title = await _get_title(match)
            if title:
                yield title
                logger.info(
                    f'Title relayed from {match} in {message.target} '
                    f'from {message.listener}'
                )


async def _get_title(url):
    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: requests.get(
                url,
                headers={'User-Agent': config['user_agent']},
                stream=True,
                timeout=5,
            ),
        )
        data = response.raw.read(512000, decode_content=True).decode('utf-8')
    except (requests.RequestException, UnicodeDecodeError):
        return

    match = TITLE_REGEX.search(' '.join(LB_REGEX.split(html.unescape(data))))
    if match:
        return f'Title: {trim_message(match[1].strip(), length=400)}'
