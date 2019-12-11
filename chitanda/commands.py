import asyncio
import json
import logging
import sys

import click

from chitanda import huey
from chitanda.bot import Chitanda
from chitanda.config import BLANK_CONFIG, CONFIG_PATH
from chitanda.database import calculate_migrations_needed, database

logger = logging.getLogger(__name__)


@click.group()
def cmdgroup():
    pass


@cmdgroup.command()  # pragma: no cover
def run():
    """Run the bot."""
    huey.start()
    bot = Chitanda()
    bot.start()
    asyncio.get_event_loop().run_forever()


@cmdgroup.command()
def config():
    """Edit the configuration file."""
    if not CONFIG_PATH.is_file():
        with CONFIG_PATH.open('w') as f:
            json.dump(BLANK_CONFIG, f, indent=4)
    click.edit(filename=CONFIG_PATH)


@cmdgroup.command()
def migrate():
    """Upgrade the database to the latest migration."""
    migrations_needed = calculate_migrations_needed()

    if not migrations_needed:
        click.echo('Database is up to date.')
        sys.exit(1)

    logger.info('Pending database migrations found.')
    with database() as (conn, cursor):
        for mig in migrations_needed:
            logger.info(f'Executing migration at {mig.path} .')
            with mig.path.open() as sql:
                cursor.executescript(sql.read())
                cursor.execute(
                    'INSERT INTO versions (source, version) VALUES (?, ?)',
                    (mig.source, mig.version),
                )
            conn.commit()
