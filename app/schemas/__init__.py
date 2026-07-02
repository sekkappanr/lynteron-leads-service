"""Pydantic schemas for Leads Service API."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LeadCreateRequest(BaseModel):
    """Request to create a new lead."""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    organization: Optional[str] = Field(None, max_length=255)
    role_title: Optional[str] = Field(None, max_length=100)
    school_size: Optional[str] = Field(None, max_length=50)
    message: Optional[str] = None
    source: Optional[str] = Field(None, max_length=100)
    utm_source: Optional[str] = Field(None, max_length=100)
    utm_medium: Optional[str] = Field(None, max_length=100)
    utm_campaign: Optional[str] = Field(None, max_length=100)
    honeypot: Optional[str] = Field(None)  # Hidden spam trap field


class LeadResponse(BaseModel):
    """Response containing lead details."""

    id: int
    public_id: UUID
    name: str
    email: str
    phone: Optional[str]
    organization: Optional[str]
    role_title: Optional[str]
    school_size: Optional[str]
    message: Optional[str]
    source: Optional[str]
    status: str
    utm_source: Optional[str]
    utm_medium: Optional[str]
    utm_campaign: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    """Response containing a list of leads."""

    items: list[LeadResponse]
    total: int


class LeadStatusUpdateRequest(BaseModel):
    """Request to update lead status."""

    status: str = Field(..., pattern="^(new|contacted|qualified|won|lost)$")
