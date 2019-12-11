import inspect

from discord import Embed

from chitanda.config import config
from chitanda.decorators import args, register
from chitanda.listeners import DiscordListener


@register('help')
@args(r'$')
async def call(message):
    """Sends a private message detailing the available commands."""
    if isinstance(message.listener, DiscordListener):
        embed = Embed(title='Help!')
        for trigger, command in sorted(message.bot.commands.items()):
            if _applicable_listener(message.listener, command.call):
                embed.add_field(
                    name=f'{config["trigger_character"]}{trigger}',
                    value=_generate_help_text(command.call),
                    inline=False,
                )

        yield {
            'target': message.author,
            'message': embed,
            'private': True,
            'embed': True,
        }
    else:
        longest = max(len(t) for t in message.bot.commands)
        yield {'target': message.author, 'message': 'Help:'}
        for trigger, command in sorted(message.bot.commands.items()):
            if _applicable_listener(message.listener, command.call):
                yield {
                    'target': message.author,
                    'message': (
                        f'{config["trigger_character"]}'
                        f'{trigger.ljust(longest)} | '
                        f'{_generate_help_text(command.call)}'
                    ),
                }


def _applicable_listener(listener, call):
    return not hasattr(call, 'listeners') or type(listener) in call.listeners


def _generate_help_text(call):
    doc = inspect.getdoc(call)
    if hasattr(call, 'admin_only'):
        doc += ' (admin only)'
    if hasattr(call, 'auth_only'):
        doc += ' (requires authentication)'
    if hasattr(call, 'channel_only'):
        doc += ' (channel only)'
    if hasattr(call, 'private_message_only'):
        doc += ' (PM only)'
    return doc
