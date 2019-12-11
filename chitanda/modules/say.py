from chitanda.decorators import args, register


@register('say')
@args(r'(.+)')
async def call(message):
    """Repeats whatever the command was followed by."""
    return message.args[0]
