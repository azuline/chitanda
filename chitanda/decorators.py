import functools
import re
import sys
from inspect import isasyncgenfunction

from chitanda.errors import BotError


def register(trigger):
    def decorator(func):
        from chitanda.bot import Chitanda

        Chitanda.commands[trigger] = sys.modules[func.__module__]
        return functools.wraps(func)(func)

    return decorator


def args(*regexes):
    regexes = [
        re.compile(r) if not isinstance(r, re.Pattern) else r for r in regexes
    ]

    def decorator(func):
        @functools.wraps(func)
        def wrapper(message):
            for regex in regexes:
                match = regex.match(message.contents)
                if match:
                    message.args = match.groups()
                    return func(message)
            else:
                raise BotError('Invalid arguments.')

        return wrapper

    return decorator


def admin_only(func):
    setattr(func, 'admin_only', True)

    if isasyncgenfunction(func):

        @functools.wraps(func)
        async def wrapper(message):
            if not await message.listener.is_admin(message.author):
                raise BotError('Unauthorized.')
            async for r in func(message):
                yield r

    else:

        @functools.wraps(func)
        async def wrapper(message):
            if not await message.listener.is_admin(message.author):
                raise BotError('Unauthorized.')
            return await func(message)

    return wrapper


def auth_only(func):
    setattr(func, 'auth_only', True)

    if isasyncgenfunction(func):

        @functools.wraps(func)
        async def wrapper(message):
            message.username = await message.listener.is_authed(message.author)
            if not message.username:
                raise BotError('Identify with NickServ to use this command.')
            async for r in func(message):
                yield r

    else:

        @functools.wraps(func)
        async def wrapper(message):
            message.username = await message.listener.is_authed(message.author)
            if not message.username:
                raise BotError('Identify with NickServ to use this command.')
            return await func(message)

    return wrapper


def channel_only(func):
    setattr(func, 'channel_only', True)

    @functools.wraps(func)
    def wrapper(message):
        if not message.private:
            return func(message)
        raise BotError('This command can only be run in a channel.')

    return wrapper


def private_message_only(func):
    setattr(func, 'private_message_only', True)

    @functools.wraps(func)
    def wrapper(message):
        if message.private:
            return func(message)
        raise BotError('This command can only be run in a private message.')

    return wrapper


def allowed_listeners(*listeners):
    def decorator(func):
        setattr(func, 'listeners', listeners)

        @functools.wraps(func)
        def wrapper(message):
            if any(isinstance(message.listener, l) for l in listeners):
                return func(message)
            raise BotError('This command cannot be run on this listener.')

        return wrapper

    return decorator
