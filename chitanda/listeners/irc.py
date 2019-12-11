import asyncio
import logging
import time
from collections import deque

import pydle

from chitanda.config import config
from chitanda.util import Message

logger = logging.getLogger(__name__)


class IRCListener(
    pydle.Client,
    pydle.features.AccountSupport,
    pydle.features.TLSSupport,
    pydle.features.RFC1459Support,
):
    def __init__(self, bot, nickname, hostname):
        self.bot = bot
        self.hostname = hostname
        self.performed = False  # Whether or not performs have been sent.
        self.message_lock = False
        self.message_queue = deque()
        self.message_times = deque(maxlen=8)
        super().__init__(nickname, username=nickname, realname=nickname)

    def __repr__(self):
        return f'IRCListener@{self.hostname}'

    async def on_connect(self):  # pragma: no cover
        await self.set_mode(self.nickname, 'BI')
        await self._perform()
        await self._loop_interrupter()

    async def _perform(self):
        logger.info(f'Running IRC perform commands on {self.hostname}.')
        for cmd in config['irc_servers'][self.hostname]['perform']:
            await self.raw(f'{cmd}\r\n')
        self.performed = True

    async def _loop_interrupter(self):  # pragma: no cover
        """
        Pydle's event loop blocks other coroutines from running.
        So there now is this.
        """
        while True:
            await asyncio.sleep(0.005)

    async def message(self, target, message, **_):
        """Implement throttle on outgoing messages."""
        self.message_queue.append((target, message, time.time()))
        if not self.message_lock:
            self.message_lock = True
            try:
                while self.message_queue:
                    try:
                        if time.time() - self.message_times[7] < 3:
                            logger.info('Throttling outgoing IRC messages.')
                            await asyncio.sleep(3 / 8)
                    except IndexError:
                        pass

                    target, message, msg_time = self.message_queue.popleft()
                    logger.info(
                        f'Sending "{message}" on IRC ({self.hostname}) '
                        f'to {target}.'
                    )
                    await super().message(target, message)
                    self.message_times.appendleft(msg_time)
            finally:
                self.message_lock = False

    async def on_raw(self, message):  # pragma: no cover
        logger.debug(f'Received raw IRC message: {message}'.rstrip())
        await super().on_raw(message)

    async def on_channel_message(self, target, by, message):
        if by != self.nickname:
            message = Message(
                bot=self.bot,
                listener=self,
                target=target,
                author=by,
                contents=message,
                private=False,
            )
            await self.bot.handle_message(message)

    async def on_private_message(self, target, by, message):
        if by != self.nickname:
            message = Message(
                bot=self.bot,
                listener=self,
                target=by,
                author=by,
                contents=message,
                private=True,
            )
            await self.bot.handle_message(message)

    async def is_admin(self, user):
        info = await self.whois(user)
        return info['identified'] and info['account'] in config['admins'].get(
            str(self), []
        )

    async def is_authed(self, user):
        info = await self.whois(user)
        return info['identified'] and info['account']
