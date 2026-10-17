from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Complaint, Incident, IncidentAssignment, IncidentComplaint, Zone
from app.schemas.admin_incidents import (AssignmentTeam, CurrentAssignment, IncidentDetails,
    IncidentDetailsData, IncidentDetailsResponse, IncidentImpact, IncidentLocation, IncidentSla, IncidentTypeDetails,
    IncidentZoneDetails, LinkedComplaintItem, LinkedComplaints)
from app.services.admin_dashboard import AdminDashboardService


class AdminIncidentDetailsService:
    def __init__(self, db: Session):
        self.db = db
        self.dashboard = AdminDashboardService(db)

    def get(self, incident: Incident) -> IncidentDetailsResponse:
        incident = self.db.scalar(select(Incident).where(Incident.id == incident.id).options(selectinload(Incident.complaint_links).selectinload(IncidentComplaint.complaint).selectinload(Complaint.images), selectinload(Incident.assignments).selectinload(IncidentAssignment.team)))
        zone = self.db.scalar(select(Zone).where(Zone.id == incident.zone_id).options(selectinload(Zone.city)))
        complaints = [link.complaint for link in incident.complaint_links]
        complaints.sort(key=lambda item: item.created_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        active = [assignment for assignment in incident.assignments if assignment.unassigned_at is None]
        current = max(active, key=lambda item: self._aware(item.assigned_at)) if active else None
        details = IncidentDetails(id=incident.id, reference_number=None, incident_type=IncidentTypeDetails(id=incident.category, name=self.dashboard._category_name(incident.category)), title=incident.title, description=incident.description, status=incident.status.lower(), priority=self.dashboard._priority_name(incident.priority_score), location=IncidentLocation(city=IncidentZoneDetails(id=zone.city.id, name=zone.city.name), zone=IncidentZoneDetails(id=zone.id, name=zone.name), locality=incident.locality, latitude=incident.latitude, longitude=incident.longitude) if zone else None, created_at=incident.created_at, updated_at=incident.updated_at, resolved_at=incident.resolved_at)
        linked_items = [LinkedComplaintItem(complaint_id=item.id, reference_number=None, submitted_at=item.created_at, severity=self.dashboard._priority_name(item.priority_score), status=item.status.lower(), summary=item.description[:240] if item.description else None, evidence_count=len(item.images), has_evidence=bool(item.images)) for item in complaints[:20]]
        linked = LinkedComplaints(total_count=len(complaints), items=linked_items, has_more=len(complaints) > len(linked_items))
        waiting = None if incident.sla_status is None else incident.sla_status == "breached"
        return IncidentDetailsResponse(data=IncidentDetailsData(incident=details, assignment=CurrentAssignment(status="assigned" if current else "unassigned", team=AssignmentTeam(id=current.team.id, name=current.team.name) if current else None, assigned_at=current.assigned_at if current else None), sla=IncidentSla(waiting_too_long=waiting, status=incident.sla_status, response_due_at=incident.response_due_at, breached_at=incident.sla_breached_at), linked_complaints=linked, impact=IncidentImpact(linked_complaint_count=len(complaints), waiting_duration_seconds=None, potential_impact=None)), meta={"data_as_of": datetime.now(timezone.utc)})

    @staticmethod
    def _aware(value: datetime | None) -> datetime:
        if value is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
