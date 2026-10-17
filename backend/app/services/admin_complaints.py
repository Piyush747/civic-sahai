from __future__ import annotations

from datetime import datetime, timezone
from pathlib import PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Complaint, IncidentComplaint, Zone
from app.schemas.admin_complaints import (
    AdminComplaintDetails,
    AdminComplaintDetailsData,
    AdminComplaintDetailsResponse,
    ComplaintEvidence,
    ComplaintEvidenceItem,
    ComplaintCategoryDetails,
    ComplaintIncidentDetails,
    ComplaintLocation,
    ComplaintZoneDetails,
    CitizenIdentity,
)
from app.services.admin_dashboard import AdminDashboardService


class AdminComplaintDetailsService:
    def __init__(self, db: Session):
        self.db = db
        self.dashboard = AdminDashboardService(db)

    def get(self, complaint_id: str, city_id: str) -> AdminComplaintDetailsResponse | None:
        complaint = self.db.scalar(
            select(Complaint)
            .where(Complaint.id == complaint_id, Complaint.zone.has(city_id=city_id))
            .options(
                selectinload(Complaint.zone).selectinload(Zone.city),
                selectinload(Complaint.images),
                selectinload(Complaint.incident_link).selectinload(IncidentComplaint.incident),
            )
        )
        if complaint is None:
            return None

        incident = complaint.incident_link.incident if complaint.incident_link else None
        images = sorted(complaint.images, key=lambda item: self._aware(item.created_at), reverse=True)
        zone = ComplaintZoneDetails(id=complaint.zone.id, name=complaint.zone.name)
        city = ComplaintZoneDetails(id=complaint.zone.city.id, name=complaint.zone.city.name)
        category = ComplaintCategoryDetails(id=complaint.category, name=self.dashboard._category_name(complaint.category))
        details = AdminComplaintDetails(
            id=complaint.id,
            reference_number=None,
            description=complaint.description,
            status=complaint.status.lower(),
            category=category,
            severity=self.dashboard._priority_name(complaint.priority_score),
            submitted_at=complaint.created_at,
            updated_at=complaint.updated_at,
            citizen_identity=CitizenIdentity(display_label="Citizen identity masked", masked=True),
            location=ComplaintLocation(city=city, zone=zone, locality=complaint.landmark, latitude=complaint.latitude, longitude=complaint.longitude),
            evidence=ComplaintEvidence(
                total_count=len(images),
                items=[self._evidence_item(image) for image in images[:20]],
            ),
        )
        incident_details = None
        if incident:
            incident_details = ComplaintIncidentDetails(
                id=incident.id,
                reference_number=None,
                title=incident.title,
                category=ComplaintCategoryDetails(id=incident.category, name=self.dashboard._category_name(incident.category)),
                status=incident.status.lower(),
            )
        return AdminComplaintDetailsResponse(
            data=AdminComplaintDetailsData(complaint=details, incident=incident_details),
            meta={"data_as_of": datetime.now(timezone.utc)},
        )

    @staticmethod
    def _evidence_item(image) -> ComplaintEvidenceItem:
        file_name = image.image_id
        suffix = PurePosixPath(file_name).suffix.lower()
        content_type = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
            ".webp": "image/webp", ".gif": "image/gif", ".svg": "image/svg+xml",
        }.get(suffix)
        return ComplaintEvidenceItem(
            id=image.id,
            file_name=file_name,
            content_type=content_type,
            uploaded_at=image.created_at,
        )

    @staticmethod
    def _aware(value: datetime | None) -> datetime:
        if value is None:
            return datetime.min.replace(tzinfo=timezone.utc)
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
