import asyncio
import logging
import re
from collections import defaultdict, deque
from functools import partial
from multiprocessing import Pipe, Process

from chitanda.decorators import args, channel_only, register
from chitanda.errors import BotError
from chitanda.listeners import DiscordListener, IRCListener
from chitanda.util import irc_unstyle, trim_message

logger = logging.getLogger(__name__)

PATTERN = r"(?:\.| )?s/(.*?)(?<!\\)/(.*?)(?:(?<!\\)/([gi]{,2})?)?$"
REGEX = re.compile(PATTERN)
REGEX_WITH_PREFIX = re.compile(r".sed +" + PATTERN)
TIMEOUT = 1


def setup(bot):  # pragma: no cover
    bot.message_handlers.append(on_message)
    bot.response_handlers.append(on_response)


async def on_message(message):
    if not message.private:
        _attach_message_log(message.listener)
        message_log = message.listener.message_log[message.target]
        match = REGEX.match(message.contents)
        if match:
            return await _substitute(match.groups(), message_log)
        elif not REGEX_WITH_PREFIX.match(message.contents):
            message_log.appendleft(
                _format_message(
                    message.contents,
                    message.formatted_author,
                    message.listener,
                )
            )


async def on_response(response):
    _attach_message_log(response.listener)
    response.listener.message_log[response.target].appendleft(
        _format_message(
            response.contents,
            _get_author(response.listener),
            response.listener,
        )
    )


def _attach_message_log(listener):
    if not hasattr(listener, "message_log"):
        listener.message_log = defaultdict(partial(deque, maxlen=1024))


def _get_author(listener):
    if isinstance(listener, DiscordListener):
        return f"<@{listener.user.id}>"
    elif isinstance(listener, IRCListener):
        return listener.nickname


@register("sed")
@channel_only
@args(REGEX)
async def call(message):
    """Find and replace a message in the message history."""
    return await _substitute(message.args, message.listener.message_log[message.target])


async def _substitute(match, message_log):
    flags = _parse_flags(match[2])
    regex = _compile_regex(match[0], flags)

    count = 0 if flags["global"] else 1

    response = await _find_and_replace(message_log, regex, match[1], count)
    return trim_message(response, length=400)


async def _find_and_replace(message_log, regex, repl, count):
    parent_connection, child_connection = Pipe()
    process = Process(
        target=_sed_and_send_value_over_conn,
        args=(child_connection, message_log, regex, repl, count),
    )
    process.start()
    logging.info(f"Started Process {process.pid} for sed command.")

    for _ in range(int(TIMEOUT / 0.02)):
        if process.exitcode is not None:
            logging.info(f"Process {process.pid} has completed its sed.")
            result = parent_connection.recv()
            parent_connection.close()
            return result
        await asyncio.sleep(0.02)

    logging.info(f"Process {process.pid}'s sed has timed out, killing...")
    process.kill()
    raise BotError("Regex substitution timed out.")


def _sed_and_send_value_over_conn(conn, message_log, regex, repl, count):
    try:
        for message in message_log:
            if regex.search(message):
                conn.send(regex.sub(repl, message, count=count))
                break
        else:
            conn.send("No matching message found.")
    except re.error:
        conn.send("Invalid regex substitution.")
    conn.close()


def _parse_flags(flags):
    return {
        "global": "g" in flags if flags else False,
        "nocase": "i" in flags if flags else False,
    }


def _compile_regex(regex, flags):
    try:
        if flags["nocase"]:
            return re.compile(regex, flags=re.IGNORECASE)
        return re.compile(regex)
    except re.error:  # noqa E722
        raise BotError(f"{regex} is not a valid regex.")


def _format_message(message, author, listener):
    if isinstance(listener, IRCListener):
        message = irc_unstyle(message)
    return f"<{author}> {message}"
