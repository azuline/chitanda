from chitanda.database import database
from chitanda.decorators import args, auth_only, register


@register('lastfm set')
@args(r'([^ ]+)$')
@auth_only
async def call(message):
    """Set a Last.FM name for the nowplaying command."""
    lastfm = message.args[0]
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT OR IGNORE INTO lastfm (
                user, listener, lastfm
            ) VALUES (?, ?, ?)
            """,
            (message.username, str(message.listener), lastfm),
        )
        cursor.execute(
            'UPDATE lastfm SET lastfm = ? WHERE user = ? AND listener = ?',
            (lastfm, message.username, str(message.listener)),
        )
        conn.commit()
    return f'Set Last.FM username to {lastfm}.'
