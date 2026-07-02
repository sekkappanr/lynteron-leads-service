"""Leads Service FastAPI application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from lynteronlib.auth.dependencies import configure_auth
from lynteronlib.cache import CacheService
from lynteronlib.events import EventPublisher
from lynteronlib.logging import configure_logging
from lynteronlib.health import check_db, check_redis
from lynteronlib.middleware import CorrelationIdMiddleware, RequestLoggingMiddleware, register_error_handlers
from lynteronlib.metrics import MetricsCollector, get_metrics
from lynteronlib.schemas import HealthResponse
from .api import leads_router
from .config import settings
from .dependencies import set_publisher, set_cache

logger = logging.getLogger(__name__)

metrics = MetricsCollector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)
    configure_auth(settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)
    from . import models  # noqa: F401
    try:
        alembic_cfg = AlembicConfig("/app/alembic.ini")
        alembic_command.upgrade(alembic_cfg, "head")
    except Exception as _alembic_exc:
        logger.warning("Alembic migration skipped (alembic.ini not found or error): %s", _alembic_exc)
    publisher = EventPublisher(settings.RABBITMQ_URL)
    try:
        await publisher.connect()
        set_publisher(publisher)
        logger.info("EventPublisher connected for %s", settings.SERVICE_NAME)
    except Exception as exc:
        logger.warning("RabbitMQ unavailable at startup: %s — events disabled", exc)
    cache = CacheService(settings.REDIS_URL)
    await cache.connect()
    set_cache(cache)
    yield
    await cache.close()
    await publisher.close()


app = FastAPI(
    title="Leads Service",
    description="Sales lead management for Lynteron Education Platform",
    version=settings.SERVICE_VERSION,
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(CorrelationIdMiddleware)
register_error_handlers(app)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Deep health check endpoint: probes DB and Redis connectivity."""
    db_result = await check_db(settings.DATABASE_URL)
    redis_result = await check_redis(settings.REDIS_URL)
    checks = {"db": db_result, "redis": redis_result}
    overall = "healthy" if all(v["status"] == "ok" for v in checks.values()) else "degraded"
    return HealthResponse(
        service=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        status=overall,
        checks=checks,
    )


@app.get("/metrics", tags=["Observability"])
async def metrics_endpoint():
    """Lightweight in-memory request metrics."""
    return get_metrics(metrics)


app.include_router(leads_router)
