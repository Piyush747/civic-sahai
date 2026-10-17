from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import require_city_admin
from app.db.session import get_db
from app.schemas.admin_assignments import TeamAssignmentCreate, TeamAssignmentResponse
from app.services.admin_assignments import AdminTeamAssignmentService


router = APIRouter(prefix="/admin/incidents", tags=["admin-assignments"])


@router.post("/{incident_id}/assignments", response_model=TeamAssignmentResponse, status_code=201)
def assign_team(incident_id: str, payload: TeamAssignmentCreate, admin_context=Depends(require_city_admin), db: Session = Depends(get_db)):
    admin, city = admin_context
    return AdminTeamAssignmentService(db).assign(incident_id, payload, city.id, admin.id)
