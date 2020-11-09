from discord import Embed

from chitanda.config import config
from chitanda.decorators import args, register
from chitanda.listeners import DiscordListener


def setup(bot):  # pragma: no cover
    bot.message_handlers.append(alias_handler)


async def alias_handler(message):
    if not message.contents.startswith(config["trigger_character"]):
        return

    cont = message.contents[1:]
    for trigger, repl in _get_aliases(message.listener):
        if cont == trigger or cont.startswith(f"{trigger} "):
            message.contents = config["trigger_character"] + cont.replace(
                trigger, repl, 1
            )


@register("aliases")
@args(r"$")
async def call(message):
    """Sends a private message detailing the command aliases."""
    if isinstance(message.listener, DiscordListener):
        embed = Embed(title="Aliases")
        for alias, command in _get_aliases(message.listener):
            embed.add_field(
                name=f'{config["trigger_character"]}{alias}',
                value=f'{config["trigger_character"]}{command}',
                inline=False,
            )

        yield {
            "target": message.author,
            "message": embed,
            "private": True,
            "embed": True,
        }
    else:
        yield {"target": message.author, "message": "Aliases:"}
        for alias, command in _get_aliases(message.listener):
            yield {
                "target": message.author,
                "message": (
                    f'{config["trigger_character"]}{alias} --> '
                    f'{config["trigger_character"]}{command}'
                ),
            }


def _get_aliases(listener):
    aliases = {
        **config["aliases"].get("global", {}),
        **config["aliases"].get(str(listener), {}),
    }
    return sorted(aliases.items(), key=lambda t: len(t[0]), reverse=True)
