"""Leads Service – Core business logic."""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lynteronlib.events import DomainEvent, EventPublisher

from ..config import settings
from ..models import Lead
from ..schemas import LeadCreateRequest

logger = logging.getLogger(__name__)


class LeadService:
    """Service for managing sales leads."""

    def __init__(self, session: AsyncSession, event_publisher: Optional[EventPublisher] = None):
        self._session = session
        self._publisher = event_publisher

    async def create_lead(self, data: LeadCreateRequest) -> Optional[Lead]:
        """Create a new lead; return None if honeypot is triggered."""
        # Honeypot: if honeypot field is filled, drop silently (likely bot)
        if data.honeypot:
            logger.warning("Honeypot triggered for lead submission")
            return None

        lead = Lead(
            name=data.name,
            email=data.email,
            phone=data.phone,
            organization=data.organization,
            role_title=data.role_title,
            school_size=data.school_size,
            message=data.message,
            source=data.source,
            utm_source=data.utm_source,
            utm_medium=data.utm_medium,
            utm_campaign=data.utm_campaign,
            status="new",
        )
        self._session.add(lead)
        await self._session.flush()

        # Publish lead_created event
        await self._publish_event(
            "lead_created",
            payload={
                "lead_id": str(lead.public_id),
                "name": lead.name,
                "email": lead.email,
                "organization": lead.organization or "Unknown",
            },
        )

        return lead

    async def list_leads(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Lead], int]:
        """List leads with optional status filter."""
        query = select(Lead)
        if status:
            query = query.where(Lead.status == status)

        # Get total count
        count_query = select(func.count()).select_from(Lead)
        if status:
            count_query = count_query.where(Lead.status == status)
        count_result = await self._session.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated results
        query = query.order_by(Lead.created_at.desc()).limit(limit).offset(skip)
        result = await self._session.execute(query)
        leads = list(result.scalars().all())

        return leads, total

    async def update_lead_status(self, public_id: UUID, status: str) -> Optional[Lead]:
        """Update a lead's status by public_id."""
        query = select(Lead).where(Lead.public_id == public_id)
        result = await self._session.execute(query)
        lead = result.scalar_one_or_none()

        if not lead:
            return None

        lead.status = status
        await self._session.flush()
        return lead

    async def get_lead_by_public_id(self, public_id: UUID) -> Optional[Lead]:
        """Fetch a lead by public_id."""
        query = select(Lead).where(Lead.public_id == public_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    # --- Event Publishing ---

    async def _publish_event(self, event_type: str, payload: Optional[dict] = None) -> None:
        """Publish a domain event if publisher is available."""
        if self._publisher:
            event = DomainEvent(
                event_type=event_type,
                source_service="leads",
                payload=payload or {},
            )
            try:
                await self._publisher.publish(event)
            except Exception:
                logger.exception("Failed to publish event %s", event_type)
