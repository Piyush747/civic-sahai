from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models import City, Zone
from app.db.session import get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
with TestingSession() as db:
    from app.db.models import User
    db.add(User(id="admin_01", name="Test Admin", initials="TA", email="admin@example.com", user_type="CITY_ADMIN"))
    db.add(City(id="city_01", name="Test City", admin_user_id="admin_01"))
    db.commit()
    db.add(Zone(id="zone_01", city_id="city_01", name="Test", population=1))
    db.commit()


def override_db():
    with TestingSession() as db:
        yield db


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


def test_create_and_get_complaint():
    user = client.post("/api/v1/users", json={"name": "Test Citizen", "email": "citizen@example.com"})
    assert user.status_code == 201
    assert user.json()["initials"] == "TC"
    assert user.json()["user_type"] == "CITIZEN"
    assert user.json()["created_at"]
    response = client.post("/api/v1/complaints", headers={"X-User-Id": user.json()["id"]}, json={"title": "Broken streetlight", "description": "The streetlight has been out for three nights.", "category": "STREETLIGHT", "location": {"latitude": 13, "longitude": 80, "address": "Test Road"}, "zone_id": "zone_01"})
    assert response.status_code == 201
    complaint_id = response.json()["id"]
    assert client.get(f"/api/v1/complaints/{complaint_id}").status_code == 200


def test_missing_zone_is_stable_error():
    user = client.post("/api/v1/users", json={"name": "Another Citizen", "email": "another@example.com"})
    response = client.post("/api/v1/complaints", headers={"X-User-Id": user.json()["id"]}, json={"title": "Broken road", "description": "A very large pothole is dangerous.", "category": "ROAD_DAMAGE", "location": {"latitude": 13, "longitude": 80, "address": "Test Road"}, "zone_id": "missing"})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ZONE_NOT_FOUND"


def test_zone_crud_generates_id_and_updates():
    boundary = {"type": "Polygon", "coordinates": [[[80.20, 13.00], [80.24, 13.00], [80.24, 13.04], [80.20, 13.00]]]}
    created = client.post("/api/v1/zones", json={"city_id": "city_01", "name": "South Chennai", "population": 50000, "boundary": boundary})
    assert created.status_code == 201
    zone = created.json()
    assert zone["id"]
    assert zone["created_at"]
    assert zone["boundary"] == boundary
    updated = client.patch(f"/api/v1/zones/{zone['id']}", json={"population": 60000})
    assert updated.status_code == 200
    assert updated.json()["population"] == 60000

