from chitanda.database import database
from chitanda.decorators import args, channel_only, register


@register('quote find')
@channel_only
@args(r'(.+)')
async def call(message):
    """Find a quote by its content."""
    with database() as (conn, cursor):
        cursor.execute(
            """
            SELECT
                id,
                quote,
                time,
                adder
            FROM quotes
            WHERE
                channel = ?
                AND listener = ?
                AND quote LIKE ?
            ORDER BY random()
            LIMIT 3
            """,
            (message.target, str(message.listener), f'%{message.args[0]}%'),
        )
        quotes = cursor.fetchall()
        if quotes:
            for quote in quotes:
                yield f'#{quote["id"]} by {quote["adder"]}: {quote["quote"]}'
        else:
            yield 'No quotes found.'
