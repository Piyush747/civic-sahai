from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import require_city_admin
from app.db.models import Incident
from app.db.session import get_db
from app.schemas.admin_incidents import IncidentDetailsResponse
from app.services.admin_incidents import AdminIncidentDetailsService

router = APIRouter(prefix="/admin/incidents", tags=["admin-incidents"])


@router.get("/{incident_id}", response_model=IncidentDetailsResponse)
def incident_details(incident_id: str, admin_context=Depends(require_city_admin), db: Session = Depends(get_db)):
    _, city = admin_context
    incident = db.scalar(select(Incident).where(Incident.id == incident_id, Incident.city_id == city.id))
    if incident is None:
        raise HTTPException(404, {"code": "INCIDENT_NOT_FOUND", "message": "The requested incident could not be found."})
    return AdminIncidentDetailsService(db).get(incident)
