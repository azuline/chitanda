from pathlib import Path

import pytest
from click.testing import CliRunner

from chitanda.commands import migrate
from chitanda.database import create_database_if_nonexistent


@pytest.fixture
def test_db(monkeypatch):
    db_path = Path(__file__).parent / "test.sqlite3"
    monkeypatch.setattr("chitanda.database.DATABASE_PATH", db_path)
    create_database_if_nonexistent()
    CliRunner().invoke(migrate)
    yield db_path
    db_path.unlink()
