from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.models import Complaint, Incident
from app.domain.incidents import IncidentStatus
from app.repositories.incidents import IncidentRepository
from app.schemas.incidents import IncidentStatusUpdate


class IncidentNotFoundError(Exception):
    pass


class IncidentAdministratorError(Exception):
    pass


class IncidentService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = IncidentRepository(db)

    def get(self, incident_id: str) -> Incident:
        incident = self.repository.get(incident_id)
        if incident is None:
            raise IncidentNotFoundError(incident_id)
        return incident

    def list(self, status: IncidentStatus | None) -> tuple[list[Incident], int]:
        return self.repository.list(status.value if status else None)

    def update_status(self, incident_id: str, data: IncidentStatusUpdate, admin_user_id: str | None) -> Incident:
        incident = self.get(incident_id)
        if admin_user_id is None or not self._is_city_admin(incident.city_id, admin_user_id):
            raise IncidentAdministratorError(incident_id)
        incident.status = data.status.value
        for link in incident.complaint_links:
            complaint = self.db.get(Complaint, link.complaint_id)
            if complaint is not None:
                complaint.status = data.status.value
        return self.repository.update(incident)

    def create_from_complaint(self, complaint: Complaint) -> Incident:
        """Internal clustering hook; deliberately not exposed as an HTTP endpoint."""
        incident = Incident(city_id=complaint.zone.city_id, zone_id=complaint.zone_id, category=complaint.category, title=complaint.title, description=complaint.description, status="OPEN")
        return self.repository.create_from_complaint(incident, complaint.id)

    def _is_city_admin(self, city_id: str, user_id: str) -> bool:
        from app.db.models import City, User
        user = self.db.get(User, user_id)
        return user is not None and user.user_type == "CITY_ADMIN" and self.db.scalar(select(City.id).where(City.id == city_id, City.admin_user_id == user_id)) is not None
