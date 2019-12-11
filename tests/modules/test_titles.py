import pytest
from mock import Mock

from chitanda.listeners import IRCListener
from chitanda.modules.titles import title_handler
from chitanda.util import Message


@pytest.mark.asyncio
async def test_title_handler(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.titles.config', {'user_agent': 'chitanda'}
    )
    requests = Mock(RequestException=Exception)
    requests.get.return_value.raw.read.return_value = DEMO_RESPONSE.encode(
        'utf-8'
    )
    monkeypatch.setattr('chitanda.modules.titles.requests', requests)

    'Title: azul\'s website!' == [
        r
        async for r in title_handler(
            Message(
                bot=None,
                listener=Mock(spec=IRCListener),
                target=None,
                author=None,
                contents='Hi this is my website! https://d.az',
                private=False,
            )
        )
    ][0]


@pytest.mark.asyncio
async def test_title_handler_no_title(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.titles.config', {'user_agent': 'chitanda'}
    )

    assert not [
        r
        async for r in title_handler(
            Message(
                bot=None,
                listener=Mock(spec=IRCListener),
                target=None,
                author=None,
                contents=(
                    'Hi this is my website! htps://d.az/oops/messed/it/up'
                ),
                private=False,
            )
        )
    ]


DEMO_RESPONSE = """
<!DOCTYPE html>
<html>
<head>
  <title>azul's website</title>
  <link href="static/index.css" rel="stylesheet" type="text/css" media="all">
  <meta name="viewport" content="width=device-width, initial-scale=1">
</head>

<body>
  heres some bod
</body>
"""
