"""Service-level dependencies for Leads Service."""

import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from lynteronlib.cache import CacheService
from lynteronlib.database.session import get_session_factory
from lynteronlib.events import EventPublisher
from .config import settings

logger = logging.getLogger(__name__)

_session_factory = None
_publisher: Optional[EventPublisher] = None
_cache: Optional[CacheService] = None


def _get_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = get_session_factory(settings.DATABASE_URL, settings.DB_SCHEMA)
    return _session_factory


def set_publisher(pub: EventPublisher) -> None:
    """Set the module-level EventPublisher instance (called during startup)."""
    global _publisher
    _publisher = pub


async def get_event_publisher() -> Optional[EventPublisher]:
    """Return the EventPublisher, or None if RabbitMQ is unavailable."""
    return _publisher


def set_cache(cache: CacheService) -> None:
    """Set the module-level CacheService instance (called during startup)."""
    global _cache
    _cache = cache


def get_cache() -> Optional[CacheService]:
    """Return the CacheService, or None if Redis is unavailable."""
    return _cache


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
