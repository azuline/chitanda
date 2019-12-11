from chitanda.database import database
from chitanda.decorators import args, auth_only, channel_only, register


@register('quote add')
@channel_only
@args(r'(.+)')
@auth_only
async def call(message):
    """Add a quote to the database."""
    with database() as (conn, cursor):
        new_quote_id = _get_quote_id(cursor, message.listener, message.target)
        cursor.execute(
            """
            INSERT INTO quotes (
                id, channel, listener, quote, adder
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                new_quote_id,
                message.target,
                str(message.listener),
                message.args[0],
                message.username,
            ),
        )
        conn.commit()
    return f'Added quote with ID {new_quote_id}.'


def _get_quote_id(cursor, listener, target):
    cursor.execute(
        """
        SELECT max(id)
        FROM quotes
        WHERE listener = ? AND channel = ?
        """,
        (str(listener), target),
    )
    row = cursor.fetchone()
    try:
        return row[0] + 1
    except TypeError:
        return 1
