from __future__ import annotations

from app.db.models import City, User, Zone
from app.db.session import SessionLocal


def seed() -> None:
    with SessionLocal() as db:
        if db.get(User, "user_city_admin_01") is None:
            db.add(User(id="user_city_admin_01", name="Chennai City Administrator", initials="CCA", email="admin@chennai.example", user_type="CITY_ADMIN"))
            db.commit()
        if db.get(User, "101") is None:
            db.add(User(id="101", name="Piyush Jain", initials="PJ", email="piyush.jain@example.com", user_type="CITIZEN"))
            db.commit()
        if db.get(City, "city_01") is None:
            db.add(City(id="city_01", name="Chennai", admin_user_id="user_city_admin_01"))
            db.commit()
        if db.get(Zone, "zone_01") is None:
            db.add_all([Zone(id="zone_01", city_id="city_01", name="Central Chennai", population=250000), Zone(id="zone_02", city_id="city_01", name="North Chennai", population=180000)])
            db.commit()


if __name__ == "__main__":
    seed()

