from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Landmark


class LandmarkRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, landmark: Landmark) -> Landmark:
        self.db.add(landmark)
        self.db.commit()
        self.db.refresh(landmark)
        return landmark

    def get(self, landmark_id: str) -> Landmark | None:
        return self.db.get(Landmark, landmark_id)

    def list_for_zone(self, zone_id: str) -> tuple[list[Landmark], int]:
        query = select(Landmark).where(Landmark.zone_id == zone_id).order_by(Landmark.name.asc())
        total = self.db.scalar(select(func.count()).select_from(Landmark).where(Landmark.zone_id == zone_id)) or 0
        return list(self.db.scalars(query)), int(total)

    def update(self, landmark: Landmark) -> Landmark:
        self.db.commit()
        self.db.refresh(landmark)
        return landmark

    def delete(self, landmark: Landmark) -> None:
        self.db.delete(landmark)
        self.db.commit()

