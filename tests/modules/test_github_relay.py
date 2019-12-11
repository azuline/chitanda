from asyncio import coroutine

import pytest
from mock import Mock, patch

from chitanda.errors import BotError
from chitanda.modules.github_relay import (
    _check_signature,
    _construct_commit_message,
    _construct_push_message,
    _get_event_handler,
    _get_num_commits,
    _get_repo_cfgs,
    _handle_request,
    _relay_push,
    _relay_push_discord,
    handle_issue,
    handle_pull_request,
    handle_push,
)
from chitanda.modules.github_relay import setup as module_setup


def test_bot_setup():
    bot = Mock()
    delattr(bot, '_github_webserver_create')
    module_setup(bot)
    bot.web_application.router.add_route.assert_called()
    assert bot._github_webserver_create is True


def test_bot_already_setup():
    bot = Mock(_github_webserver_create=True)
    module_setup(bot)
    bot.web_application.router.add_route.assert_not_called()


@pytest.mark.asyncio
async def test_handle_request(monkeypatch):
    monkeypatch.setattr('chitanda.modules.github_relay.config', {})

    check_signature = Mock(return_value=True)
    get_repo_cfgs = Mock(
        return_value=[
            {'listener': 'BananaListener'},
            {'listener': 'AppleListener'},
        ]
    )
    get_event_handler = Mock(return_value=coroutine(lambda *args: True))
    get_listener = Mock()

    monkeypatch.setattr(
        'chitanda.modules.github_relay._check_signature', check_signature
    )
    monkeypatch.setattr(
        'chitanda.modules.github_relay._get_repo_cfgs', get_repo_cfgs
    )
    monkeypatch.setattr(
        'chitanda.modules.github_relay._get_event_handler', get_event_handler
    )
    monkeypatch.setattr(
        'chitanda.modules.github_relay.get_listener', get_listener
    )

    request = Mock(
        text=coroutine(lambda: True),
        json=coroutine(lambda: {'repository': {'id': 1}}),
    )

    await _handle_request(None, request)
    assert get_listener.call_count == 2


@pytest.mark.asyncio
async def test_handle_request_invalid_signature(monkeypatch):
    monkeypatch.setattr('chitanda.modules.github_relay.config', {})

    check_signature = Mock(return_value=False)
    get_repo_cfgs = Mock()

    monkeypatch.setattr(
        'chitanda.modules.github_relay._check_signature', check_signature
    )
    monkeypatch.setattr(
        'chitanda.modules.github_relay._get_repo_cfgs', get_repo_cfgs
    )
    monkeypatch.setattr(
        'chitanda.modules.github_relay._get_event_handler', Mock()
    )
    monkeypatch.setattr('chitanda.modules.github_relay.get_listener', Mock())

    request = Mock(
        text=coroutine(lambda: True),
        json=coroutine(lambda: {'repository': {'id': 1}}),
    )

    await _handle_request(None, request)
    get_repo_cfgs.assert_not_called()


def test_signature_not_configured(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.github_relay.config',
        {'github_relay': {'secret': None}},
    )
    assert _check_signature(None, None) is True


@patch('chitanda.modules.github_relay.hmac')
def test_signature(hmac, monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.github_relay.config',
        {'github_relay': {'secret': 'abc'}},
    )
    hmac.new = lambda *args, **kwargs: Mock(hexdigest=lambda: 'hi')
    hmac.compare_digest = lambda *args, **kargs: 'bye'
    assert 'bye' == _check_signature('hi', {'X-Hub-Signature': 'googly eyes'})


@patch('chitanda.modules.github_relay.hmac')
def test_signature_not_sent_by_github(hmac, monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.github_relay.config',
        {'github_relay': {'secret': 'abc'}},
    )
    hmac.new = lambda *args, **kwargs: Mock(hexdigest=lambda: 'hi')
    hmac.compare_digest = lambda *args, **kargs: 'bye'
    with pytest.raises(BotError):
        _check_signature('hi', {})


def test_get_repo_configs(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.github_relay.config',
        {'github_relay': {'relays': {'1': 'pears'}}},
    )

    assert _get_repo_cfgs(1) == 'pears'


def test_get_repo_configs_untracked(monkeypatch):
    monkeypatch.setattr(
        'chitanda.modules.github_relay.config',
        {'github_relay': {'relays': {'1': 'pears'}}},
    )

    with pytest.raises(BotError):
        _get_repo_cfgs(2)


def test_get_event_handler():
    handler = _get_event_handler({'X-Github-Event': 'pull_request'})
    assert handler == handle_pull_request


def test_get_event_handler_error():
    with pytest.raises(BotError):
        _get_event_handler({'X-Github-Event': 'la'})


@pytest.mark.asyncio
async def test_handle_push_tag(monkeypatch):
    listener = Mock()
    listener.message = Mock(
        return_value=coroutine(lambda *args, **kwargs: 345)()
    )

    relay_push_discord = Mock(return_value=coroutine(lambda: True)())
    relay_push = Mock(return_value=coroutine(lambda: True)())
    monkeypatch.setattr(
        'chitanda.modules.github_relay._relay_push_discord', relay_push_discord
    )
    monkeypatch.setattr(
        'chitanda.modules.github_relay._relay_push', relay_push
    )

    await handle_push(
        listener,
        payload={
            'ref': 'refs/tags/master',
            'before': 'abcdefghi',
            'repository': {'name': 'chitanda'},
        },
        cfg={'branches': ['master'], 'channel': 'hi'},
    )
    listener.message.assert_called()
    relay_push_discord.assert_not_called()
    relay_push.assert_not_called()


@pytest.mark.asyncio
async def test_handle_push(monkeypatch):
    relay_push_discord = Mock(return_value=coroutine(lambda: True)())
    relay_push = Mock(return_value=coroutine(lambda: True)())
    monkeypatch.setattr(
        'chitanda.modules.github_relay._relay_push_discord', relay_push_discord
    )
    monkeypatch.setattr(
        'chitanda.modules.github_relay._relay_push', relay_push
    )

    await handle_push(
        Mock(),
        payload={
            'ref': 'refs/heads/master',
            'before': 'abcdefghi',
            'repository': {'name': 'chitanda'},
        },
        cfg={'branches': ['master'], 'channel': 'hi'},
    )
    relay_push_discord.assert_not_called()
    relay_push.assert_called()


@pytest.mark.asyncio
async def test_handle_push_untracked_branch(monkeypatch):
    relay_push_discord = Mock(return_value=coroutine(lambda: True)())
    relay_push = Mock(return_value=coroutine(lambda: True)())
    monkeypatch.setattr(
        'chitanda.modules.github_relay._relay_push_discord', relay_push_discord
    )
    monkeypatch.setattr(
        'chitanda.modules.github_relay._relay_push', relay_push
    )

    await handle_push(
        Mock(),
        payload={
            'ref': 'refs/heads/dev',
            'before': 'abcdefghi',
            'repository': {'name': 'chitanda'},
        },
        cfg={'branches': ['master'], 'channel': 'hi'},
    )
    relay_push_discord.assert_not_called()
    relay_push.assert_not_called()


@pytest.mark.asyncio
async def test_relay_push_discord(monkeypatch):
    construct_push_message = Mock(return_value='title')
    monkeypatch.setattr(
        'chitanda.modules.github_relay._construct_push_message',
        construct_push_message,
    )
    listener = Mock(
        message=Mock(return_value=coroutine(lambda **kwargs: True)())
    )
    await _relay_push_discord(
        listener,
        '#chan',
        {
            'compare': 'comp',
            'commits': [
                {
                    'author': {'username': 'azul'},
                    'message': 'test github relay',
                    'url': 'https://github.com/thingy/1234567890',
                    'id': '1234567890',
                }
            ],
        },
        None,
    )
    assert listener.message.call_args[1]['message'].fields[0].value == 'comp'
    assert listener.message.call_args[1]['message'].fields[1].name == (
        'azul - test github relay'
    )
    assert listener.message.call_args[1]['message'].fields[1].value == (
        'https://github.com/thingy/12345678'
    )


@pytest.mark.asyncio
async def test_relay_push(monkeypatch):
    construct_push_message = Mock(return_value='title')
    construct_commit_message = Mock(return_value='commit')
    monkeypatch.setattr(
        'chitanda.modules.github_relay._construct_push_message',
        construct_push_message,
    )
    monkeypatch.setattr(
        'chitanda.modules.github_relay._construct_commit_message',
        construct_commit_message,
    )
    listener = Mock(
        message=Mock(return_value=coroutine(lambda **kwargs: True)())
    )
    await _relay_push(
        listener,
        '#chan',
        {
            'compare': 'comp',
            'commits': [
                {
                    'author': {'username': 'azul'},
                    'message': 'test github relay',
                    'url': 'https://github.com/thingy/1234567890',
                    'id': '1234567890',
                }
            ],
        },
        None,
    )
    assert listener.message.call_count == 3


def test_construct_push_message():
    assert '3 commit(s) pushed to chitanda/master by azul' == (
        _construct_push_message(
            payload={
                'commits': [None] * 3,
                'repository': {'name': 'chitanda'},
                'pusher': {'name': 'azul'},
            },
            branch='master',
        )
    )


def test_construct_commit_message():
    assert 'abcdefgh - azul - update github test - url/abcdefgh' == (
        _construct_commit_message(
            {
                'id': 'abcdefghijk',
                'author': {'username': 'azul'},
                'message': 'update github test',
                'url': 'url/abcdefghijk',
            }
        )
    )


@pytest.mark.asyncio
async def test_handle_issue():
    listener = Mock(
        message=Mock(return_value=coroutine(lambda **kwargs: True)())
    )
    await handle_issue(
        listener,
        payload={
            'sender': {'login': 'azul'},
            'action': 'opened',
            'issue': {'number': 8, 'title': 'fix bot', 'html_url': 'url//'},
            'repository': {'name': 'chitanda'},
        },
        cfg={'channel': '#chan'},
    )
    listener.message.assert_called_with(
        target='#chan',
        message='azul opened issue 8 in chitanda - fix bot - url//',
    )


@pytest.mark.asyncio
async def test_handle_pull_request():
    listener = Mock(
        message=Mock(return_value=coroutine(lambda **kwargs: True)())
    )
    await handle_pull_request(
        listener,
        payload={
            'sender': {'login': 'azul'},
            'action': 'opened',
            'pull_request': {
                'number': 8,
                'title': 'fix bot',
                'html_url': 'url//',
            },
            'repository': {'name': 'chitanda'},
        },
        cfg={'channel': '#chan'},
    )
    listener.message.assert_called_with(
        target='#chan',
        message=('azul opened pull request 8 in chitanda - fix bot - url//'),
    )


def test_get_num_commits():
    assert '20+' == _get_num_commits([None] * 20)
