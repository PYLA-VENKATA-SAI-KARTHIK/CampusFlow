"""
Regression tests for test database isolation.

Verifies:
1. Pytest test engine is strictly bound to 'campusflow_test'.
2. Safety guard function _assert_is_test_database rejects 'campusflow_dev' and production DB URLs.
3. Development database 'campusflow_dev' remains completely intact and undisturbed by test suite operations.
"""
from urllib.parse import urlparse
import os
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from tests.conftest import _assert_is_test_database


@pytest.mark.asyncio
async def test_pytest_engine_resolves_to_test_database(db_engine):
    """Verify that the pytest db_engine fixture connects strictly to campusflow_test."""
    engine_url = str(db_engine.url)
    parsed = urlparse(engine_url)
    db_name = parsed.path.lstrip("/")

    assert db_name == "campusflow_test", f"Expected 'campusflow_test', but engine was connected to '{db_name}'!"
    assert db_name != "campusflow_dev", "CRITICAL SAFETY FAILURE: Pytest engine is connected to 'campusflow_dev'!"

    # Verify that the safety guard validates this URL without error
    _assert_is_test_database(engine_url)


@pytest.mark.asyncio
async def test_settings_database_url_is_isolated():
    """Verify that application settings in the test environment point to the test database."""
    settings = get_settings()
    parsed = urlparse(settings.database_url)
    db_name = parsed.path.lstrip("/")

    assert db_name == "campusflow_test", f"Settings database_url must be 'campusflow_test', got '{db_name}'"
    assert db_name != "campusflow_dev"


def test_safety_guard_rejects_dev_database():
    """Verify that _assert_is_test_database raises RuntimeError on non-test databases."""
    with pytest.raises(RuntimeError, match="CRITICAL SAFETY VIOLATION.*development database 'campusflow_dev'"):
        _assert_is_test_database("postgresql+asyncpg://campusflow:secret@localhost:5432/campusflow_dev")

    with pytest.raises(RuntimeError, match="CRITICAL SAFETY VIOLATION.*non-test database 'production_db'"):
        _assert_is_test_database("postgresql+asyncpg://user:secret@prod-host:5432/production_db")

    # Verify valid test database names pass
    _assert_is_test_database("postgresql+asyncpg://campusflow:secret@localhost:5432/campusflow_test")
    _assert_is_test_database("postgresql+asyncpg://campusflow:secret@localhost:5432/my_app_test")


@pytest.mark.asyncio
async def test_dev_database_remains_untouched():
    """
    Read-only check against campusflow_dev to confirm that development accounts
    exist and are not destroyed by pytest running on campusflow_test.
    """
    dev_url = os.getenv(
        "DATABASE_URL_DEV",
        "postgresql+asyncpg://campusflow:campusflow_dev@localhost:5432/campusflow_dev",
    )
    dev_engine = create_async_engine(
        dev_url,
        connect_args={"server_settings": {"search_path": "campusflow, public"}},
    )
    try:
        async with dev_engine.connect() as conn:
            result = await conn.execute(
                text("SELECT email, role, is_active FROM campusflow.users WHERE email IN ('student1@campusflow.edu', 'officer@campusflow.edu', 'admin@campusflow.edu') ORDER BY email")
            )
            rows = result.fetchall()
            found_emails = {r[0]: (r[1], r[2]) for r in rows}

            assert "student1@campusflow.edu" in found_emails, "student1@campusflow.edu missing from campusflow_dev!"
            assert found_emails["student1@campusflow.edu"] == ("STUDENT", True)

            assert "officer@campusflow.edu" in found_emails, "officer@campusflow.edu missing from campusflow_dev!"
            assert found_emails["officer@campusflow.edu"] == ("OFFICER", True)

            assert "admin@campusflow.edu" in found_emails, "admin@campusflow.edu missing from campusflow_dev!"
            assert found_emails["admin@campusflow.edu"] == ("ADMIN", True)
    finally:
        await dev_engine.dispose()
