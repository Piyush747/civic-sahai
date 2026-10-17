from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TeamAssignmentCreate(BaseModel):
    team_id: str = Field(min_length=1)
    recommendation_id: str | None = Field(default=None, min_length=1)


class AssignedTeam(BaseModel):
    id: str
    name: str


class AssignmentDetails(BaseModel):
    id: str
    incident_id: str
    team: AssignedTeam
    status: str
    assigned_at: datetime | None
    assigned_by: str | None
    recommendation_id: str | None


class AssignmentIncidentState(BaseModel):
    id: str
    assignment_status: str


class TeamAssignmentResponseData(BaseModel):
    assignment: AssignmentDetails
    incident: AssignmentIncidentState


class TeamAssignmentResponse(BaseModel):
    data: TeamAssignmentResponseData
    meta: dict[str, datetime]
