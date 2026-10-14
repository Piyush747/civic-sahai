from __future__ import annotations

from sqlalchemy.orm import Session
from app.core.exceptions import ComplaintNotFoundError, ZoneNotFoundError
from app.db.models import Complaint, ComplaintImage
from app.repositories.complaints import ComplaintRepository
from app.repositories.users import UserRepository
from app.schemas.complaints import ComplaintCreate
from app.integrations.complaint_events import ComplaintEventPublisher


class ComplaintService:
    def __init__(self, db: Session):
        self.repository = ComplaintRepository(db)

    def create(self, data: ComplaintCreate, user_id: str | None, event_publisher: ComplaintEventPublisher | None = None) -> Complaint:
        if not user_id or UserRepository(self.repository.db).get(user_id) is None:
            raise ValueError("A valid X-User-Id is required.")
        if not self.repository.zone_exists(data.zone_id):
            raise ZoneNotFoundError(data.zone_id)
        complaint = Complaint(
            user_id=user_id, title=data.title.strip(), description=data.description.strip(),
            category=data.category.value, latitude=data.location.latitude,
            longitude=data.location.longitude, address=data.location.address.strip(),
            zone_id=data.zone_id, status="OPEN",
        )
        complaint.images = [ComplaintImage(image_id=image_id.strip()) for image_id in data.image_ids if image_id.strip()]
        complaint = self.repository.create(complaint)
        if event_publisher is not None:
            event_publisher.publish_received(complaint)
        return complaint

    def get(self, complaint_id: str) -> Complaint:
        complaint = self.repository.get(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(complaint_id)
        return complaint

    def list(self, skip: int, limit: int, category: str | None, status: str | None) -> tuple[list[Complaint], int]:
        return self.repository.list(skip, limit, category, status)

