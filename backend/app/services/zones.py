from __future__ import annotations

from uuid import uuid4
from sqlalchemy.orm import Session
from app.db.models import Zone
from app.repositories.zones import ZoneRepository
from app.schemas.zones import ZoneCreate, ZoneUpdate


class ZoneNotFoundError(Exception):
    pass


class CityNotFoundError(Exception):
    pass


class ZoneService:
    def __init__(self, db: Session):
        self.repository = ZoneRepository(db)

    def create(self, data: ZoneCreate) -> Zone:
        if not self.repository.city_exists(data.city_id):
            raise CityNotFoundError(data.city_id)
        return self.repository.create(Zone(id=str(uuid4()), city_id=data.city_id, name=data.name.strip(), population=data.population, boundary=data.boundary))

    def get(self, zone_id: str) -> Zone:
        zone = self.repository.get(zone_id)
        if zone is None:
            raise ZoneNotFoundError(zone_id)
        return zone

    def list(self) -> tuple[list[Zone], int]:
        return self.repository.list()

    def update(self, zone_id: str, data: ZoneUpdate) -> Zone:
        zone = self.get(zone_id)
        if data.city_id is not None:
            if not self.repository.city_exists(data.city_id):
                raise CityNotFoundError(data.city_id)
            zone.city_id = data.city_id
        if data.name is not None:
            zone.name = data.name.strip()
        if data.population is not None:
            zone.population = data.population
        if data.boundary is not None:
            zone.boundary = data.boundary
        return self.repository.update(zone)

    def delete(self, zone_id: str) -> None:
        self.repository.delete(self.get(zone_id))

