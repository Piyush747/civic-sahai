from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AllocationRecommendation, Incident, IncidentAssignment, Team
from app.schemas.admin_assignments import (
    AssignmentDetails, AssignmentIncidentState, AssignedTeam, TeamAssignmentCreate,
    TeamAssignmentResponse, TeamAssignmentResponseData,
)


class AdminTeamAssignmentService:
    def __init__(self, db: Session):
        self.db = db

    def assign(self, incident_id: str, payload: TeamAssignmentCreate, city_id: str, admin_user_id: str) -> TeamAssignmentResponse:
        incident = self.db.scalar(select(Incident).where(Incident.id == incident_id, Incident.city_id == city_id).with_for_update())
        if incident is None:
            raise HTTPException(404, {"code": "INCIDENT_NOT_FOUND", "message": "The requested incident was not found."})
        if incident.status not in {"OPEN", "IN_PROGRESS"}:
            raise HTTPException(409, {"code": "INCIDENT_NOT_ASSIGNABLE", "message": "The incident cannot receive a team assignment in its current state."})

        team = self.db.scalar(select(Team).where(Team.id == payload.team_id, Team.city_id == city_id).with_for_update())
        if team is None:
            raise HTTPException(404, {"code": "TEAM_NOT_FOUND", "message": "The requested team was not found."})
        if team.availability_status != "AVAILABLE" or team.capacity < 1:
            raise HTTPException(409, {"code": "TEAM_NOT_AVAILABLE", "message": "The selected team is not currently available."})

        active_incident = self.db.scalar(select(IncidentAssignment).where(IncidentAssignment.incident_id == incident.id, IncidentAssignment.unassigned_at.is_(None)))
        if active_incident is not None:
            raise HTTPException(409, {"code": "ASSIGNMENT_CONFLICT", "message": "The incident already has an active team assignment."})
        active_team = self.db.scalar(select(IncidentAssignment).where(IncidentAssignment.team_id == team.id, IncidentAssignment.unassigned_at.is_(None)))
        if active_team is not None:
            raise HTTPException(409, {"code": "TEAM_NOT_AVAILABLE", "message": "The selected team already has an active assignment."})

        if payload.recommendation_id:
            recommendation = self.db.scalar(select(AllocationRecommendation).where(AllocationRecommendation.id == payload.recommendation_id, AllocationRecommendation.incident_id == incident.id))
            if recommendation is None:
                raise HTTPException(404, {"code": "RECOMMENDATION_NOT_FOUND", "message": "The requested recommendation was not found."})
            if recommendation.status != "AWAITING_DECISION":
                raise HTTPException(409, {"code": "RECOMMENDATION_NOT_ELIGIBLE", "message": "The recommendation is no longer eligible for assignment."})

        now = datetime.now(timezone.utc)
        assignment = IncidentAssignment(id=str(uuid4()), incident_id=incident.id, team_id=team.id, assigned_at=now, assigned_by=admin_user_id, recommendation_id=payload.recommendation_id)
        self.db.add(assignment)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise HTTPException(409, {"code": "ASSIGNMENT_CONFLICT", "message": "The assignment could not be created because the state changed."})
        return TeamAssignmentResponse(data=TeamAssignmentResponseData(assignment=AssignmentDetails(id=assignment.id, incident_id=incident.id, team=AssignedTeam(id=team.id, name=team.name), status="assigned", assigned_at=assignment.assigned_at, assigned_by=assignment.assigned_by, recommendation_id=assignment.recommendation_id), incident=AssignmentIncidentState(id=incident.id, assignment_status="assigned")), meta={"data_as_of": now})
