"""Shared test fixtures for Leads Service."""
import sys
from types import ModuleType
from typing import Annotated, Any
from unittest.mock import MagicMock, AsyncMock
from fastapi import Depends

# Build a fake user class
class _FakeUser:
    sub = "user-uuid-123"
    roles = ["OWNER"]
    school_id = 1
    school_ids = [1]
    school_codes = ["SCHOOL001"]
    user_id = 1

    def get(self, k, d=None):
        return getattr(self, k, d)


_FAKE_USER = _FakeUser()


def _fake_current_user_dep():
    return _FAKE_USER


_CurrentUser = Annotated[Any, Depends(_fake_current_user_dep)]

for mod_path in [
    "lynteronlib", "lynteronlib.auth", "lynteronlib.auth.dependencies",
    "lynteronlib.auth.jwt_handler", "lynteronlib.auth.access_control",
    "lynteronlib.auth.password", "lynteronlib.cache",
    "lynteronlib.database", "lynteronlib.database.session",
    "lynteronlib.events", "lynteronlib.logging", "lynteronlib.health",
    "lynteronlib.middleware", "lynteronlib.metrics", "lynteronlib.schemas",
    "lynteronlib.email", "lynteronlib.validators",
]:
    m = ModuleType(mod_path)
    sys.modules[mod_path] = m

sys.modules["lynteronlib.auth.dependencies"].configure_auth = MagicMock()
sys.modules["lynteronlib.auth"].require_roles = MagicMock(
    side_effect=lambda *roles: _fake_current_user_dep
)
sys.modules["lynteronlib.auth"].CurrentUser = _CurrentUser
sys.modules["lynteronlib.auth"].configure_auth = MagicMock()
sys.modules["lynteronlib.auth"].require_school_access = MagicMock()
sys.modules["lynteronlib.cache"].CacheService = MagicMock
sys.modules["lynteronlib.database.session"].get_session_factory = MagicMock(return_value=MagicMock())
sys.modules["lynteronlib.database"].get_session_factory = MagicMock(return_value=MagicMock())

from sqlalchemy.orm import DeclarativeBase
class MockBase(DeclarativeBase): pass
sys.modules["lynteronlib.database"].Base = MockBase

sys.modules["lynteronlib.events"].EventPublisher = MagicMock
sys.modules["lynteronlib.events"].EventConsumer = MagicMock

class MockDomainEvent:
    def __init__(self, **kw):
        for k, v in kw.items(): setattr(self, k, v)
    def model_dump(self):
        return {k: v for k, v in self.__dict__.items()}
sys.modules["lynteronlib.events"].DomainEvent = MockDomainEvent

sys.modules["lynteronlib.logging"].configure_logging = MagicMock()
sys.modules["lynteronlib.health"].check_db = AsyncMock(return_value={"status": "ok"})
sys.modules["lynteronlib.health"].check_redis = AsyncMock(return_value={"status": "ok"})
sys.modules["lynteronlib.email"].send_email = AsyncMock(return_value=True)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class _PassthroughMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        return await call_next(request)

sys.modules["lynteronlib.middleware"].CorrelationIdMiddleware = _PassthroughMiddleware
sys.modules["lynteronlib.middleware"].RequestLoggingMiddleware = _PassthroughMiddleware
sys.modules["lynteronlib.middleware"].register_error_handlers = MagicMock()
sys.modules["lynteronlib.metrics"].MetricsCollector = MagicMock
sys.modules["lynteronlib.metrics"].get_metrics = MagicMock(return_value={})

from pydantic import BaseModel
class MockHealthResponse(BaseModel):
    service: str = ""
    version: str = ""
    status: str = "healthy"
    checks: dict = {}
sys.modules["lynteronlib.schemas"].HealthResponse = MockHealthResponse

import pytest

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def mock_current_user():
    """Return shared fake user; restore original attribute values after each test."""
    orig_roles = list(_FAKE_USER.roles)
    orig_school_ids = list(_FAKE_USER.school_ids)
    orig_school_codes = list(_FAKE_USER.school_codes)
    yield _FAKE_USER
    _FAKE_USER.roles = orig_roles
    _FAKE_USER.school_ids = orig_school_ids
    _FAKE_USER.school_codes = orig_school_codes

# LYN-11: app.main imports run_migrations_or_fail from lynteronlib.database
# (the real startup migration runner; unit tests never run migrations).
sys.modules["lynteronlib.database"].run_migrations_or_fail = MagicMock()
