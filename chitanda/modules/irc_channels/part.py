from chitanda.decorators import admin_only, allowed_listeners, args, register
from chitanda.errors import BotError
from chitanda.listeners import IRCListener


@register('part')
@allowed_listeners(IRCListener)
@args(r'$', r'([#&][^\x07\x2C\s]{,199})$')
@admin_only
async def call(message):
    """Part a channel."""
    if message.args:
        await message.listener.part(message.args[0])
        return f'Attempted to part {message.args[0]}.'
    elif message.target != message.author:
        await message.listener.part(message.target)
    else:
        raise BotError('This command must be ran in a channel.')
