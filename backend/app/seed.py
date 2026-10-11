from app.db.models import Zone
from app.db.session import SessionLocal


def seed() -> None:
    with SessionLocal() as db:
        if db.get(Zone, "zone_01") is None:
            db.add_all([Zone(id="zone_01", name="Central Chennai", population=250000), Zone(id="zone_02", name="North Chennai", population=180000)])
            db.commit()


if __name__ == "__main__":
    seed()

