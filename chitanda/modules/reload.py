import logging

from chitanda.config import config
from chitanda.decorators import admin_only, args, register
from chitanda.errors import BotError
from chitanda.loader import load_commands

logger = logging.getLogger(__name__)


@register('reload')
@args(r'$')
@admin_only
async def call(message):
    """Hot reload the bot's config and modules."""
    try:
        config.reload()
    except Exception as e:  # noqa: E203
        logger.error(f'Error reloading config: {e}')
        raise BotError('Couldn\'t reload config.')

    try:
        load_commands(message.bot, run_setup=False)
    except Exception as e:  # noqa: E203
        logger.error(f'Error reloading modules: {e}')
        raise BotError('Couldn\'t reload modules.')

    return 'Commands reloaded.'
