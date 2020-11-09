from unittest.mock import call, patch

import pytest

from chitanda.database import database
from chitanda.modules.tell import _delete_tell, _fetch_tells
from chitanda.modules.tell import call as call_cmd
from chitanda.modules.tell import tell_handler
from chitanda.util import Message


@pytest.mark.asyncio
async def test_tell_handler():
    with patch("chitanda.modules.tell._fetch_tells") as fetch:
        with patch("chitanda.modules.tell._delete_tell") as delete:
            fetch.return_value = [
                {
                    "time": "2019-01-01T12:34:56",
                    "sender": "azul",
                    "message": "hi",
                    "id": 1,
                },
                {
                    "time": "2019-01-02T12:34:56",
                    "sender": "azul",
                    "message": "hi again",
                    "id": 2,
                },
            ]

            responses = [
                r
                async for r in tell_handler(
                    Message(None, None, None, "newuser", None, False)
                )
            ]

            assert responses == [
                "newuser: On Jan 01, 12:34:56, azul said: hi",
                "newuser: On Jan 02, 12:34:56, azul said: hi again",
            ]
            assert delete.call_args_list == [call(1), call(2)]


@pytest.mark.asyncio
async def test_tell_handler_private():
    with patch("chitanda.modules.tell._fetch_tells") as fetch:
        with patch("chitanda.modules.tell._delete_tell"):
            fetch.return_value = [
                {
                    "time": "2019-01-01T12:34:56",
                    "sender": "azul",
                    "message": "hi",
                    "id": 1,
                }
            ]

            assert not [
                r
                async for r in tell_handler(
                    Message(None, None, None, "newuser", None, private=True)
                )
            ]


@pytest.mark.asyncio
async def test_add_tell(test_db):
    await call_cmd(
        Message(
            bot=None,
            listener="DiscordListener",
            target="#chan",
            author="azul",
            contents="newuser hi again!",
            private=False,
        )
    )
    with database() as (conn, cursor):
        cursor.execute(
            """
            SELECT 1 FROM tells
            WHERE channel = "#chan"
                AND listener = "DiscordListener"
                AND message = "hi again!"
                AND recipient = "newuser"
                AND sender = "azul"
            """
        )
        assert cursor.fetchone()


def test_fetch_tells(test_db):
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO tells
                (channel, listener, message, recipient, sender)
            VALUES
                ("#chan", "DiscordListener", "hi", "azul", "newuser"),
                ("#notchan", "DiscordListener", "hi", "azul", "newuser"),
                ("#chan", "IRCListener@irc.freenode.fake", "hi", "azul",
                    "newuser"),
                ("#chan", "DiscordListener", "hi", "notazul", "newuser")
            """
        )
        conn.commit()
    assert len(_fetch_tells("#chan", "DiscordListener", "azul")) == 1


def test_delete_tell(test_db):
    with database() as (conn, cursor):
        cursor.execute(
            """
            INSERT INTO tells (
                id, channel, listener, message, recipient, sender
            ) VALUES
                (1, "#chan", "DiscordListener", "hi", "azul", "newuser"),
                (2, "#notchan", "DiscordListener", "hi", "azul", "newuser")
            """
        )
        conn.commit()
    _delete_tell(1)
    with database() as (conn, cursor):
        cursor.execute("SELECT COUNT(1) FROM tells")
        assert 1 == cursor.fetchone()[0]
