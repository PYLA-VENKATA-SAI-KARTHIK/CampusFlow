import os
from collections.abc import AsyncGenerator
from pathlib import Path

from dotenv import load_dotenv

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Test environment & Database Isolation
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

os.environ["APP_ENV"] = "testing"

# Resolve TEST_DATABASE_URL with fallback derivation
raw_dev_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://campusflow:campusflow_dev@localhost:5432/campusflow_dev",
)
explicit_test_url = os.getenv("TEST_DATABASE_URL")

if explicit_test_url:
    test_db_url = explicit_test_url
elif "/campusflow_dev" in raw_dev_url:
    test_db_url = raw_dev_url.replace("/campusflow_dev", "/campusflow_test")
else:
    test_db_url = raw_dev_url.rstrip("/") + "_test"

# Override DATABASE_URL in testing environment so all dependencies resolve to test DB
os.environ["DATABASE_URL"] = test_db_url

os.environ["JWT_PRIVATE_KEY_BASE64"] = "LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFb2dJQkFBS0NBUUVBdXluNjlDQzZJbkxBVTVZTUs0aUQxdjFDY2FZRENzZGpqeWxRRVFrMkxWc0p4S2lCCnM5S3F3NkJZTXpXODFCV21pYTdWc0RTYVV2WEZrU0RVZlRhY0tBUkg1WjlFV0JNekhBMGVTNmRudHlvZGVZeTQKRnZFRUZOK3BteEJ6RTE2SVZma1FqU1dXRU53aVpFeFVRQ0d6dmJSZkh3TmxQdTdoL1poYXgxVFdCWEw4VlBNcwpnZWd0Qi94T1JoUUpOYWhVN3BKZ2hBMkh5dm96QzBibGtUVzgxM21tcmFOK1o0NTZ5cVBLN3hsTlhFWGNQeHRQCjBycVYzWWJmMFd6MUROendxSFRsL1lJR0RwMkRCNUN5Znh1RHRpYkZ2YU9LbWVhcUZ4cE45WnI5Wnc0Wm5wdmUKNlgvTEROK3JlVkZRbHYzK2NVSXJNNnZRejdlSnBPbXA1NFc3V3dJREFRQUJBb0lCQUFVdEhZd241WTN6VjM5WQpUSURkdHl1NGVHQjFRMnRHWlduOXJnR3luQVY0R1phUFJIc0pMZ0RZQytocXFZekNCb2VUUnNTblI4ZFlsYnkwClNEd29TUHhRVmY2elAyd2lKODAwVGF5dzlnemFSTk5xUVdNZENreGJmVERWTFNHUmdUckRkeUk0TW1USCtjbUYKVk9VcktYSHJMYUJKYzBEZzBXNDJpdmd0VC9mNWtIMDV0NTFBNkVxb3BmZVdkS2RteWloZWtLN2tHdExTNXVVUgpPK2o5bTFldVdzVHRLTFh2cklDaUNGQm9oYU1Pd0RucnNLTUZZbkpZdTZ3NzNPVWRiZkhSMlBsUE0vNnlyMElsCi9KZ0c5S3g0MjB1bld5Vk1HdXlwUWtSRHJDSXowclA0Z2c2Ym9NaUxaeHZndUtLVTNzaTRpNFdqdWJMektmRS8KTU9DcHQ3a0NnWUVBN0dmWTZwbjI5S0RiQXBuWElURGpkVzNLazlQSjRhSTVFaUtJUys5WnhJMnRreUFmcFFFNQpBbWxjRjBXQXEzWFdLbUFzMC9NclNmbE9KMzB5LzIxYWxsVzFackVpSzdvdDFXd3FvMFZMS2xLUmhVNWtXM3VNCmRBS3AyN2Nrb0ovTXhZRG1pdWxLZGV4MnNjbXRacTFPWWQrZGpDdVdLSjdjR3RhR3JxZFl3N01DZ1lFQXlxMU4KalByZGxOWURWYXJvTXE5VGNxZHkrZ2gvMjdNam5SQ09jS1A1dVlsVDlTVnVKamk2cmFmQkxVZVpETHp0WEFyZQpsZ3N6U0VIVzFrYmZ3amJmeG95dnRSYlJwb0lhTzdndFl6RWUyZHUwVzQwckovYlhDWTBhcHY2UEtpazJVem9qCmZoTUp0RXlGamhkVjRFUUNVOUVWcG8vYWJkVmFKRDVOTm5PUzlia0NnWUJISE0zeGRETUhUMFBTT25pdU1VaWEKMEZYNXRlR3FqK1BmQXFoQlAxU2ZmWWJURlB5djQvaEVNM0ZTUnNQM3o5Q0dtcnVoWGlxTmJBTUllZTdYU3d2Two0U1ZhS0xxQXNOYU10cWIweWlsY0o4NUNiVnhlOElGRmZHK2YraTE0YTlsckorVXhzQStIL1lPTzQzM1h2eFl1Cjl0Y3JqUWowV3lVV3BhV0o4Q2tSWlFLQmdFQkNvR01CcXoya2VWd3hHdnZ2QU90S1VqY2FlTWVFemRiZngvbkkKMDhYUzE4N1RObEJpRGpZL0NRMjlOTGFJTkUzSm1IZEVSOWN5SU5iQmsvSjFDWkJmVE5xQ3lLZ2RlZ25UUkhpOQp1MFZoMXBac2RQRnYzeEJGTDkwZ3V1Mm9NWFJENjdydWVGWTFLT2M3V053SlZCK1ZIR002R3d4VjZBV3p4ekZyCmhYM3BBb0dBRWJhSHdVYktPTUZKYlorN1VNU2VHNUI5UkJVQy8wRnlYeC9Wc2hrdWJpTTZ1YjdQZHFCUVk1b2kKcjUyWVRDTmszTkIrRTJvdTF5QjdUVTJuSEdrT25sMjlOSXRyWEJrdVh2WHdKYVBOZU1zQzBsKzJBT242RzZtOApFUVh5RzlKaThYSmhnaGRlY0dYNm13aE9rRk11R05KcEQ5WmorZTJLRmdDZXoybk5Uekk9Ci0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCg=="
os.environ["JWT_PUBLIC_KEY_BASE64"] = "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUF1eW42OUNDNkluTEFVNVlNSzRpRAoxdjFDY2FZRENzZGpqeWxRRVFrMkxWc0p4S2lCczlLcXc2QllNelc4MUJXbWlhN1ZzRFNhVXZYRmtTRFVmVGFjCktBUkg1WjlFV0JNekhBMGVTNmRudHlvZGVZeTRGdkVFRk4rcG14QnpFMTZJVmZrUWpTV1dFTndpWkV4VVFDR3oKdmJSZkh3TmxQdTdoL1poYXgxVFdCWEw4VlBNc2dlZ3RCL3hPUmhRSk5haFU3cEpnaEEySHl2b3pDMGJsa1RXOAoxM21tcmFOK1o0NTZ5cVBLN3hsTlhFWGNQeHRQMHJxVjNZYmYwV3oxRE56d3FIVGwvWUlHRHAyREI1Q3lmeHVECnRpYkZ2YU9LbWVhcUZ4cE45WnI5Wnc0Wm5wdmU2WC9MRE4rcmVWRlFsdjMrY1VJck02dlF6N2VKcE9tcDU0VzcKV3dJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg=="


def _assert_is_test_database(url_str: str) -> None:
    """
    Defensive safety assertion:
    Verifies that test setup/teardown executes strictly against campusflow_test.
    Fails loudly and immediately if pointing to campusflow_dev or production.
    """
    parsed = urlparse(url_str)
    db_name = parsed.path.lstrip("/")
    if db_name == "campusflow_dev":
        raise RuntimeError(
            "CRITICAL SAFETY VIOLATION: Pytest attempted to run against development database 'campusflow_dev'! "
            "Test execution has been aborted immediately to protect development data."
        )
    if not db_name.endswith("_test") and db_name != "campusflow_test":
        raise RuntimeError(
            f"CRITICAL SAFETY VIOLATION: Pytest attempted to run against non-test database '{db_name}'. "
            f"Database name must be 'campusflow_test' or end with '_test'!"
        )


# Validate configured test database URL at import time
_assert_is_test_database(test_db_url)

# ---------------------------------------------------------------------------
# Import application AFTER environment variables are configured
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from app.db.base import Base
from app.main import app
from app.core.config import get_settings
from app.core.security import init_jwt_manager

from app.core.limiter import limiter

# Clear settings cache and initialize JWTManager for test suite
get_settings.cache_clear()
init_jwt_manager(get_settings())

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator:
    _assert_is_test_database(os.environ["DATABASE_URL"])
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        echo=False,
        poolclass=NullPool,
        connect_args={"server_settings": {"search_path": "campusflow, public"}},
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(db_engine) -> AsyncGenerator[None, None]:
    """
    Reset the database before every test strictly in campusflow_test.
    """
    _assert_is_test_database(str(db_engine.url))

    limiter.reset()
    # Create a fresh connection for schema setup.
    async with db_engine.begin() as connection:
        await connection.execute(text("CREATE SCHEMA IF NOT EXISTS campusflow AUTHORIZATION campusflow;"))
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    yield

    limiter.reset()
    # Remove all test data/schema after the test inside the test database only.
    async with db_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide one database session per test.
    """
    TestingSessionLocal = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

from app.db.session import get_db_session
from app.core.dependencies import get_db

@pytest_asyncio.fixture
async def async_client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP client for the FastAPI app.
    Overrides the database dependency to use a fresh test session per request.
    """
    TestingSessionLocal = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()