import logging
import re
from functools import singledispatch

import aiohttp
from discord import AsyncWebhookAdapter, Webhook

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
    await _relay(
        response.bot,
        response.listener,
        response.target,
        response.contents,
    )


async def _relay(bot, listener, target, contents, source=None):
    targets = _get_linked_targets(listener, target)
    for target in targets:
        target_listener = get_listener(bot, target["listener"])
        for (author, message) in _get_relay_messages(listener, contents, source):
            await _relay_message(target_listener, target, author, message)


def _get_linked_targets(listener, target):
    """
    Get all targets that are linked to the message source.
    """
    targets = []
    for link in config["relay"]:
        link = link.copy()
        for i, link_target in enumerate(link):
            eq_listener = link_target["listener"] == str(listener)
            eq_target = link_target["channel"] == str(target)
            if eq_listener and eq_target:
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
def _get_relay_messages_discord(listener, contents, source):
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

        attachments = [a.url for a in source.raw.attachments]

        if contents:
            return (
                (source.raw.author.display_name, c) for c in [contents, *attachments]
            )
        return ((source.raw.author.display_name, c) for c in attachments)

    return ((None, contents),)


@singledispatch
async def _relay_message(listener, target, author, message):
    """
    This relays the message to the target.
    """
    await listener.message(target["channel"], f"<{author}> {message}")


@_relay_message.register(IRCListener)
async def _relay_irc(listener, target, author, message):
    """
    For IRC, color the author name by taking the modulo of a hash of the author
    name. This remains deterministic until the bot is restarted (or maybe until
    the module is reloaded, not sure).
    """
    if author:
        color = abs(hash(author)) % 12 + 2
        author = f"\x03{color:02d}\x02<{author[:1]}\x02\x02{author[1:]}>\x02\x0F"
        message = f"{author} {message}"

    await listener.message(target["channel"], message)


@_relay_message.register(DiscordListener)
async def _relay_discord(listener, target, author, message):
    """
    For Discord, relay the message using a webhook. Requires server admin to
    configure a webhook endpoint.
    """
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(
            target["webhook"],
            adapter=AsyncWebhookAdapter(session),
        )

        await webhook.send(
            content=await _substitute_discord_nicknames(listener, target, message),
            username=author,
            avatar_url=await _locate_sender_avatar_url(listener, target, author),
        )


async def _locate_sender_avatar_url(listener, target, author):
    for m in await listener.find_prefix_matches(int(target["channel"]), author):
        return m.avatar_url

    return None


async def _substitute_discord_nicknames(listener, target, message):
    if "@" in message:
        for match in re.finditer("@([^ ]+)", message):
            members = await listener.find_prefix_matches(
                int(target["channel"]), match[1]
            )
            for m in members:
                message_name = message[
                    match.start(1) : match.start(1) + len(m.display_name)
                ]
                if m.display_name.lower() == message_name.lower():
                    message = message.replace(
                        f"@{m.display_name.lower()}", f"<@{m.id}>"
                    )

    return message
