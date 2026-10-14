from __future__ import annotations

from uuid import uuid4
from sqlalchemy.orm import Session
from app.db.models import Landmark
from app.repositories.landmarks import LandmarkRepository
from app.repositories.zones import ZoneRepository
from app.schemas.landmarks import LandmarkCreate, LandmarkUpdate


class LandmarkNotFoundError(Exception):
    pass


class LandmarkZoneNotFoundError(Exception):
    pass


class LandmarkService:
    def __init__(self, db: Session):
        self.repository = LandmarkRepository(db)
        self.zone_repository = ZoneRepository(db)

    def create(self, zone_id: str, data: LandmarkCreate) -> Landmark:
        if self.zone_repository.get(zone_id) is None:
            raise LandmarkZoneNotFoundError(zone_id)
        return self.repository.create(Landmark(id=str(uuid4()), zone_id=zone_id, name=data.name.strip(), landmark_type=data.landmark_type.strip(), latitude=data.latitude, longitude=data.longitude, criticality_weight=data.criticality_weight))

    def get(self, landmark_id: str) -> Landmark:
        landmark = self.repository.get(landmark_id)
        if landmark is None:
            raise LandmarkNotFoundError(landmark_id)
        return landmark

    def list_for_zone(self, zone_id: str) -> tuple[list[Landmark], int]:
        if self.zone_repository.get(zone_id) is None:
            raise LandmarkZoneNotFoundError(zone_id)
        return self.repository.list_for_zone(zone_id)

    def update(self, landmark_id: str, data: LandmarkUpdate) -> Landmark:
        landmark = self.get(landmark_id)
        for field in ("name", "landmark_type", "latitude", "longitude", "criticality_weight"):
            value = getattr(data, field)
            if value is not None:
                setattr(landmark, field, value.strip() if isinstance(value, str) else value)
        return self.repository.update(landmark)

    def delete(self, landmark_id: str) -> None:
        self.repository.delete(self.get(landmark_id))

