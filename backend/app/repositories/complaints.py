from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Complaint, Zone


class ComplaintRepository:
    def __init__(self, db: Session):
        self.db = db

    def zone_exists(self, zone_id: str) -> bool:
        return self.db.scalar(select(func.count()).select_from(Zone).where(Zone.id == zone_id)) == 1

    def create(self, complaint: Complaint) -> Complaint:
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        return complaint

    def get(self, complaint_id: str) -> Complaint | None:
        return self.db.get(Complaint, complaint_id)

    def list(self, skip: int, limit: int, category: str | None, status: str | None) -> tuple[list[Complaint], int]:
        query = select(Complaint).order_by(Complaint.created_at.desc(), Complaint.id.desc())
        count = select(func.count()).select_from(Complaint)
        if category:
            query = query.where(Complaint.category == category)
            count = count.where(Complaint.category == category)
        if status:
            query = query.where(Complaint.status == status)
            count = count.where(Complaint.status == status)
        return list(self.db.scalars(query.offset(skip).limit(limit))), int(self.db.scalar(count) or 0)

