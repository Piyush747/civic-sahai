from __future__ import annotations

from app.db.models import City, Landmark, User, Zone
from app.db.session import SessionLocal


def zone_polygon(latitude: float, longitude: float, delta: float = 0.045) -> dict:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [longitude - delta, latitude - delta],
                [longitude + delta, latitude - delta],
                [longitude + delta, latitude + delta],
                [longitude - delta, latitude + delta],
                [longitude - delta, latitude - delta],
            ]
        ],
    }


def seed() -> None:
    with SessionLocal() as db:
        if db.get(User, "user_city_admin_01") is None:
            db.add(User(id="user_city_admin_01", name="Chennai City Administrator", initials="CCA", email="admin@chennai.example", user_type="CITY_ADMIN"))
            db.commit()
        if db.get(User, "1001") is None:
            db.add(User(id="1001", name="Piyush Jain", initials="PJ", email="piyush.jain@example.com", user_type="CITIZEN"))
            db.commit()
        if db.get(City, "city_01") is None:
            db.add(City(id="city_01", name="Chennai", admin_user_id="user_city_admin_01"))
            db.commit()
        if db.get(Zone, "zone_01") is None:
            db.add_all(
                [
                    Zone(
                        id="zone_01",
                        city_id="city_01",
                        name="Central Chennai",
                        population=250000,
                        boundary=zone_polygon(13.0827, 80.2707),
                    ),
                    Zone(
                        id="zone_02",
                        city_id="city_01",
                        name="North Chennai",
                        population=180000,
                        boundary=zone_polygon(13.15, 80.24, delta=0.04),
                    ),
                ]
            )
            db.commit()
        for zone_id, latitude, longitude, delta in (
            ("zone_01", 13.0827, 80.2707, 0.045),
            ("zone_02", 13.15, 80.24, 0.04),
        ):
            zone = db.get(Zone, zone_id)
            if zone is not None and zone.boundary is None:
                zone.boundary = zone_polygon(latitude, longitude, delta=delta)
        db.commit()
        landmarks = [
            ("landmark_central_01", "zone_01", "Government General Hospital", "HOSPITAL", 13.0815, 80.2782, 2.5),
            ("landmark_central_02", "zone_01", "Chennai Central", "TRANSIT_HUB", 13.0827, 80.2755, 2.0),
            ("landmark_central_03", "zone_01", "Ripon Building", "CIVIC", 13.0820, 80.2705, 1.8),
            ("landmark_central_04", "zone_01", "Spencer Plaza", "MARKET", 13.0614, 80.2615, 1.2),
            ("landmark_central_05", "zone_01", "Marina Beach", "BEACH", 13.0500, 80.2824, 1.4),
            ("landmark_central_06", "zone_01", "Egmore Railway Station", "TRANSIT_HUB", 13.0780, 80.2615, 1.6),
        ]
        for landmark_id, zone_id, name, landmark_type, latitude, longitude, weight in landmarks:
            if db.get(Landmark, landmark_id) is None and db.get(Zone, zone_id) is not None:
                db.add(
                    Landmark(
                        id=landmark_id,
                        zone_id=zone_id,
                        name=name,
                        landmark_type=landmark_type,
                        latitude=latitude,
                        longitude=longitude,
                        criticality_weight=weight,
                    )
                )
        db.commit()


if __name__ == "__main__":
    seed()
