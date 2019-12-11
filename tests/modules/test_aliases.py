import pytest
from mock import Mock

from chitanda.listeners import DiscordListener
from chitanda.modules.aliases import alias_handler, call
from chitanda.util import Message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'alias, expanded', [('.a', '.apples'), ('.b', '.b'), ('.c', '.cookies')]
)
async def test_alias_handler(alias, expanded, monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.aliases.config',
        {
            'trigger_character': '.',
            'aliases': {
                'global': {'a': 'apples'},
                'ChocolateListener': {'b': 'bananas'},
                'BananaListener': {'c': 'cookies'},
            },
        },
    )
    message = Message(0, 'BananaListener', 0, 0, alias, 0)
    await alias_handler(message)  # Modifies message object.
    assert expanded == message.contents


@pytest.mark.asyncio
async def test_aliases(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.aliases.config',
        {
            'trigger_character': '.',
            'aliases': {
                'global': {'a': 'apples'},
                'ChocolateListener': {'b': 'bananas'},
                'BananaListener': {'c': 'cookies'},
            },
        },
    )

    response = [
        r
        async for r in call(
            Message(
                bot=None,
                listener='ChocolateListener',
                target=None,
                author='azul',
                contents='',
                private=False,
            )
        )
    ]

    assert response == [
        {'target': 'azul', 'message': 'Aliases:'},
        {'target': 'azul', 'message': '.a --> .apples'},
        {'target': 'azul', 'message': '.b --> .bananas'},
    ]


@pytest.mark.asyncio
async def test_aliases_discord(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.aliases.config',
        {
            'trigger_character': '.',
            'aliases': {'global': {'a': 'apples', 'b': 'bananas'}},
        },
    )

    response = [
        r
        async for r in call(
            Message(
                bot=None,
                listener=Mock(spec=DiscordListener),
                target=None,
                author='azul',
                contents='',
                private=False,
            )
        )
    ][0]

    assert response['message'].title == 'Aliases'
    assert response['message'].fields[0].name == '.a'
    assert response['message'].fields[0].value == '.apples'
    assert response['message'].fields[1].name == '.b'
    assert response['message'].fields[1].value == '.bananas'
