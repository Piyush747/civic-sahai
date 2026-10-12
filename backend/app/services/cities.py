from __future__ import annotations

from uuid import uuid4
from sqlalchemy.orm import Session
from app.db.models import City
from app.repositories.cities import CityRepository
from app.schemas.cities import CityCreate, CityUpdate


class CityNotFoundError(Exception):
    pass


class CityAdministratorNotFoundError(Exception):
    pass


class CityService:
    def __init__(self, db: Session):
        self.repository = CityRepository(db)

    def create(self, data: CityCreate) -> City:
        if not self.repository.city_admin_exists(data.admin_user_id):
            raise CityAdministratorNotFoundError(data.admin_user_id)
        return self.repository.create(City(id=str(uuid4()), name=data.name.strip(), admin_user_id=data.admin_user_id))

    def get(self, city_id: str) -> City:
        city = self.repository.get(city_id)
        if city is None:
            raise CityNotFoundError(city_id)
        return city

    def list(self) -> tuple[list[City], int]:
        return self.repository.list()

    def update(self, city_id: str, data: CityUpdate) -> City:
        city = self.get(city_id)
        if data.admin_user_id is not None:
            if not self.repository.city_admin_exists(data.admin_user_id):
                raise CityAdministratorNotFoundError(data.admin_user_id)
            city.admin_user_id = data.admin_user_id
        if data.name is not None:
            city.name = data.name.strip()
        return self.repository.update(city)

    def delete(self, city_id: str) -> None:
        self.repository.delete(self.get(city_id))

