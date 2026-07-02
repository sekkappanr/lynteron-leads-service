"""Leads Service API routes."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from lynteronlib.auth import require_roles

from ..schemas import (
    LeadCreateRequest,
    LeadResponse,
    LeadListResponse,
    LeadStatusUpdateRequest,
)
from ..services import LeadService
from ..dependencies import get_session

logger = logging.getLogger(__name__)

leads_router = APIRouter(prefix="/leads", tags=["Leads"])


@leads_router.post("/", status_code=status.HTTP_201_CREATED, response_model=LeadResponse)
async def create_lead(
    request: LeadCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new lead (public endpoint, no authentication required)."""
    service = LeadService(session)
    lead = await service.create_lead(request)
    if lead is None:
        # Honeypot triggered — silently succeed so bots don't retry
        return JSONResponse(status_code=201, content={"submitted": True})
    return LeadResponse.model_validate(lead)


@leads_router.get("/", response_model=LeadListResponse)
async def list_leads(
    status: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    _=Depends(require_roles("OWNER", "ADMIN")),
):
    """List leads (authenticated, owner/admin only)."""
    service = LeadService(session)
    leads, total = await service.list_leads(status=status, skip=skip, limit=limit)
    return LeadListResponse(
        items=[LeadResponse.model_validate(lead) for lead in leads],
        total=total,
    )


@leads_router.patch("/{public_id}", response_model=LeadResponse)
async def update_lead_status(
    public_id: UUID,
    request: LeadStatusUpdateRequest,
    session: AsyncSession = Depends(get_session),
    _=Depends(require_roles("OWNER", "ADMIN")),
):
    """Update lead status (authenticated, owner/admin only)."""
    service = LeadService(session)
    lead = await service.update_lead_status(public_id, request.status)
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return LeadResponse.model_validate(lead)
