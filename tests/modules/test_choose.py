import pytest

from chitanda.errors import BotError
from chitanda.modules.choose import call
from chitanda.util import Message


@pytest.mark.asyncio
async def test_choose_integer():
    response = await call(
        Message(
            bot=None,
            listener=None,
            target=None,
            author=None,
            contents="1 - 4",
            private=False,
        )
    )
    assert isinstance(response, int) and response >= 1 and response <= 4


@pytest.mark.asyncio
async def test_choose_string_comma():
    response = await call(
        Message(
            bot=None,
            listener=None,
            target=None,
            author=None,
            contents="a, b,    c",
            private=False,
        )
    )
    assert isinstance(response, str) and response in {"a", "b", "c"}


@pytest.mark.asyncio
async def test_choose_string_space():
    response = await call(
        Message(
            bot=None,
            listener=None,
            target=None,
            author=None,
            contents="a b    c",
            private=False,
        )
    )
    assert isinstance(response, str) and response in {"a", "b", "c"}


@pytest.mark.asyncio
async def test_choose_nothing():
    with pytest.raises(BotError):
        await call(
            Message(
                bot=None,
                listener=None,
                target=None,
                author=None,
                contents="abc",
                private=False,
            )
        )
