from chitanda.decorators import admin_only, allowed_listeners, args, register
from chitanda.listeners import IRCListener


@register('join')
@allowed_listeners(IRCListener)
@args(r'([#&][^\x07\x2C\s]{,199})$')
@admin_only
async def call(message):
    """Join a channel."""
    channel = message.args[0]
    await message.listener.join(channel)
    return f'Attempted to join {channel}.'
