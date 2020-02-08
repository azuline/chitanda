from asyncio import Future, coroutine

import pytest
from mock import Mock, patch

from chitanda.bot import Chitanda, NoCommandFound
from chitanda.errors import BotError
from chitanda.util import Message, Response


@patch('chitanda.bot.load_commands')
def test_load_webserver(_, monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})
    with patch.object(Chitanda, '_start_webserver'):
        with patch.object(Chitanda, 'connect'):
            chitanda = Chitanda()
            chitanda.start()
            assert chitanda.webserver is not None


@patch('chitanda.bot.load_commands')
def test_dont_load_webserver(_, monkeypatch):
    monkeypatch.setattr(
        'chitanda.bot.config', {'webserver': {'enable': False}}
    )
    with patch.object(Chitanda, '_start_webserver'):
        with patch.object(Chitanda, 'connect'):
            chitanda = Chitanda()
            chitanda.start()
            assert not hasattr(chitanda, 'webserver')


def test_start_webserver_invalid_port(monkeypatch):
    monkeypatch.setattr(
        'chitanda.bot.config', {'webserver': {'enable': True, 'port': '123a'}}
    )
    with patch.object(Chitanda, 'connect'):
        with pytest.raises(SystemExit):
            chitanda = Chitanda()
            chitanda._start_webserver()


def test_start_bot_with_listeners(monkeypatch):
    monkeypatch.setattr(
        'chitanda.bot.config',
        {
            'webserver': {'enable': True},
            'irc_servers': {'An IRC Server': 'details'},
            'discord_token': 'abcdefg',
        },
    )

    with patch.object(Chitanda, '_connect_irc') as conn_irc:
        with patch.object(Chitanda, '_connect_discord') as conn_discord:
            Chitanda().connect()

            conn_irc.assert_called()
            conn_discord.assert_called()


def test_start_bot_without_listeners(monkeypatch):
    monkeypatch.setattr(
        'chitanda.bot.config',
        {
            'webserver': {'enable': True},
            'irc_servers': {},
            'discord_token': None,
        },
    )

    with patch.object(Chitanda, '_connect_irc') as conn_irc:
        with patch.object(Chitanda, '_connect_discord') as conn_discord:
            Chitanda().connect()

            conn_irc.assert_not_called()
            conn_discord.assert_not_called()


@patch('chitanda.bot.IRCListener')
@patch('chitanda.bot.asyncio')
def test_connect_irc(asyncio, irc_listener, monkeypatch):
    monkeypatch.setattr(
        'chitanda.bot.config',
        {
            'webserver': {'enable': True},
            'irc_servers': {
                'hostname1': {
                    'nickname': 1,
                    'port': 1,
                    'tls': 1,
                    'tls_verify': 1,
                },
                'hostname2': {
                    'nickname': 1,
                    'port': 1,
                    'tls': 1,
                    'tls_verify': 1,
                },
            },
        },
    )

    chitanda = Chitanda()
    chitanda._connect_irc()
    assert 'hostname1' in chitanda.irc_listeners
    assert 'hostname2' in chitanda.irc_listeners


@patch('chitanda.bot.DiscordListener')
def test_connect_discord(discord_listener, monkeypatch):
    monkeypatch.setattr(
        'chitanda.bot.config',
        {'webserver': {'enable': True}, 'discord_token': 'token'},
    )
    chitanda = Chitanda()
    chitanda._connect_discord()
    assert discord_listener.return_value.run.called_with('token')


@pytest.mark.asyncio
async def test_handle_message(monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})
    chitanda = Chitanda()
    handle1 = coroutine(lambda *a, **k: True)
    handle2 = coroutine(lambda *a, **k: True)
    with patch.object(chitanda, 'message_handlers') as msg_handlers:
        with patch.object(
            chitanda, 'dispatch_command', return_value=Future()
        ) as dispatch:
            with patch.object(
                chitanda, 'handle_response', return_value=Future()
            ) as handler:
                dispatch.return_value.set_result(123)
                handler.return_value.set_result(123)

                msg_handlers.__iter__.return_value = [handle1, handle2]
                message = Message(chitanda, 1, 2, 3, 4, 5)
                await chitanda.handle_message(message)

                assert handler.call_count == 2
                dispatch.assert_called_once()


@pytest.mark.asyncio
async def test_handle_message_bot_error(monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})
    listener = Mock()
    listener.message.return_value = Future()
    listener.message.return_value.set_result(123)

    chitanda = Chitanda()
    with patch.object(chitanda, 'message_handlers') as msg_handlers:
        msg_handlers.__iter__.side_effect = BotError('test error')
        message = Message(chitanda, listener, 2, 'azul', 4, 5)
        await chitanda.handle_message(message)
        listener.message.assert_called_with(2, f'Error: test error')


@pytest.mark.asyncio
async def test_dispatch_command(monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})
    chitanda = Chitanda()
    command = Mock()
    command.call.return_value = 789
    listener = Mock()
    message = Message(chitanda, listener, 2, 3, 4, 5)

    with patch.object(message, 'call_command', return_value=789):
        with patch.object(
            chitanda, 'handle_response', return_value=Future()
        ) as handler:
            handler.return_value.set_result(123)

            await chitanda.dispatch_command(message)

            message.call_command.assert_called()
            listener.assert_not_called()
            handler.assert_called_with(789, source=message)


@pytest.mark.asyncio
async def test_dispatch_command_not_found(monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})
    chitanda = Chitanda()
    command = Mock()
    listener = Mock()
    message = Message(chitanda, listener, 2, 3, 4, 5)

    with patch.object(message, 'call_command', side_effect=NoCommandFound):
        with patch.object(
            Chitanda, 'handle_response', return_value=Future()
        ) as handler:
            handler.return_value.set_result(123)

            await chitanda.dispatch_command(message)

            command.call.assert_not_called()
            listener.assert_not_called()
            handler.assert_not_called()


@pytest.mark.asyncio
async def test_handle_response_async_generator(monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})

    async def generator():
        for i in [1, 2, 3]:
            yield i

    with patch.object(
        Chitanda, '_handle_response_message', return_value=Future()
    ) as handler:
        handler.return_value.set_result(123)
        chitanda = Chitanda()
        await chitanda.handle_response(generator(), 'a')
        assert [(1, 'a'), (2, 'a'), (3, 'a')] == [
            tuple(args) for args, _ in handler.call_args_list
        ]


@pytest.mark.asyncio
async def test_handle_response_generator(monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})

    async def generator():
        def subgenerator():
            for i in [1, 2, 3]:
                yield i

        return subgenerator()

    with patch.object(
        Chitanda, '_handle_response_message', return_value=Future()
    ) as handler:
        handler.return_value.set_result(123)
        chitanda = Chitanda()
        await chitanda.handle_response(generator(), 'a')
        assert [(1, 'a'), (2, 'a'), (3, 'a')] == [
            tuple(args) for args, _ in handler.call_args_list
        ]


@pytest.mark.asyncio
async def test_handle_plain_response(monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})

    async def function():
        return 3

    with patch.object(
        Chitanda, '_handle_response_message', return_value=Future()
    ) as handler:
        handler.return_value.set_result(123)
        chitanda = Chitanda()
        response = coroutine(lambda: 2)()
        await chitanda.handle_response(response, None)
        assert handler.called_with(2)


@pytest.mark.asyncio
async def test_handle_response_message_str(monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})
    listener = Mock()
    listener.message.return_value = Future()
    listener.message.return_value.set_result(123)

    with patch.object(
        Chitanda, 'call_response_handlers', return_value=Future()
    ) as caller:
        caller.return_value.set_result(123)

        chitanda = Chitanda()
        response = Response(chitanda, listener, 1, 'hi')
        await chitanda._handle_response_message(response, None)
        assert caller.called_with(response)
        assert listener.message.called_with(target=1, message='hi')


@pytest.mark.asyncio
async def test_handle_response_message_dict(monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})
    listener = Mock()
    listener.message.return_value = Future()
    listener.message.return_value.set_result(123)

    with patch.object(
        Chitanda, 'call_response_handlers', return_value=Future()
    ) as caller:
        caller.return_value.set_result(123)

        chitanda = Chitanda()
        response = Response(
            chitanda,
            listener,
            1,
            {'target': 1, 'message': 'hi', 'extra': 'cereal'},
        )

        await chitanda._handle_response_message(response, None)
        assert caller.called_with(response)
        assert listener.message.called_with(
            target=1, message='hi', extra='cereal'
        )


@pytest.mark.asyncio
async def test_call_response_handlers(monkeypatch):
    monkeypatch.setattr('chitanda.bot.config', {'webserver': {'enable': True}})
    handler1 = Mock(return_value=coroutine(lambda: True)())
    handler2 = Mock(return_value=coroutine(lambda: True)())
    chitanda = Chitanda()
    with patch.object(chitanda, 'response_handlers') as handlers:
        handlers.__iter__.return_value = [handler1, handler2]
        await chitanda.call_response_handlers('abc')
        handler1.assert_called_with('abc')
        handler2.assert_called_with('abc')
