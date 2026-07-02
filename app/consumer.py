"""Leads event consumer worker.

Subscribes to leads.lead_created and sends sales notifications.
Run as: python -m app.consumer
"""

import asyncio
import logging

from lynteronlib.database.session import get_session_factory
from lynteronlib.events import EventConsumer, DomainEvent
from lynteronlib.email import send_email

from .config import settings

logger = logging.getLogger(__name__)

# Module-level session factory — created once, reused for every message
_session_factory = None


def _get_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = get_session_factory(settings.DATABASE_URL, settings.DB_SCHEMA)
    return _session_factory


async def handle_lead_created(event: DomainEvent) -> None:
    """Send a notification email when a new lead is created.

    Triggered when a lead is submitted via the public form.
    """
    payload = dict(event.payload)

    logger.info(
        "Received lead_created — lead_id=%s name=%s email=%s event_id=%s",
        payload.get("lead_id"),
        payload.get("name"),
        payload.get("email"),
        event.event_id,
    )

    # Compose email
    name = payload.get("name", "Unknown")
    email = payload.get("email", "unknown@example.com")
    organization = payload.get("organization", "Unknown organization")
    lead_id = payload.get("lead_id", "unknown")

    subject = f"New Lead: {name} from {organization}"
    body_text = (
        f"New lead submitted!\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Organization: {organization}\n"
        f"Lead ID: {lead_id}\n\n"
        f"Log in to the platform to follow up."
    )
    body_html = f"""
    <h2>New Lead Submitted</h2>
    <p><strong>Name:</strong> {name}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Organization:</strong> {organization}</p>
    <p><strong>Lead ID:</strong> {lead_id}</p>
    <p><a href="https://lynteron.app" style="background:#4f46e5;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;">View in Platform</a></p>
    """

    success = await send_email(
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        to_emails=[settings.SALES_EMAIL],
        smtp_host=settings.SMTP_HOST,
        smtp_port=settings.SMTP_PORT,
        smtp_user=settings.SMTP_USER,
        smtp_password=settings.SMTP_PASSWORD,
        from_email=settings.EMAIL_FROM,
    )

    if success:
        logger.info(
            "Sent lead notification — lead_id=%s to=%s event_id=%s",
            payload.get("lead_id"),
            settings.SALES_EMAIL,
            event.event_id,
        )
    else:
        logger.warning(
            "Failed to send lead notification — lead_id=%s event_id=%s",
            payload.get("lead_id"),
            event.event_id,
        )


async def main() -> None:
    consumer = EventConsumer(settings.RABBITMQ_URL)
    consumer.on("lead_created", handle_lead_created)
    logger.info(
        "Leads consumer starting — queue=leads.events binding_key=leads.lead_created rabbitmq=%s",
        settings.RABBITMQ_URL,
    )
    await consumer.start(
        queue_name="leads.events",
        binding_keys=["leads.lead_created"],
    )
    logger.info("Leads consumer is now consuming events")
    # Keep running indefinitely
    try:
        await asyncio.Future()
    finally:
        await consumer.close()
        logger.info("Leads consumer shut down")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
