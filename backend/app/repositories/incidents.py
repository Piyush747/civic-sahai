from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Incident, IncidentComplaint


class IncidentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, incident_id: str) -> Incident | None:
        return self.db.get(Incident, incident_id)

    def list(self, status: str | None) -> tuple[list[Incident], int]:
        query = select(Incident).order_by(Incident.created_at.desc(), Incident.id.desc())
        count = select(func.count()).select_from(Incident)
        if status:
            query = query.where(Incident.status == status)
            count = count.where(Incident.status == status)
        return list(self.db.scalars(query)), int(self.db.scalar(count) or 0)

    def create_from_complaint(self, incident: Incident, complaint_id: str) -> Incident:
        incident.complaint_links.append(IncidentComplaint(complaint_id=complaint_id, relationship_type="PRIMARY", matched_by="SYSTEM"))
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def update(self, incident: Incident) -> Incident:
        self.db.commit()
        self.db.refresh(incident)
        return incident
