import asyncio
import logging
import sys
from types import AsyncGeneratorType, GeneratorType

from aiohttp import web

from chitanda.config import config
from chitanda.errors import BotError, NoCommandFound
from chitanda.listeners import DiscordListener, IRCListener
from chitanda.loader import load_commands
from chitanda.util import Response

logger = logging.getLogger(__name__)


class Chitanda:

    commands = {}

    def __init__(self):
        self.irc_listeners = {}
        self.discord_listener = None
        self.message_handlers = []
        self.response_handlers = []
        if config['webserver']['enable']:
            self.web_application = web.Application()

    def start(self):
        load_commands(self)
        if hasattr(self, 'web_application'):
            self.webserver = self._start_webserver()

        self.connect()

    def _start_webserver(self):
        try:
            return asyncio.ensure_future(
                asyncio.get_event_loop().create_server(
                    self.web_application.make_handler(),
                    port=int(config['webserver']['port']),
                )
            )
        except ValueError:
            logging.critical('Invalid port value for webserver.')
            sys.exit(1)

    def connect(self):
        logger.info('Initiating connection to listeners.')
        if config['irc_servers']:
            logger.info('IRC Servers found, connecting...')
            self._connect_irc()
        if config['discord_token']:
            logger.info('Discord token found, connecting...')
            self._connect_discord()

    def _connect_irc(self):
        for hostname, server in config['irc_servers'].items():
            logger.info(f'Connecting to IRC server: {hostname}.')
            self.irc_listeners[hostname] = IRCListener(
                self, server['nickname'], hostname
            )
            asyncio.ensure_future(
                self.irc_listeners[hostname].connect(
                    hostname,
                    server['port'],
                    tls=server['tls'],
                    tls_verify=server['tls_verify'],
                )
            )

    def _connect_discord(self):
        self.discord_listener = DiscordListener(self)
        self.discord_listener.run(config['discord_token'])

    async def handle_message(self, message):
        logger.debug(
            f'New message in {message.target} on {message.listener} '
            f'from {message.author}: {message.contents}'
        )
        try:
            for handler in self.message_handlers:
                response = await handler(message)
                if response:
                    await self.handle_response(response, source=message)

            await self.dispatch_command(message)
        except BotError as e:
            logger.info(f'Error triggered by {message.author}: {e}.')
            await message.listener.message(message.target, f'Error: {e}')

    async def dispatch_command(self, message):
        try:
            response = message.call_command()
            if response:
                await self.handle_response(response)
        except NoCommandFound:
            pass

    async def handle_response(self, response, source):
        logger.debug(f'Response received of type: {type(response)}.')
        if isinstance(response, AsyncGeneratorType):
            async for resp in response:
                await self._handle_response_message(resp, source)
            return

        response = await response

        if isinstance(response, GeneratorType):
            for resp in response:
                await self._handle_response_message(resp, source)
        elif response:
            await self._handle_response_message(response, source)

    async def _handle_response_message(self, response, source):
        response = Response.wrap(response, source)
        await self.call_response_handlers(response)
        await response.listener.message(
            target=response.target, message=response.contents
        )

    async def call_response_handlers(self, response):
        for handler in self.response_handlers:
            await handler(response)
