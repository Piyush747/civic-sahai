from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import City, Zone


class ZoneRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, zone: Zone) -> Zone:
        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)
        return zone

    def city_exists(self, city_id: str) -> bool:
        return self.db.get(City, city_id) is not None

    def get(self, zone_id: str) -> Zone | None:
        return self.db.get(Zone, zone_id)

    def list(self) -> tuple[list[Zone], int]:
        zones = list(self.db.scalars(select(Zone).order_by(Zone.name.asc(), Zone.id.asc())))
        return zones, int(self.db.scalar(select(func.count()).select_from(Zone)) or 0)

    def update(self, zone: Zone) -> Zone:
        self.db.commit()
        self.db.refresh(zone)
        return zone

    def delete(self, zone: Zone) -> None:
        self.db.delete(zone)
        self.db.commit()

