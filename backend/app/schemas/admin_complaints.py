from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ComplaintZoneDetails(BaseModel):
    id: str
    name: str


class ComplaintCategoryDetails(BaseModel):
    id: str
    name: str


class ComplaintIncidentDetails(BaseModel):
    id: str
    reference_number: str | None
    title: str
    category: ComplaintCategoryDetails
    status: str


class ComplaintLocation(BaseModel):
    city: ComplaintZoneDetails
    zone: ComplaintZoneDetails
    locality: str | None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class CitizenIdentity(BaseModel):
    display_label: str
    masked: bool


class ComplaintEvidenceItem(BaseModel):
    id: str
    file_name: str
    content_type: str | None
    uploaded_at: datetime | None


class ComplaintEvidence(BaseModel):
    total_count: int = Field(ge=0)
    items: list[ComplaintEvidenceItem]


class AdminComplaintDetails(BaseModel):
    id: str
    reference_number: str | None
    description: str
    status: str
    category: ComplaintCategoryDetails
    severity: str | None
    submitted_at: datetime | None
    updated_at: datetime | None
    citizen_identity: CitizenIdentity
    location: ComplaintLocation | None
    evidence: ComplaintEvidence


class AdminComplaintDetailsData(BaseModel):
    complaint: AdminComplaintDetails
    incident: ComplaintIncidentDetails | None


class AdminComplaintDetailsResponse(BaseModel):
    data: AdminComplaintDetailsData
    meta: dict[str, datetime]
