import logging
from datetime import datetime

from chitanda.database import database
from chitanda.decorators import args, channel_only, register

logger = logging.getLogger(__name__)

TIME_FORMAT = '%b %d, %H:%M:%S'


def setup(bot):  # pragma: no cover
    bot.message_handlers.append(tell_handler)


async def tell_handler(message):
    if message.private:
        return

    for row in _fetch_tells(message.target, message.listener, message.author):
        time = datetime.fromisoformat(row['time']).strftime(TIME_FORMAT)
        logger.info(
            f'Sent tell to {message.author} in {message.target} '
            f'on {message.listener}.'
        )
        yield (
            f'{message.author}: On {time}, {row["sender"]} said: '
            f'{row["message"]}'
        )
        _delete_tell(row['id'])


@register('tell')
@channel_only
@args(r'([^ ]+) (.+)')
async def call(message):
    """Save a message for a user the next time they are seen."""
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO tells (
                channel, listener, message, recipient, sender
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                message.target,
                str(message.listener),
                message.args[1],
                message.args[0],
                message.author,
            ),
        )
        conn.commit()
    logger.info(
        f'Added a tell for {message.args[0]} in {message.target} on '
        f'{message.listener}'
    )
    return f'{message.args[0]} will be told when next seen.'


def _fetch_tells(target, listener, author):
    with database() as (conn, cursor):
        cursor.execute(
            """
            SELECT
                id,
                message,
                time,
                sender
            FROM tells
            WHERE
                channel = ?
                AND listener = ?
                AND recipient = ?
            ORDER BY id ASC
            """,
            (target, str(listener), author),
        )
        return cursor.fetchall()


def _delete_tell(tell_id):
    logger.debug(f'Deleting tell {tell_id}.')
    with database() as (conn, cursor):
        cursor.execute('DELETE FROM tells WHERE id = ?', (tell_id,))
        conn.commit()
