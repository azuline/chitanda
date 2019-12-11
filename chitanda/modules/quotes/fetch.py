from chitanda.database import database
from chitanda.decorators import channel_only, register
from chitanda.errors import BotError


@register('quote')
@channel_only
async def call(message):
    """Fetch quotes by ID or one random quote from the channel."""
    with database() as (conn, cursor):
        if not message.contents:
            yield _fetch_random_quote(cursor, message.target, message.listener)
        else:
            quote_ids = _parse_quote_ids(message.contents)
            for quote in fetch_quotes(
                cursor, message.target, message.listener, quote_ids
            ):
                yield quote


def fetch_quotes(cursor, target, listener, quote_ids):
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
            AND id IN ("""
        + (','.join(['?'] * len(quote_ids)))
        + """)
        ORDER BY id ASC
        """,
        (target, str(listener), *quote_ids),
    )
    quotes = cursor.fetchall()
    for quote in quotes:
        yield f'#{quote["id"]} by {quote["adder"]}: {quote["quote"]}'
        quote_ids.remove(quote["id"])
    if quote_ids:
        yield (
            f'Quote(s) {", ".join(str(qid) for qid in quote_ids)} '
            'do not exist.'
        )


def _parse_quote_ids(message):
    try:
        quote_ids = [int(qid) for qid in message.split(' ')]
    except ValueError:
        raise BotError('Quote IDs must be integers.')

    if len(quote_ids) > 3:
        raise BotError('A maximum of three quotes may be queried at once.')
    return quote_ids


def _fetch_random_quote(cursor, target, listener):
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
        ORDER BY random()
        LIMIT 1
        """,
        (target, str(listener)),
    )
    quote = cursor.fetchone()
    if quote:
        return f'#{quote["id"]} by {quote["adder"]}: {quote["quote"]}'
    return 'This channel has no quotes saved.'
