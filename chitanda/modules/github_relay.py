import asyncio
import hashlib
import hmac
import logging
import sys

from aiohttp import web
from discord import Embed

from chitanda.config import config
from chitanda.errors import BotError, InvalidListener
from chitanda.listeners import DiscordListener
from chitanda.util import get_listener, trim_message

logger = logging.getLogger(__name__)


def setup(bot):
    if not hasattr(bot, "_github_webserver_create"):
        bot.web_application.router.add_route(
            "POST",
            "/github",
            lambda request, bot=bot, **kwargs: (
                sys.modules[__name__]._handle_request(bot, request, **kwargs)
            ),  # Allow for hot-reloading to change outout.
        )
        bot._github_webserver_create = True


async def _handle_request(bot, request, **kwargs):
    try:
        logger.info("Received request from GitHub webhook.")
        if not _check_signature(await request.text(), request.headers):
            logger.info("GitHub request contained invalid signature, ignoring.")
            raise BotError("Invalid signature.")

        payload = await request.json()
        repo_cfgs = _get_repo_cfgs(payload["repository"]["id"])
        logger.info('Event for repository {payload["repository"]["name"]}.')
        event_handler = _get_event_handler(request.headers)

        for cfg in repo_cfgs:
            asyncio.ensure_future(
                event_handler(get_listener(bot, cfg["listener"]), payload, cfg)
            )

        return web.Response(body="Received.")
    except InvalidListener:
        return web.Response(body="Invalid listener configured.", status=500)
    except BotError as e:
        return web.Response(body=e.args[0], status=500)


def _check_signature(payload, headers):
    secret = config["github_relay"]["secret"]
    if not secret:
        return True

    expected_sig = hmac.new(
        key=secret.encode(), msg=payload.encode(), digestmod=hashlib.sha1
    ).hexdigest()
    try:
        return hmac.compare_digest(f"sha1={expected_sig}", headers["X-Hub-Signature"])
    except KeyError:
        raise BotError("Expected signature.")


def _get_repo_cfgs(repository_id):
    try:
        return config["github_relay"]["relays"][str(repository_id)]
    except KeyError:
        logger.info("GitHub request's repository is not tracked, ignoring.")
        raise BotError("Untracked repository.")


def _get_event_handler(headers):
    events = {
        "push": handle_push,
        "issues": handle_issue,
        "pull_request": handle_pull_request,
    }

    try:
        return events[headers["X-Github-Event"]]
    except KeyError:
        logger.info("GitHub request's event is unsupported, ignoring.")
        raise BotError("Unsupported event.")


async def handle_push(listener, payload, cfg):
    branch = payload["ref"].split("/")[2]

    if payload["ref"].split("/")[1] == "tags":
        logger.info("Received tag push event.")
        return await listener.message(
            target=cfg["channel"],
            message=(
                f'New tag {branch} tracking {payload["before"][:8]} pushed '
                f'to {payload["repository"]["name"]}'
            ),
        )

    if cfg["branches"] and branch not in cfg["branches"]:
        return logger.info(f"Push event was for untracked branch {branch}.")

    logger.info("Received push to branch event.")
    if isinstance(listener, DiscordListener):
        await _relay_push_discord(listener, cfg["channel"], payload, branch)
    else:
        await _relay_push(listener, cfg["channel"], payload, branch)


async def _relay_push_discord(listener, channel, payload, branch):
    embed = Embed(title=_construct_push_message(payload, branch))
    embed.add_field(name="Compare", value=payload["compare"], inline=False)
    for commit in payload["commits"]:
        embed.add_field(
            name=(
                f'{commit["author"]["username"]} - ' + trim_message(commit["message"])
            ),
            value=commit["url"].replace(commit["id"], commit["id"][:8]),
            inline=False,
        )
    await listener.message(target=channel, message=embed, embed=True)


async def _relay_push(listener, channel, payload, branch):
    await listener.message(
        target=channel, message=_construct_push_message(payload, branch)
    )
    await listener.message(target=channel, message=f'Compare - {payload["compare"]}')
    for commit in payload["commits"]:
        await listener.message(
            target=channel, message=_construct_commit_message(commit)
        )


def _construct_push_message(payload, branch):
    return (
        f'{_get_num_commits(payload["commits"])} commit(s) pushed to '
        f'{payload["repository"]["name"]}/{branch} by '
        f'{payload["pusher"]["name"]}'
    )


def _construct_commit_message(commit):
    chash = commit["id"][:8]
    url = commit["url"].replace(commit["id"], chash)
    return (
        f'{chash} - {commit["author"]["username"]} - '
        f'{trim_message(commit["message"])} - {url}'
    )


async def handle_issue(listener, payload, cfg):
    logger.info(f'Received a {payload["action"]} issue event.')
    await listener.message(
        target=cfg["channel"],
        message=(
            f'{payload["sender"]["login"]} {payload["action"]} issue '
            f'{payload["issue"]["number"]} in '
            f'{payload["repository"]["name"]} - '
            f'{trim_message(payload["issue"]["title"], 200)} - '
            f'{payload["issue"]["html_url"]}'
        ),
    )


async def handle_pull_request(listener, payload, cfg):
    logger.info(f'Received a {payload["action"]} pull request event.')
    await listener.message(
        target=cfg["channel"],
        message=(
            f'{payload["sender"]["login"]} {payload["action"]} pull request '
            f'{payload["pull_request"]["number"]} in '
            f'{payload["repository"]["name"]} - '
            f'{trim_message(payload["pull_request"]["title"], 200)} - '
            f'{payload["pull_request"]["html_url"]}'
        ),
    )


def _get_num_commits(commits):
    return "20+" if len(commits) == 20 else len(commits)
