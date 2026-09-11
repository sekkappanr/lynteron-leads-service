"""Regression guard for the DEF-9 retest failure (RAID-40).

`PATCH /leads/{public_id}` 400'd with `MissingGreenlet` because
`LeadService.update_lead_status` flushed the UPDATE but never refreshed the row,
so the router's `LeadResponse.model_validate(lead)` lazy-loaded the
server-`onupdate` `updated_at` outside the async greenlet. The fix adds
`await session.refresh(lead)`. This test pins that the PATCH path awaits
`refresh` and returns 200 with the new status.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models import Lead
from app.dependencies import get_session


def _scalar_one_or_none(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


@pytest.fixture
async def client(mock_session):
    async def _fake_session():
        yield mock_session

    app.dependency_overrides[get_session] = _fake_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_session, None)


@pytest.mark.asyncio
async def test_patch_lead_status_refreshes_and_returns_200(client, mock_session):
    public_id = uuid.uuid4()
    lead = Lead(
        id=1, public_id=public_id, name="Jane", email="jane@example.com",
        status="new",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    mock_session.execute = AsyncMock(return_value=_scalar_one_or_none(lead))
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    resp = await client.patch(f"/leads/{public_id}", json={"status": "contacted"})

    assert resp.status_code == 200
    assert resp.json()["status"] == "contacted"
    # The fix: the row must be refreshed after flush so serialization does not
    # trigger a lazy load outside the greenlet.
    mock_session.refresh.assert_awaited_once_with(lead)


@pytest.mark.asyncio
async def test_patch_lead_status_404_when_missing(client, mock_session):
    mock_session.execute = AsyncMock(return_value=_scalar_one_or_none(None))
    mock_session.refresh = AsyncMock()

    resp = await client.patch(f"/leads/{uuid.uuid4()}", json={"status": "contacted"})

    assert resp.status_code == 404
    mock_session.refresh.assert_not_awaited()
