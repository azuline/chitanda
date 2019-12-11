from pathlib import Path

import click
import pytest
from click.testing import CliRunner
from mock import Mock, patch

from chitanda.database import (
    Migration,
    _find_migrations,
    _get_versions,
    calculate_migrations_needed,
    confirm_database_is_updated,
    create_database_if_nonexistent,
    database,
)
from chitanda.errors import BotError


def test_database_contextmanager(monkeypatch):
    with CliRunner().isolated_filesystem():
        monkeypatch.setattr(
            'chitanda.database.DATABASE_PATH', Path.cwd() / 'db.sqlite3'
        )
        with database() as (conn, cursor):
            cursor.execute('CREATE TABLE ham(id INTEGER PRIMARY KEY)')
            cursor.execute('INSERT INTO ham (id) VALUES (1)')
            conn.commit()
            cursor.execute('SELECT id FROM ham')
            assert cursor.fetchone()[0] == 1


def test_create_nonexistent_database(monkeypatch):
    with CliRunner().isolated_filesystem():
        monkeypatch.setattr(
            'chitanda.database.DATABASE_PATH', Path.cwd() / 'db.sqlite3'
        )
        create_database_if_nonexistent()
        with database() as (conn, cursor):
            cursor.execute('SELECT version FROM versions')


@patch('chitanda.database.calculate_migrations_needed')
def test_confirm_db_updated_true(calculate):
    calculate.return_value = False
    confirm_database_is_updated()


@patch('chitanda.database.calculate_migrations_needed')
def test_confirm_db_updated_false(calculate):
    calculate.return_value = True
    with pytest.raises(BotError):
        confirm_database_is_updated()


@patch('chitanda.database.calculate_migrations_needed')
@patch('chitanda.database.sys')
def test_confirm_db_updated_updating(sys, calculate):
    sys.argv = ['chitanda', 'migrate']
    calculate.return_value = True
    confirm_database_is_updated()


@patch('chitanda.database._get_versions')
@patch('chitanda.database._find_migrations')
def testcalculate_migrations_needed(find_migrations, get_version):
    mig1 = Migration(path='', version=1, source='a')
    mig2 = Migration(path='', version=2, source='a')
    mig3 = Migration(path='', version=2, source='b')
    mig4 = Migration(path='', version=4, source='b')
    find_migrations.return_value = [mig3, mig4, mig2, mig1]
    get_version.return_value = {'a': 1, 'b': 2}

    assert list(calculate_migrations_needed()) == [mig2, mig4]


@patch('chitanda.database.Path')
def test_find_migrations(path):
    with CliRunner().isolated_filesystem():
        path.return_value.parent.__truediv__.return_value.glob = Mock(
            return_value=[
                Path.cwd() / '0001.sql',
                Path.cwd() / '0002.sql',
                Path.cwd() / '0003.sql',
            ]
        )
        assert len(_find_migrations()) == 3


@patch('chitanda.database.Path')
def test_find_invalid_migration_name(path):
    with CliRunner().isolated_filesystem():
        path.return_value.parent.__truediv__.return_value.glob = Mock(
            return_value=[
                Path.cwd() / '0001.sql',
                Path.cwd() / '0002.sql',
                Path.cwd() / 'abcd.sql',
            ]
        )
        with pytest.raises(click.Abort):
            _find_migrations()


def test_get_version(test_db):
    with database() as (conn, cursor):
        cursor.execute('DELETE FROM versions')
        cursor.execute(
            'INSERT INTO versions (version, source) VALUES (83, "a")'
        )
        cursor.execute(
            'INSERT INTO versions (version, source) VALUES (28, "b")'
        )
        cursor.execute(
            'INSERT INTO versions (version, source) VALUES (18, "b")'
        )
        conn.commit()

    assert {'a': 83, 'b': 28} == _get_versions()


def test_get_version_empty_table(test_db):
    with database() as (conn, cursor):
        cursor.execute('DELETE FROM versions')
        conn.commit()

    assert {} == _get_versions()
