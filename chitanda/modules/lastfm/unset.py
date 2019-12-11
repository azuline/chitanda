from chitanda.database import database
from chitanda.decorators import args, auth_only, register


@register('lastfm unset')
@args(r'$')
@auth_only
async def call(message):
    """Unset your Last.FM name."""
    with database() as (conn, cursor):
        cursor.execute(
            """
            SELECT 1
            FROM lastfm
            WHERE user = ?  AND listener = ?
            """,
            (message.username, str(message.listener)),
        )
        if cursor.fetchone():
            cursor.execute(
                """
                DELETE FROM lastfm
                WHERE user = ?  AND listener = ?
                """,
                (message.username, str(message.listener)),
            )
            conn.commit()
            return 'Unset Last.FM username.'
        return 'No Last.FM username to unset.'
