from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class IncidentTypeDetails(BaseModel):
    id: str
    name: str


class IncidentZoneDetails(BaseModel):
    id: str
    name: str


class IncidentLocation(BaseModel):
    city: IncidentZoneDetails
    zone: IncidentZoneDetails
    locality: str | None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class IncidentDetails(BaseModel):
    id: str
    reference_number: str | None
    incident_type: IncidentTypeDetails
    title: str
    description: str | None
    status: str
    priority: str | None
    location: IncidentLocation | None
    created_at: datetime
    updated_at: datetime | None
    resolved_at: datetime | None


class AssignmentTeam(BaseModel):
    id: str
    name: str


class CurrentAssignment(BaseModel):
    status: Literal["assigned", "unassigned"]
    team: AssignmentTeam | None
    assigned_at: datetime | None


class IncidentSla(BaseModel):
    waiting_too_long: bool | None
    status: str | None
    response_due_at: datetime | None
    breached_at: datetime | None


class LinkedComplaintItem(BaseModel):
    complaint_id: str
    reference_number: str | None
    submitted_at: datetime | None
    severity: str | None
    status: str
    summary: str | None
    evidence_count: int = Field(ge=0)
    has_evidence: bool


class LinkedComplaints(BaseModel):
    total_count: int = Field(ge=0)
    items: list[LinkedComplaintItem]
    has_more: bool


class IncidentImpact(BaseModel):
    linked_complaint_count: int = Field(ge=0)
    waiting_duration_seconds: int | None = Field(default=None, ge=0)
    potential_impact: object | None = None


class IncidentDetailsData(BaseModel):
    incident: IncidentDetails
    assignment: CurrentAssignment
    sla: IncidentSla
    linked_complaints: LinkedComplaints
    impact: IncidentImpact


class IncidentDetailsResponse(BaseModel):
    data: IncidentDetailsData
    meta: dict[str, datetime]
