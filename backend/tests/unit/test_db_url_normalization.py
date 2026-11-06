import pytest
from app.core.config import Settings


@pytest.fixture(autouse=True)
def setup_test_db():
    yield


def test_database_url_normalization():
    cases = [
        ("postgresql://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"),
        ("postgres://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"),
        ('"postgresql://u:p@h:5432/db"', "postgresql+asyncpg://u:p@h:5432/db"),
        ("'postgresql://u:p@h:5432/db'", "postgresql+asyncpg://u:p@h:5432/db"),
        ("  postgresql://u:p@h:5432/db \n", "postgresql+asyncpg://u:p@h:5432/db"),
        ("DATABASE_URL=postgresql://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"),
        ("DATABASE_URL='postgresql://u:p@h:5432/db'", "postgresql+asyncpg://u:p@h:5432/db"),
        ('DATABASE_URL="postgresql://u:p@h:5432/db"', "postgresql+asyncpg://u:p@h:5432/db"),
        ("psql 'postgresql://u:p@h:5432/db'", "postgresql+asyncpg://u:p@h:5432/db"),
        ("postgres://u:p@h:5432/db?sslmode=require", "postgresql+asyncpg://u:p@h:5432/db?ssl=require"),
        ("postgresql://u:p@h:5432/db?sslmode=disable", "postgresql+asyncpg://u:p@h:5432/db"),
    ]

    for inp, expected in cases:
        res = Settings.assemble_db_connection(inp)
        assert res == expected, f"Failed for {inp}: got {res}, expected {expected}"
