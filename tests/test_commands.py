from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from chitanda.commands import config, migrate
from chitanda.database import Migration, database


@patch("chitanda.commands.json")
@patch("chitanda.commands.click")
def test_config_file_exists(click, json, monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        cfg_path = Path.cwd() / "config.json"
        cfg_path.touch()
        monkeypatch.setattr("chitanda.commands.CONFIG_PATH", cfg_path)
        runner.invoke(config)

        json.dump.assert_not_called()
        click.edit.assert_called_with(filename=cfg_path)


@patch("chitanda.commands.json")
@patch("chitanda.commands.click")
def test_config_file_doesnt_exist(click, json, monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        cfg_path = Path.cwd() / "config.json"
        monkeypatch.setattr("chitanda.commands.CONFIG_PATH", cfg_path)
        runner.invoke(config)

        assert cfg_path.is_file()
        json.dump.assert_called()
        click.edit.assert_called_with(filename=cfg_path)


@patch("chitanda.commands.calculate_migrations_needed")
def test_migrate(calculate, monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        fake_mig = Path.cwd() / "0001.sql"
        with fake_mig.open("w") as f:
            f.write("INSERT INTO test (id) VALUES (29)")

        monkeypatch.setattr(
            "chitanda.database.DATABASE_PATH", Path.cwd() / "db.sqlite3"
        )
        with database() as (conn, cursor):
            cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            cursor.execute(
                """
                CREATE TABLE versions (
                    source TEXT,
                    version INTEGER,
                    PRIMARY KEY (source, version)
                );
                """
            )
            conn.commit()

        calculate.return_value = [Migration(path=fake_mig, version=9, source="hi")]
        runner.invoke(migrate)

        with database() as (conn, cursor):
            cursor.execute('SELECT version FROM versions WHERE source = "hi"')
            assert 9 == cursor.fetchone()[0]
            cursor.execute("SELECT id FROM test")
            assert 29 == cursor.fetchone()[0]


def test_migrate_not_needed(test_db):
    runner = CliRunner()
    result = runner.invoke(migrate)
    assert isinstance(result.exception, SystemExit)
