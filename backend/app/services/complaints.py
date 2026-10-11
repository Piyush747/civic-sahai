from sqlalchemy.orm import Session
from app.core.exceptions import ComplaintNotFoundError, ZoneNotFoundError
from app.db.models import Complaint
from app.repositories.complaints import ComplaintRepository
from app.schemas.complaints import ComplaintCreate


class ComplaintService:
    def __init__(self, db: Session):
        self.repository = ComplaintRepository(db)

    def create(self, data: ComplaintCreate, user_id: str | None) -> Complaint:
        if not self.repository.zone_exists(data.zone_id):
            raise ZoneNotFoundError(data.zone_id)
        return self.repository.create(Complaint(
            user_id=user_id, title=data.title.strip(), description=data.description.strip(),
            category=data.category.value, latitude=data.location.latitude,
            longitude=data.location.longitude, address=data.location.address.strip(),
            zone_id=data.zone_id, status="OPEN",
        ))

    def get(self, complaint_id: str) -> Complaint:
        complaint = self.repository.get(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(complaint_id)
        return complaint

    def list(self, skip: int, limit: int, category: str | None, status: str | None) -> tuple[list[Complaint], int]:
        return self.repository.list(skip, limit, category, status)

