from asyncio import Future, coroutine

import pytest
from mock import Mock, patch

from chitanda.listeners import DiscordListener


@pytest.mark.asyncio
async def test_discord_listener_message():
    with patch.object(DiscordListener, 'get_channel') as gc:
        gc.return_value.send.return_value = Future()
        gc.return_value.send.return_value.set_result(123)
        listener = DiscordListener(Mock())
        await listener.message(123, 'message')
        assert gc.return_value.send.called_with(content='message')
        assert not listener.message_queue[123]
        assert not listener.message_lock[123]


@pytest.mark.asyncio
async def test_discord_listener_message_embed():
    with patch.object(DiscordListener, 'get_channel') as gc:
        gc.return_value.send.return_value = Future()
        gc.return_value.send.return_value.set_result(123)
        listener = DiscordListener(Mock())
        await listener.message(123, 'message', embed=True)
        assert gc.return_value.send.called_with(embed='message')


@pytest.mark.asyncio
async def test_discord_listener_message_private():
    with patch.object(
        DiscordListener, 'get_dm_channel_id', return_value=Future()
    ) as gdmcid:
        with patch.object(DiscordListener, 'get_channel') as gc:
            gdmcid.return_value.set_result('789')
            gc.return_value.send.return_value = Future()
            gc.return_value.send.return_value.set_result(123)
            listener = DiscordListener(Mock())
            await listener.message(123, 'message', private=True)
            assert gc.called_with(789)
            assert gc.return_value.send.called_with(embed='message')


@pytest.mark.asyncio
async def test_discord_listener_error():
    with patch.object(DiscordListener, 'get_channel') as gc:
        gc.return_value.send.return_value = Future()
        gc.return_value.send.return_value.set_exception(Exception)
        listener = DiscordListener(Mock())
        with pytest.raises(Exception):
            await listener.message(123, 'message')
        assert not listener.message_lock[123]


@pytest.mark.asyncio
async def test_get_dm_channel_id():
    with patch.object(
        DiscordListener, 'fetch_user', return_value=Future()
    ) as fu:
        discord_user = Mock(dm_channel=Mock(id=123))
        fu.return_value.set_result(discord_user)
        assert 123 == await DiscordListener(Mock()).get_dm_channel_id(1)
        discord_user.create_dm.assert_not_called()


@pytest.mark.asyncio
async def test_get_dm_channel_id_create_dm():
    class FakeDiscordUser:
        dm_channel = False

        async def create_dm(self):
            self.dm_channel = Mock(id=123)

    with patch.object(
        DiscordListener, 'fetch_user', return_value=Future()
    ) as fu:
        fu.return_value.set_result(FakeDiscordUser())
        assert 123 == await DiscordListener(Mock()).get_dm_channel_id(1)


@pytest.mark.asyncio
async def test_on_message():
    bot = Mock()
    bot.handle_message.return_value = coroutine(lambda **kwargs: None)()
    message = Mock(
        author=Mock(id=1, bot=False), channel=Mock(id=2), content='abc'
    )

    listener = DiscordListener(bot)
    await listener.on_message(message)
    bot.handle_message.assert_called()


@pytest.mark.asyncio
async def test_on_message_bot():
    bot = Mock()
    bot.handle_message.return_value = coroutine(lambda **kwargs: None)()
    message = Mock(
        author=Mock(id=1, bot=True), channel=Mock(id=2), content='abc'
    )

    listener = DiscordListener(bot)
    await listener.on_message(message)
    bot.handle_message.assert_not_called()


@pytest.mark.asyncio
async def test_is_admin(monkeypatch):
    listener = DiscordListener(None)
    monkeypatch.setattr(
        'chitanda.listeners.discord.config',
        {'admins': {str(listener): ['azul']}},
    )
    assert await listener.is_admin('azul')


@pytest.mark.asyncio
async def test_is_not_admin(monkeypatch):
    listener = DiscordListener(None)
    monkeypatch.setattr(
        'chitanda.listeners.discord.config',
        {'admins': {str(listener): ['zad']}},
    )
    assert not await listener.is_admin('azul')
