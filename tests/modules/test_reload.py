from unittest.mock import AsyncMock, Mock

import pytest

from chitanda.errors import BotError
from chitanda.modules.reload import call
from chitanda.util import Message


@pytest.mark.asyncio
async def test_reload(monkeypatch):
    monkeypatch.setattr("chitanda.modules.reload.config", Mock())
    monkeypatch.setattr("chitanda.modules.reload.load_commands", Mock())
    assert "Commands reloaded." == await call(
        Message(
            bot=None,
            listener=Mock(is_admin=AsyncMock(return_value=True)),
            target=None,
            author=None,
            contents="",
            private=False,
        )
    )


@pytest.mark.asyncio
async def test_reload_error_config(monkeypatch):
    config = Mock()
    config.reload.side_effect = BotError
    monkeypatch.setattr("chitanda.modules.reload.config", config)
    monkeypatch.setattr("chitanda.modules.reload.load_commands", Mock())
    with pytest.raises(BotError):
        await call(
            Message(
                bot=None,
                listener=Mock(is_admin=AsyncMock(return_value=True)),
                target=None,
                author=None,
                contents="",
                private=False,
            )
        )


@pytest.mark.asyncio
async def test_reload_error_commands(monkeypatch):
    load = Mock(side_effect=BotError)
    monkeypatch.setattr("chitanda.modules.reload.config", Mock())
    monkeypatch.setattr("chitanda.modules.reload.load_commands", load)
    with pytest.raises(BotError):
        await call(
            Message(
                bot=None,
                listener=Mock(is_admin=AsyncMock(return_value=True)),
                target=None,
                author=None,
                contents="",
                private=False,
            )
        )
