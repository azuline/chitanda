from json import JSONDecodeError

import pytest
from mock import Mock

from chitanda.errors import BotError
from chitanda.modules.urbandictionary import (
    _get_definition,
    _make_request,
    _parse_args,
    call,
)
from chitanda.util import Message

# Demo response at bottom of file.


@pytest.mark.asyncio
async def test_call(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.urbandictionary.config', {'user_agent': 'chitanda'}
    )
    monkeypatch.setattr(
        'chitanda.modules.urbandictionary.requests',
        Mock(
            get=Mock(return_value=(Mock(json=lambda: DEMO_RESPONSE))),
            RequestException=Exception,
        ),
    )
    assert 'def2' == await call(
        Message(
            bot=None,
            listener=None,
            target=None,
            author=None,
            contents='2 azul',
            private=False,
        )
    )


@pytest.mark.parametrize(
    'args, return_',
    [
        (['search value'], (1, 'search value')),
        ([5, 'search value'], (5, 'search value')),
    ],
)
def test_parse_args(args, return_):
    assert return_ == _parse_args(args)


@pytest.mark.asyncio
async def test_make_request(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.urbandictionary.config', {'user_agent': 'chitanda'}
    )
    monkeypatch.setattr(
        'chitanda.modules.urbandictionary.requests',
        Mock(
            get=Mock(
                return_value=(Mock(json=lambda: {'text': 'idontwantthis'}))
            ),
            RequestException=Exception,
        ),
    )
    assert {'text': 'idontwantthis'} == await _make_request('term')


@pytest.mark.asyncio
async def test_make_request_error(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.urbandictionary.config', {'user_agent': 'chitanda'}
    )
    monkeypatch.setattr(
        'chitanda.modules.urbandictionary.requests',
        Mock(
            get=Mock(side_effect=JSONDecodeError), RequestException=Exception
        ),
    )
    with pytest.raises(BotError):
        await _make_request('term')


def test_get_definition():
    assert 'a definition for 3' == _get_definition(DEMO_RESPONSE, 3)


DEMO_RESPONSE = {
    'list': [
        {
            'definition': 'def1',
            'permalink': 'http://azul.urbanup.com/1',
            'thumbs_up': 130,
            'sound_urls': [],
            'author': 'author1',
            'word': 'Azul',
            'defid': 1,
            'current_vote': '',
            'written_on': '2019-10-12T00:00:00.000Z',
            'example': 'example1',
            'thumbs_down': 31,
        },
        {
            'definition': '[def2]',
            'permalink': 'http://azul.urbanup.com/2',
            'thumbs_up': 112,
            'sound_urls': [],
            'author': 'author2',
            'word': 'Azul',
            'defid': 2,
            'current_vote': '',
            'written_on': '2009-08-07T00:00:00.000Z',
            'example': 'example2',
            'thumbs_down': 64,
        },
        {
            'definition': 'a definition [for] [3]',
            'permalink': 'http://azul.urbanup.com/3',
            'thumbs_up': 130,
            'sound_urls': [],
            'author': 'author3',
            'word': 'Azul',
            'defid': 3,
            'current_vote': '',
            'written_on': '2013-10-16T00:00:00.000Z',
            'example': '',
            'thumbs_down': 128,
        },
    ]
}
