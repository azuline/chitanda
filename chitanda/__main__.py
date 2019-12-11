import click

from chitanda.commands import cmdgroup
from chitanda.database import (
    confirm_database_is_updated,
    create_database_if_nonexistent,
)
from chitanda.errors import BotError
from chitanda.util import create_app_dirs


def run():
    try:
        create_app_dirs()
        create_database_if_nonexistent()
        confirm_database_is_updated()
        cmdgroup()
    except BotError as e:
        click.echo(f'Error: {e}')


if __name__ == '__main__':
    run()
