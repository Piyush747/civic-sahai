from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import City, User


class CityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, city: City) -> City:
        self.db.add(city)
        self.db.commit()
        self.db.refresh(city)
        return city

    def city_admin_exists(self, user_id: str) -> bool:
        user = self.db.get(User, user_id)
        return user is not None and user.user_type == "CITY_ADMIN"

    def get(self, city_id: str) -> City | None:
        return self.db.get(City, city_id)

    def list(self) -> tuple[list[City], int]:
        cities = list(self.db.scalars(select(City).order_by(City.name.asc(), City.id.asc())))
        return cities, int(self.db.scalar(select(func.count()).select_from(City)) or 0)

    def update(self, city: City) -> City:
        self.db.commit()
        self.db.refresh(city)
        return city

    def delete(self, city: City) -> None:
        self.db.delete(city)
        self.db.commit()

