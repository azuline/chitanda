import pytest
from mock import Mock
from requests import RequestException

from chitanda.errors import BotError
from chitanda.modules.wolframalpha import call
from chitanda.util import Message


@pytest.mark.asyncio
async def test_call(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.wolframalpha.config',
        {'user_agent': 'chitanda', 'wolframalpha': {'appid': 'abc'}},
    )
    monkeypatch.setattr(
        'chitanda.modules.wolframalpha.requests',
        Mock(
            get=Mock(return_value=(Mock(text='its hot'))),
            RequestException=Exception,
        ),
    )
    assert 'its hot' == await call(
        Message(
            bot=None,
            listener=None,
            target=None,
            author=None,
            contents='hows the weather',
            private=False,
        )
    )


@pytest.mark.asyncio
async def test_call_error(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.wolframalpha.config',
        {'user_agent': 'chitanda', 'wolframalpha': {'appid': 'abc'}},
    )
    monkeypatch.setattr(
        'chitanda.modules.wolframalpha.requests',
        Mock(
            get=Mock(side_effect=RequestException),
            RequestException=RequestException,
        ),
    )
    with pytest.raises(BotError):
        await call(
            Message(
                bot=None,
                listener=None,
                target=None,
                author=None,
                contents='hows the weather',
                private=False,
            )
        )
