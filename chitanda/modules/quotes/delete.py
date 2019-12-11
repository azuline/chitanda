from chitanda.database import database
from chitanda.decorators import admin_only, args, channel_only, register
from chitanda.errors import BotError

from . import fetch


@register('quote del')
@args(r'(.+)')
@channel_only
@admin_only
async def call(message):
    """Delete a quote from the database."""
    quote_ids = _parse_quote_ids(message.args[0])
    with database() as (conn, cursor):
        yield 'Deleted the following quotes:'
        for quote in fetch.fetch_quotes(
            cursor, message.target, message.listener, quote_ids.copy()
        ):
            yield quote

        cursor.execute(
            """
            DELETE FROM quotes
            WHERE
                channel = ?
                AND listener = ?
                AND id IN ("""
            + (','.join(['?'] * len(quote_ids)))
            + """)
            """,
            (message.target, str(message.listener), *quote_ids),
        )

        conn.commit()


def _parse_quote_ids(message):
    try:
        quote_ids = [int(qid) for qid in message.split(' ')]
    except ValueError:
        raise BotError('Quote IDs must be integers.')
    return quote_ids
