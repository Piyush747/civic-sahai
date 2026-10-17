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
    test_boundary = {
        "type": "Polygon",
        "coordinates": [[[80.20, 13.00], [80.24, 13.00], [80.24, 13.04], [80.20, 13.04], [80.20, 13.00]]],
    }
    db.add(Zone(id="zone_01", city_id="city_01", name="Test", population=1, boundary=test_boundary))
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
    response = client.post("/api/v1/complaints", headers={"X-User-Id": user.json()["id"]}, json={"title": "Broken streetlight", "description": "The streetlight has been out for three nights.", "category": "STREETLIGHT", "location": {"latitude": 13, "longitude": 80, "address": "Test Road"}, "zone_id": "zone_01", "image_ids": ["file-1"]})
    assert response.status_code == 201
    complaint_id = response.json()["id"]
    assert client.get(f"/api/v1/complaints/{complaint_id}").status_code == 200


def test_missing_zone_is_stable_error():
    user = client.post("/api/v1/users", json={"name": "Another Citizen", "email": "another@example.com"})
    response = client.post("/api/v1/complaints", headers={"X-User-Id": user.json()["id"]}, json={"title": "Broken road", "description": "A very large pothole is dangerous.", "category": "ROAD_DAMAGE", "location": {"latitude": 13, "longitude": 80, "address": "Test Road"}, "zone_id": "missing", "image_ids": ["file-1"]})
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
    photos = next(field for field in form.json()["data"]["form"]["fields"] if field["name"] == "attachments")
    assert photos["required"] is True
    assert photos["label"] == "Photos"
    assert photos["minFiles"] == 1


def test_complaint_requires_a_photo():
    user = client.post("/api/v1/users", json={"name": "Photo Required", "email": "photo-required@example.com"}).json()
    payload = {
        "category": "ROAD_DAMAGE",
        "description": "There is a large pothole near the bus stop, making it difficult for vehicles to pass safely.",
        "location": {"address": "Sector 15, Main Road", "latitude": 13.02, "longitude": 80.22},
    }
    missing = client.post("/api/v1/citizen/complaint", headers={"X-User-Id": user["id"]}, json=payload)
    assert missing.status_code == 422
    empty = client.post(
        "/api/v1/citizen/complaint",
        headers={"X-User-Id": user["id"]},
        json={**payload, "attachments": []},
    )
    assert empty.status_code == 422
    internal = client.post(
        "/api/v1/complaints",
        headers={"X-User-Id": user["id"]},
        json={
            "title": "Broken streetlight",
            "description": "The streetlight has been out for three nights.",
            "category": "STREETLIGHT",
            "location": {"latitude": 13, "longitude": 80, "address": "Test Road"},
            "zone_id": "zone_01",
        },
    )
    assert internal.status_code == 422


def test_citizen_portal_scopes_complaints_to_the_header_user():
    owner = client.post("/api/v1/users", json={"name": "Piyush Jain", "email": "piyush-portal@example.com"}).json()
    other = client.post("/api/v1/users", json={"name": "Other Citizen", "email": "other-portal@example.com"}).json()
    payload = {
        "category": "ROAD_DAMAGE",
        "description": "There is a large pothole near the bus stop, making it difficult for vehicles to pass safely.",
        "location": {"address": "Sector 15, Main Road", "landmark": "Near the bus stop", "latitude": 13.02, "longitude": 80.22},
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
            "location": {"address": "Sector 15, Main Road", "latitude": 13.01, "longitude": 80.21},
            "attachments": [{"fileId": "file-2002"}],
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
    assert page["helpSection"] == {
        "title": "Need help?",
        "description": "Call the civic helpline if you have questions about a report, or if location or issue details need to be corrected.",
        "phoneLabel": "Civic helpline",
        "phoneNumber": "1800-123-1916",
        "hours": "Monday to Saturday, 8:00 AM – 8:00 PM",
    }
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


def test_location_suggestions_rank_saved_landmarks_ahead_of_nearby_places(monkeypatch):
    from app.db.models import Landmark

    with TestingSession() as db:
        if db.get(Landmark, "landmark_near") is None:
            db.add(Landmark(id="landmark_far", zone_id="zone_01", name="Far Hospital", landmark_type="HOSPITAL", latitude=13.2, longitude=80.2, criticality_weight=1))
            db.add(Landmark(id="landmark_near", zone_id="zone_01", name="Near School", landmark_type="SCHOOL", latitude=13.001, longitude=80.001, criticality_weight=1))
            db.commit()

    def places(_latitude, _longitude):
        return [{"name": "Anna Salai", "kind": "road", "latitude": 13.0, "longitude": 80.0}]

    monkeypatch.setattr("app.services.citizen_portal.search_nearby_places", places)
    response = client.get("/api/v1/citizen/location-suggestions", params={"latitude": 13.0, "longitude": 80.0})
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["landmarks"][0]["name"] == "Near School"
    assert "Far Hospital" not in [item["name"] for item in body["landmarks"]]
    assert body["landmarks"][0]["landmarkType"] == "SCHOOL"
    assert body["landmarks"][0]["distanceMeters"] < 500
    assert body["nearbyPlaces"] == [{"name": "Anna Salai", "kind": "road", "latitude": 13.0, "longitude": 80.0}]

    def unavailable(_latitude, _longitude):
        raise OSError("overpass down")

    monkeypatch.setattr("app.services.citizen_portal.search_nearby_places", unavailable)
    fallback = client.get("/api/v1/citizen/location-suggestions", params={"latitude": 13.0, "longitude": 80.0})
    assert fallback.status_code == 200
    assert fallback.json()["data"]["nearbyPlaces"] == []
    assert fallback.json()["data"]["landmarks"][0]["name"] == "Near School"


def test_nearby_place_parsers_keep_named_places_nearest_first():
    from app.integrations.nearby_places import places_from_nominatim, places_from_overpass

    overpass = places_from_overpass(
        {
            "elements": [
                {"type": "node", "lat": 13.01, "lon": 80.01, "tags": {"name": "Spencer Plaza", "amenity": "marketplace"}},
                {"type": "node", "lat": 13.02, "lon": 80.02, "tags": {"amenity": "cafe"}},
                {"type": "node", "lat": 13.2, "lon": 80.2, "tags": {"name": "Far Park", "leisure": "park"}},
            ]
        },
        13.0,
        80.0,
    )
    assert [item["name"] for item in overpass] == ["Spencer Plaza", "Far Park"]
    assert overpass[0]["kind"] == "marketplace"
    nominatim = places_from_nominatim(
        {"lat": "13.08", "lon": "80.27", "address": {"road": "Anna Salai", "suburb": "Teynampet", "city": "Chennai"}}
    )
    assert [item["name"] for item in nominatim] == ["Anna Salai", "Teynampet"]
    assert nominatim[0]["kind"] == "road"


def test_location_status_and_outside_service_area_complaints():
    inside = client.get("/api/v1/citizen/location-status", params={"latitude": 13.02, "longitude": 80.22})
    assert inside.status_code == 200
    assert inside.json()["data"]["inServiceArea"] is True
    assert inside.json()["data"]["cityName"] == "Test City"
    assert inside.json()["data"]["zoneId"] == "zone_01"

    outside = client.get("/api/v1/citizen/location-status", params={"latitude": 12.97, "longitude": 77.59})
    assert outside.status_code == 200
    assert outside.json()["data"]["inServiceArea"] is False
    assert outside.json()["data"]["cityName"] == "Test City"

    user = client.post("/api/v1/users", json={"name": "Outside Citizen", "email": "outside@example.com"}).json()
    rejected = client.post(
        "/api/v1/citizen/complaint",
        headers={"X-User-Id": user["id"]},
        json={
            "category": "ROAD_DAMAGE",
            "description": "There is a large pothole outside the city service area for this portal.",
            "location": {"address": "MG Road", "latitude": 12.97, "longitude": 77.59},
            "attachments": [{"fileId": "file-outside"}],
        },
    )
    assert rejected.status_code == 400
    assert rejected.json()["error"]["code"] == "OUTSIDE_SERVICE_AREA"


def test_location_search_lists_matching_places(monkeypatch):
    def places(query, latitude=None, longitude=None):
        assert query == "Marina"
        assert latitude == 13.0827
        assert longitude == 80.2707
        return [{"name": "Marina Beach", "label": "Marina Beach, Chennai", "latitude": 13.05, "longitude": 80.28}]

    monkeypatch.setattr("app.services.citizen_portal.search_places", places)
    response = client.get(
        "/api/v1/citizen/location-search",
        params={"q": "Marina", "latitude": 13.0827, "longitude": 80.2707},
    )
    assert response.status_code == 200
    assert response.json()["data"]["places"] == [
        {"name": "Marina Beach", "label": "Marina Beach, Chennai", "latitude": 13.05, "longitude": 80.28}
    ]

    def unavailable(_query, latitude=None, longitude=None):
        raise OSError("nominatim down")

    monkeypatch.setattr("app.services.citizen_portal.search_places", unavailable)
    fallback = client.get(
        "/api/v1/citizen/location-search",
        params={"q": "Marina", "latitude": 13.0827, "longitude": 80.2707},
    )
    assert fallback.status_code == 200
    assert fallback.json()["data"]["places"] == []
    assert client.get("/api/v1/citizen/location-search", params={"q": "M"}).status_code == 422


def test_place_search_parser_uses_the_display_name():
    from app.integrations.nearby_places import places_from_search

    places = places_from_search(
        [
            {"display_name": "Marina Beach, Chennai, Tamil Nadu, India", "lat": "13.0500", "lon": "80.2824"},
            {"display_name": "Marina Beach, Chennai, Tamil Nadu, India", "lat": "13.0500", "lon": "80.2824"},
            {"lat": "13.0", "lon": "80.0"},
        ]
    )
    assert places == [
        {
            "name": "Marina Beach",
            "label": "Marina Beach, Chennai, Tamil Nadu, India",
            "latitude": 13.05,
            "longitude": 80.2824,
        }
    ]


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

