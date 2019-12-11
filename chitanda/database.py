import logging
import sqlite3
import sys
from collections import namedtuple
from contextlib import contextmanager
from pathlib import Path

import click

from chitanda import DATA_DIR
from chitanda.errors import BotError

DATABASE_PATH = DATA_DIR / 'db.sqlite3'


logger = logging.getLogger(__name__)

Migration = namedtuple('Migration', 'path, version, source')


@contextmanager
def database():
    with sqlite3.connect(str(DATABASE_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        yield conn, cursor
        cursor.close()


def create_database_if_nonexistent():
    with database() as (conn, cursor):
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='versions'
            """
        )
        if not cursor.fetchone():
            logger.info('Creating versions table.')
            cursor.execute(
                """
                CREATE TABLE versions (
                    source TEXT,
                    version INTEGER,
                    PRIMARY KEY (source, version)
                )
                """
            )
            conn.commit()


def confirm_database_is_updated():
    if calculate_migrations_needed():
        if not len(sys.argv) == 2 or sys.argv[1] != 'migrate':
            raise BotError(
                'The database needs to be migrated. Run `chitanda migrate`.'
            )


def calculate_migrations_needed():
    migrations = _find_migrations()
    versions = _get_versions()

    needed = []
    for mig in migrations:
        if mig.version > versions.get(mig.source, 0):
            needed.append(mig)
    return sorted(needed, key=lambda m: m.version)


def _find_migrations():
    migrations = []
    commands_path = Path(__file__).parent / 'modules'
    for sql_path in commands_path.glob('**/*.sql'):
        try:
            migrations.append(
                Migration(
                    path=sql_path,
                    version=int(sql_path.stem),
                    source=sql_path.parts[-3],
                )
            )
        except ValueError:
            click.echo(f'Invalid migration name: {sql_path}.')
            raise click.Abort
    return migrations


def _get_versions():
    with database() as (conn, cursor):
        cursor.execute(
            'SELECT source, MAX(version) FROM versions GROUP BY source'
        )
        return {r['source']: r[1] for r in cursor.fetchall()}
