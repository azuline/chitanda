import logging
import re
from functools import singledispatch

from chitanda.config import config
from chitanda.listeners import DiscordListener, IRCListener
from chitanda.util import get_listener

logger = logging.getLogger(__name__)


def setup(bot):  # pragma: no cover
    bot.message_handlers.append(on_message)
    bot.response_handlers.append(on_response)


async def on_message(message):
    await _relay(
        message.bot,
        message.listener,
        message.target,
        message.contents,
        source=message,
    )


async def on_response(response):
    if not response.relayed:  # Don't relay bot responses that are relays.
        await _relay(
            response.bot, response.listener, response.target, response.contents
        )


async def _relay(bot, listener, target, contents, source):
    targets = _get_linked_targets(listener, target)
    for target in targets:
        target_listener = get_listener(bot, target["listener"])
        for (author, message) in _get_relay_messages(listener, contents, source):
            await _relay_message(target_listener, bot, target, author, message)


def _get_linked_targets(listener, target):
    """
    Get all targets that are linked to the message source.
    """
    targets = []
    for link in config["relay"]:
        link = link.copy()
        for i, target in enumerate(link):
            if target["listener"] == str(listener) and target["target"] == target:
                del link[i]
                targets += link
                break

    return targets


@singledispatch
def _get_relay_messages(listener, contents, source):
    """
    Get the messages that need to be relayed. By default, return the source
    author and message contents.
    """
    if source:
        return ((source.author, contents),)
    return ((None, contents),)


@_get_relay_messages.register(DiscordListener)
def _(listener, contents, source):
    """
    This handles getting the messages that need to be relayed when the source
    is Discord. It processes the messages to remove Discord-specific
    formatting and replaces Discord identifiers with user-readable strings.
    """
    contents = re.sub(r"<a?:([^:]+):\d{18}>", r":\1:", contents)  # Emojis.

    if source:
        # Replace all mentions with the user's nick.
        for mention in source.raw.mentions:
            contents = re.sub(
                f"<@!?{mention.id}>", f"@{mention.display_name}", contents
            )

        attachments = [a["url"] for a in source.raw.attachments]

        return ((source.raw.author.display_name, c) for c in [contents, *attachments])

    return ((None, contents),)


@singledispatch
async def _relay_message(listener, bot, target, author, message):
    """
    This relays the message to the target.
    """
    await listener.message(target, f"<{author}> message")


@_relay_message.register(IRCListener)
async def _(listener, bot, target, author, message):
    """
    For IRC, color the author name by taking the modulo of a hash of the author
    name. This remains deterministic until the bot is restarted (or maybe until
    the module is reloaded, not sure).
    """
    color = abs(hash(author)) % 12 + 2
    author = f"\x03{color:02d}\x02<{author[:1]}\x02\x02{author[1:]}>\x02\x0F"
    await listener.message(target, author, message)


@_relay_message.register(DiscordListener)
async def _(listener, bot, target, author, message):
    """
    For Discord, relay the message using a webhook. Requires server admin to
    configure a webhook endpoint.
    """
    pass  # Use webhook.
