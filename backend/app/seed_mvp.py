"""Create a realistic, deterministic Civic SahAI MVP dataset.

Run from the backend directory after applying the schema:
    python -m app.seed_mvp

The script is idempotent by default. It refuses to create a second copy of the
MVP dataset; use --reset only when the dedicated local database may be cleared.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from random import Random

from sqlalchemy import delete

from app.db.models import (
    City,
    Complaint,
    ComplaintImage,
    Incident,
    IncidentComplaint,
    IncidentResourceRequirement,
    Landmark,
    ResourceAllocation,
    ResourceType,
    User,
    Zone,
    ZoneResource,
)
from app.db.session import SessionLocal
from app.seed_images import image_key, upload_seed_images

SEED_CITY_ID = "city_mvp_01"
SEED_ADMIN_ID = "user_mvp_admin_01"
SEED_PREFIX = "mvp_"
SEED_VERSION = "mvp-seed-v1"

NOW = datetime.now(timezone.utc)

ZONE_DATA = [
    ("zone_mvp_01", "T. Nagar", 120000, 13.0418, 80.2341),
    ("zone_mvp_02", "Adyar", 95000, 13.0067, 80.2572),
    ("zone_mvp_03", "Anna Nagar", 110000, 13.0850, 80.2101),
    ("zone_mvp_04", "Velachery", 105000, 12.9815, 80.2180),
    ("zone_mvp_05", "Mylapore", 88000, 13.0339, 80.2676),
    ("zone_mvp_06", "Guindy", 72000, 13.0064, 80.2206),
    ("zone_mvp_07", "Perambur", 98000, 13.1167, 80.2440),
    ("zone_mvp_08", "Sholinganallur", 115000, 12.9010, 80.2279),
]

LANDMARKS = [
    ("Government General Hospital", "HOSPITAL", 2.5),
    ("Corporation Higher Secondary School", "SCHOOL", 1.7),
    ("Chennai Central Bus Terminus", "TRANSIT_HUB", 2.0),
    ("Neighborhood Market", "MARKET", 1.2),
]

CATEGORIES = ["ROAD_DAMAGE", "WASTE", "WATER_SUPPLY", "STREETLIGHT", "DRAINAGE"]
RESOURCE_DATA = [
    ("ROAD", "Road repair crew", "crews"),
    ("SANITATION", "Sanitation vehicle", "vehicles"),
    ("ELECTRICITY", "Electrical crew", "crews"),
    ("WATER", "Water response crew", "crews"),
    ("DRAINAGE", "Drainage crew", "crews"),
]


def utc_days_ago(days: int, hours: int = 0) -> datetime:
    return NOW - timedelta(days=days, hours=hours)


def polygon(latitude: float, longitude: float) -> dict:
    delta = 0.008
    return {
        "type": "Polygon",
        "coordinates": [[[longitude - delta, latitude - delta], [longitude + delta, latitude - delta], [longitude + delta, latitude + delta], [longitude - delta, latitude - delta]]],
    }


def complaint_text(category: str, zone: str, number: int) -> tuple[str, str]:
    templates = {
        "ROAD_DAMAGE": (f"Pothole affecting traffic near {zone}", "A deep pothole is slowing traffic and is risky for two-wheelers near a busy road."),
        "WASTE": (f"Garbage accumulation in {zone}", "Household waste has not been collected and is spilling onto the roadside."),
        "WATER_SUPPLY": (f"Low water pressure in {zone}", "Residents have reported low pressure and intermittent water supply since yesterday."),
        "STREETLIGHT": (f"Streetlights out in {zone}", "Several streetlights are not working, making the road difficult to use after dark."),
        "DRAINAGE": (f"Blocked drain in {zone}", "A blocked drain is causing water to collect beside homes and may worsen during rain."),
    }
    title, description = templates[category]
    return f"{title} ({number})", description


def clear_seed_data(db) -> None:
    """Clear only the known MVP dataset, in dependency order."""
    db.execute(delete(ResourceAllocation).where(ResourceAllocation.id.like(f"{SEED_PREFIX}%")))
    db.execute(delete(IncidentResourceRequirement).where(IncidentResourceRequirement.id.like(f"{SEED_PREFIX}%")))
    db.execute(delete(ZoneResource).where(ZoneResource.id.like(f"{SEED_PREFIX}%")))
    db.execute(delete(ResourceType).where(ResourceType.id.like(f"{SEED_PREFIX}%")))
    db.execute(delete(IncidentComplaint).where(IncidentComplaint.incident_id.like(f"{SEED_PREFIX}%")))
    db.execute(delete(Incident).where(Incident.id.like(f"{SEED_PREFIX}%")))
    db.execute(delete(ComplaintImage).where(ComplaintImage.id.like(f"{SEED_PREFIX}%")))
    db.execute(delete(Complaint).where(Complaint.id.like(f"{SEED_PREFIX}%")))
    db.execute(delete(Landmark).where(Landmark.id.like(f"{SEED_PREFIX}%")))
    db.execute(delete(Zone).where(Zone.id.like(f"{SEED_PREFIX}%")))
    db.execute(delete(City).where(City.id == SEED_CITY_ID))
    db.execute(delete(User).where(User.id.like(f"{SEED_PREFIX}%")))
    db.commit()


def seed() -> None:
    parser = argparse.ArgumentParser(description="Seed the Civic SahAI MVP dataset")
    parser.add_argument("--reset", action="store_true", help="remove and recreate only the MVP seed records")
    args = parser.parse_args()

    with SessionLocal() as db:
        existing = db.get(City, SEED_CITY_ID)
        if existing and not args.reset:
            raise SystemExit("MVP seed data already exists. Use --reset only for a disposable local database.")
        if args.reset:
            clear_seed_data(db)

        uploaded_images = upload_seed_images()

        rng = Random(20261011)
        admin = User(id=SEED_ADMIN_ID, name="Anita Rao", initials="AR", user_type="CITY_ADMIN", email="anita.rao@civic-sahai.example", created_at=utc_days_ago(420))
        citizens = [User(id=f"user_mvp_{index:03d}", name=f"Citizen {index:03d}", initials=f"C{index:02d}", user_type="CITIZEN", email=f"citizen{index:03d}@example.test", created_at=utc_days_ago(360 - index * 4)) for index in range(1, 35)]
        db.add_all([admin, *citizens])
        db.flush()

        city = City(id=SEED_CITY_ID, name="Chennai", admin_user_id=SEED_ADMIN_ID, created_at=utc_days_ago(420))
        db.add(city)
        db.flush()

        zones = []
        for zone_id, name, population, latitude, longitude in ZONE_DATA:
            zones.append(Zone(id=zone_id, city_id=SEED_CITY_ID, name=name, population=population, boundary=polygon(latitude, longitude), created_at=utc_days_ago(400)))
        db.add_all(zones)
        db.flush()

        landmarks = []
        for zone_index, zone in enumerate(zones):
            _, _, _, latitude, longitude = ZONE_DATA[zone_index]
            for landmark_index, (name, landmark_type, weight) in enumerate(LANDMARKS[:2 + zone_index % 3]):
                landmarks.append(Landmark(id=f"landmark_mvp_{zone_index + 1:02d}_{landmark_index + 1:02d}", zone_id=zone.id, name=f"{name} - {zone.name}", landmark_type=landmark_type, latitude=latitude + (landmark_index + 1) * 0.001, longitude=longitude + (landmark_index + 1) * 0.001, criticality_weight=weight, created_at=utc_days_ago(350)))
        db.add_all(landmarks)

        resource_types = [ResourceType(id=f"resource_type_mvp_{index:02d}", code=code, name=name, unit=unit) for index, (code, name, unit) in enumerate(RESOURCE_DATA, 1)]
        db.add_all(resource_types)
        db.flush()
        for zone_index, zone in enumerate(zones):
            for resource_index, resource_type in enumerate(resource_types):
                capacity = 3 + ((zone_index + resource_index) % 5)
                db.add(ZoneResource(id=f"zone_resource_mvp_{zone_index + 1:02d}_{resource_index + 1:02d}", zone_id=zone.id, resource_type_id=resource_type.id, initial_capacity=capacity, available_capacity=capacity, created_at=utc_days_ago(300), updated_at=utc_days_ago(1)))

        statuses = ["RESOLVED"] * 20 + ["IN_PROGRESS"] * 15 + ["OPEN"] * 15
        incidents = []
        incident_specs = []
        for incident_index in range(50):
            zone = zones[incident_index % len(zones)]
            category = CATEGORIES[incident_index % len(CATEGORIES)]
            status = statuses[incident_index]
            title, description = complaint_text(category, zone.name, incident_index + 1)
            created_at = utc_days_ago(180 - incident_index * 3, incident_index % 9)
            incidents.append(Incident(id=f"incident_mvp_{incident_index + 1:03d}", city_id=SEED_CITY_ID, zone_id=zone.id, category=category, title=title, description=description, status=status, priority_score=35 + ((incident_index * 13) % 61), priority_version=SEED_VERSION, priority_metadata={"affected_population": zone.population, "nearby_landmark_factor": round(1 + (incident_index % 4) * 0.25, 2), "complaint_count": 2 if incident_index >= 30 else 3}, created_at=created_at, updated_at=created_at + timedelta(days=2)))
            incident_specs.append((zone, category, status, created_at))
        db.add_all(incidents)
        db.flush()

        complaint_number = 0
        for incident_index, incident in enumerate(incidents):
            cluster_size = 2 if incident_index < 30 else 3
            zone, category, status, created_at = incident_specs[incident_index]
            for cluster_index in range(cluster_size):
                complaint_number += 1
                citizen = citizens[(complaint_number - 1) % len(citizens)]
                title, description = complaint_text(category, zone.name, complaint_number)
                complaint = Complaint(id=f"complaint_mvp_{complaint_number:03d}", user_id=citizen.id, title=title, description=description, category=category, latitude=13.0 + (incident_index % 8) * 0.01, longitude=80.20 + (incident_index % 8) * 0.01, address=f"{zone.name}, Chennai", zone_id=zone.id, status=status, created_at=created_at + timedelta(hours=cluster_index * 5), updated_at=created_at + timedelta(hours=cluster_index * 5))
                db.add(complaint)
                db.flush()
                db.add(IncidentComplaint(incident_id=incident.id, complaint_id=complaint.id, relationship_type="PRIMARY" if cluster_index == 0 else "DUPLICATE", match_score=None if cluster_index == 0 else round(0.82 + rng.random() * 0.15, 3), matched_by="SEED", matched_at=created_at + timedelta(hours=cluster_index * 5)))
                if complaint_number % 3 == 0:
                    db.add(ComplaintImage(id=f"image_mvp_{complaint_number:03d}", complaint_id=complaint.id, image_id=image_key(complaint_number), created_at=complaint.created_at))

            resource_type = resource_types[incident_index % len(resource_types)]
            required = 1 + incident_index % 3
            allocated = required if status == "RESOLVED" else (1 if status == "IN_PROGRESS" else 0)
            db.add(IncidentResourceRequirement(id=f"requirement_mvp_{incident_index + 1:03d}", incident_id=incident.id, resource_type_id=resource_type.id, required_quantity=required, allocated_quantity=allocated, created_at=created_at, updated_at=created_at))
            if allocated:
                db.add(ResourceAllocation(id=f"allocation_mvp_{incident_index + 1:03d}", incident_id=incident.id, source_zone_id=zone.id, resource_type_id=resource_type.id, quantity=allocated, status="COMMITTED", reason="Seeded historical allocation", created_at=created_at + timedelta(days=1), updated_at=created_at + timedelta(days=1)))

        db.commit()
        print(f"Created MVP dataset with {uploaded_images} uploaded images: 1 city, 1 city administrator, 34 citizens, 8 zones, landmarks, 120 complaints, 50 incidents, 5 resource types, zone capacities, requirements, allocations, and image references.")


if __name__ == "__main__":
    seed()
