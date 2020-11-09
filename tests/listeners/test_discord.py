from asyncio import Future
from unittest.mock import AsyncMock, Mock, patch

import pytest

from chitanda.listeners import DiscordListener


@pytest.mark.asyncio
async def test_discord_listener_message():
    mock = Mock(return_value=Mock(send=AsyncMock(return_value=123)))
    with patch.object(DiscordListener, "get_channel", mock) as gc:
        listener = DiscordListener(Mock())
        await listener.message(123, "message")
        assert gc.return_value.send.called_with(content="message")
        assert not listener.message_queue[123]
        assert not listener.message_lock[123]


@pytest.mark.asyncio
async def test_discord_listener_message_embed():
    mock = Mock(return_value=Mock(send=AsyncMock(return_value=123)))
    with patch.object(DiscordListener, "get_channel", mock) as gc:
        listener = DiscordListener(Mock())
        await listener.message(123, "message", embed=True)
        assert gc.return_value.send.called_with(embed="message")


@pytest.mark.asyncio
async def test_discord_listener_message_private():
    with patch.object(
        DiscordListener, "get_dm_channel_id", return_value=AsyncMock(return_value=789)
    ):
        mock = Mock(return_value=Mock(send=AsyncMock(return_value=123)))
        with patch.object(DiscordListener, "get_channel", mock) as gc:
            listener = DiscordListener(Mock())
            await listener.message(123, "message", private=True)
            assert gc.called_with(789)
            assert gc.return_value.send.called_with(embed="message")


@pytest.mark.asyncio
async def test_discord_listener_error():
    with patch.object(DiscordListener, "get_channel") as gc:
        gc.return_value.send.return_value = Future()
        gc.return_value.send.return_value.set_exception(Exception)
        listener = DiscordListener(Mock())
        with pytest.raises(Exception):
            await listener.message(123, "message")
        assert not listener.message_lock[123]


@pytest.mark.asyncio
async def test_get_dm_channel_id():
    discord_user = Mock(dm_channel=Mock(id=123))

    with patch.object(
        DiscordListener,
        "fetch_user",
        AsyncMock(return_value=discord_user),
    ):
        assert 123 == await DiscordListener(Mock()).get_dm_channel_id(1)
        discord_user.create_dm.assert_not_called()


@pytest.mark.asyncio
async def test_get_dm_channel_id_create_dm():
    class FakeDiscordUser:
        dm_channel = False

        async def create_dm(self):
            self.dm_channel = Mock(id=123)

    with patch.object(
        DiscordListener,
        "fetch_user",
        AsyncMock(return_value=FakeDiscordUser()),
    ):
        assert 123 == await DiscordListener(Mock()).get_dm_channel_id(1)


@pytest.mark.asyncio
async def test_on_message():
    bot = Mock(handle_message=AsyncMock(return_value=None))
    message = Mock(author=Mock(id=1, bot=False), channel=Mock(id=2), content="abc")

    listener = DiscordListener(bot)
    await listener.on_message(message)
    bot.handle_message.assert_called()


@pytest.mark.asyncio
async def test_on_message_bot():
    bot = Mock()
    bot.handle_message.return_value = AsyncMock(return_value=None)
    message = Mock(author=Mock(id=1, bot=True), channel=Mock(id=2), content="abc")

    listener = DiscordListener(bot)
    await listener.on_message(message)
    bot.handle_message.assert_not_called()


@pytest.mark.asyncio
async def test_is_admin(monkeypatch):
    listener = DiscordListener(None)
    monkeypatch.setattr(
        "chitanda.listeners.discord.config",
        {"admins": {str(listener): ["azul"]}},
    )
    assert await listener.is_admin("azul")


@pytest.mark.asyncio
async def test_is_not_admin(monkeypatch):
    listener = DiscordListener(None)
    monkeypatch.setattr(
        "chitanda.listeners.discord.config",
        {"admins": {str(listener): ["zad"]}},
    )
    assert not await listener.is_admin("azul")
