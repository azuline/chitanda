import pytest

from chitanda.modules.say import call
from chitanda.util import Message


@pytest.mark.asyncio
async def test_say():
    assert 'message' == await call(
        Message(
            bot=None,
            listener=None,
            target=None,
            author=None,
            contents='message',
            private=False,
        )
    )
