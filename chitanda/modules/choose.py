import re
from random import choice, randint

from chitanda.decorators import register
from chitanda.errors import BotError


@register('choose')
async def call(message):
    """Chooses one of many provided options."""
    match = re.match(r'(\d+) *- *(\d+)', message.contents)
    if match:
        return randint(int(match[1]), int(match[2]))
    elif ',' in message.contents:
        return choice([c.strip() for c in message.contents.split(',') if c])
    elif ' ' in message.contents:
        return choice([c.strip() for c in message.contents.split(' ') if c])
    raise BotError('No options found.')
