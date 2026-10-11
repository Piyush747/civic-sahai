from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models import Zone
from app.db.session import get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
with TestingSession() as db:
    db.add(Zone(id="zone_01", name="Test", population=1))
    db.commit()


def override_db():
    with TestingSession() as db:
        yield db


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def test_create_and_get_complaint():
    response = client.post("/api/v1/complaints", json={"title": "Broken streetlight", "description": "The streetlight has been out for three nights.", "category": "STREETLIGHT", "location": {"latitude": 13, "longitude": 80, "address": "Test Road"}, "zone_id": "zone_01"})
    assert response.status_code == 201
    complaint_id = response.json()["id"]
    assert client.get(f"/api/v1/complaints/{complaint_id}").status_code == 200


def test_missing_zone_is_stable_error():
    response = client.post("/api/v1/complaints", json={"title": "Broken road", "description": "A very large pothole is dangerous.", "category": "ROAD_DAMAGE", "location": {"latitude": 13, "longitude": 80, "address": "Test Road"}, "zone_id": "missing"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ZONE_NOT_FOUND"

