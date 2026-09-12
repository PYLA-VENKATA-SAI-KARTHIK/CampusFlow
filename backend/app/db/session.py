"""
CampusFlow — Database Session Management

Provides async engine and session factory.
Reads DATABASE_URL from settings.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if "postgresql" in settings.database_url:
            connect_args = {"server_settings": {"search_path": "campusflow, public"}}
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_pre_ping=True,  # Enable connection health checks
            pool_size=10,
            max_overflow=20,
            connect_args=connect_args,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints.
    Yields a session and automatically rolls back if an exception occurs.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            logger.exception("Database session error, rolling back")
            await session.rollback()
            raise
        # We don't automatically commit here.
        # Repositories/Services should explicitly commit when appropriate.


async def close_db_engine() -> None:
    """Close the database engine (for graceful shutdown)."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")
