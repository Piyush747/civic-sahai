from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.db.models import City, Zone
from app.db.session import get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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


def test_uploaded_complaint_photo_can_be_loaded():
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    uploaded = client.post("/api/v1/complaint-images", content=png, headers={"Content-Type": "image/png"})
    assert uploaded.status_code == 201
    image_id = uploaded.json()["image_id"]

    user = client.post("/api/v1/users", json={"name": "Photo Citizen", "email": "photo@example.com"})
    created = client.post(
        "/api/v1/complaints",
        headers={"X-User-Id": user.json()["id"]},
        json={
            "title": "Pothole with photo",
            "description": "A pothole with a photo attached for the crew.",
            "category": "ROAD_DAMAGE",
            "location": {"latitude": 13, "longitude": 80, "address": "Photo Road"},
            "zone_id": "zone_01",
            "image_ids": [image_id],
        },
    )
    assert created.status_code == 201
    complaint_id = created.json()["id"]
    assert created.json()["image_ids"] == [image_id]

    fetched = client.get(f"/api/v1/complaints/{complaint_id}")
    assert fetched.status_code == 200
    assert fetched.json()["image_ids"] == [image_id]

    image = client.get(f"/api/v1/complaint-images/{image_id}")
    assert image.status_code == 200
    assert image.headers["content-type"].startswith("image/png")
    assert image.content == png


def test_citizen_routes_require_user_id():
    missing = client.get("/api/v1/citizen/homepage")
    assert missing.status_code == 400
    assert missing.json()["error"] == {"code": "USER_ID_REQUIRED", "message": "X-User-Id header is required."}
    blank = client.get("/api/v1/citizen/complaints", headers={"X-User-Id": "   "})
    assert blank.status_code == 400
    assert blank.json()["error"]["code"] == "USER_ID_REQUIRED"
    unknown = client.get("/api/v1/citizen/homepage", headers={"X-User-Id": "missing-citizen"})
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "USER_NOT_FOUND"
    form = client.get("/api/v1/citizen/complaint-form")
    assert form.status_code == 200
    names = [field["name"] for field in form.json()["data"]["form"]["fields"]]
    assert names == ["category", "description", "location.address", "attachments"]


def test_citizen_portal_scopes_complaints_to_the_header_user():
    owner = client.post("/api/v1/users", json={"name": "Piyush Jain", "email": "piyush-portal@example.com"}).json()
    other = client.post("/api/v1/users", json={"name": "Other Citizen", "email": "other-portal@example.com"}).json()
    payload = {
        "category": "ROAD_DAMAGE",
        "description": "There is a large pothole near the bus stop, making it difficult for vehicles to pass safely.",
        "location": {"address": "Sector 15, Main Road", "landmark": "Near the bus stop", "latitude": 12.9784, "longitude": 77.6408},
        "attachments": [{"fileId": "file-2001"}],
    }
    created = client.post("/api/v1/citizen/complaint", headers={"X-User-Id": owner["id"]}, json=payload)
    assert created.status_code == 201
    body = created.json()["data"]
    assert body["status"] == "SUBMITTED"
    assert body["referenceNumber"].startswith("CS-")
    assert body["location"]["landmark"] == "Near the bus stop"
    assert body["location"]["zoneId"]
    assert body["attachments"] == [{"fileId": "file-2001", "status": "ATTACHED"}]
    assert body["message"] == "Your complaint has been submitted successfully."
    complaint_id = body["complaintId"]

    other_created = client.post(
        "/api/v1/citizen/complaint",
        headers={"X-User-Id": other["id"]},
        json={
            "category": "ROAD_DAMAGE",
            "description": "Another pothole was reported beside the same bus stop this morning.",
            "location": {"address": "Sector 15, Main Road", "latitude": 12.98, "longitude": 77.64},
        },
    )
    assert other_created.status_code == 201
    other_id = other_created.json()["data"]["complaintId"]

    hidden = client.get(f"/api/v1/citizen/{other_id}", headers={"X-User-Id": owner["id"]})
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "COMPLAINT_NOT_FOUND"

    homepage = client.get("/api/v1/citizen/homepage", headers={"X-User-Id": owner["id"]})
    assert homepage.status_code == 200
    page = homepage.json()["data"]
    assert page["header"]["profileInitials"] == "PJ"
    assert page["welcomeSection"]["greeting"].endswith(", Piyush")
    assert page["summaryCards"][0] == {"key": "TOTAL", "title": "Total complaints", "count": 1, "description": "All reports you submitted"}
    assert [item["complaintId"] for item in page["complaints"]] == [complaint_id]

    detail = client.get(f"/api/v1/citizen/{complaint_id}", headers={"X-User-Id": owner["id"]})
    assert detail.status_code == 200
    detail_body = detail.json()["data"]
    assert detail_body["complaint"]["status"] == "SUBMITTED"
    assert detail_body["complaint"]["referenceNumber"] == body["referenceNumber"]
    assert detail_body["progressSection"]["events"][0]["type"] == "REPORT_RECEIVED"
    similar_ids = [item["complaintId"] for item in detail_body["similarComplaints"]]
    assert other_id in similar_ids
    assert complaint_id not in similar_ids
    assert all(item["reporterDetailsVisibility"] == "PRIVATE" for item in detail_body["similarComplaints"])

    listing = client.get(
        "/api/v1/citizen/complaints",
        headers={"X-User-Id": owner["id"]},
        params={"search": "pothole", "status": "SUBMITTED", "page": 1, "pageSize": 5},
    )
    assert listing.status_code == 200
    listed = listing.json()["data"]
    assert listed["pagination"]["totalItems"] == 1
    assert listed["pagination"]["displayText"] == "Showing 1–1 of 1"
    assert listed["complaints"][0]["complaintId"] == complaint_id
    assert listed["summary"]["totalCount"] == 1
    no_header = client.post("/api/v1/citizen/complaint", json=payload)
    assert no_header.status_code == 400
    assert no_header.json()["error"]["code"] == "USER_ID_REQUIRED"


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

