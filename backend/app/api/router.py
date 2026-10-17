from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.api.dependencies import get_complaint_event_publisher, get_image_storage, get_user_id
from app.core.exceptions import ComplaintNotFoundError, ZoneNotFoundError
from app.db.session import get_db
from app.schemas.complaints import ComplaintCreate, ComplaintList, ComplaintRead, ErrorResponse, Location
from app.services.complaints import ComplaintService
from app.services.users import UserNotFoundError, UserService
from app.schemas.users import UserCreate, UserList, UserRead, UserUpdate
from app.schemas.zones import ZoneCreate, ZoneList, ZoneRead, ZoneUpdate
from app.services.zones import CityNotFoundError as ZoneCityNotFoundError, ZoneService, ZoneNotFoundError as ServiceZoneNotFoundError
from app.schemas.cities import CityCreate, CityList, CityRead, CityUpdate
from app.services.cities import CityAdministratorNotFoundError, CityNotFoundError, CityService
from app.schemas.landmarks import LandmarkCreate, LandmarkList, LandmarkRead, LandmarkUpdate
from app.services.landmarks import LandmarkNotFoundError, LandmarkService, LandmarkZoneNotFoundError
from app.schemas.incidents import IncidentList, IncidentRead, IncidentStatusUpdate
from app.services.incidents import IncidentAdministratorError, IncidentNotFoundError, IncidentService
from app.api.citizen import router as citizen_router
from app.api.admin_dashboard import router as admin_dashboard_router
from app.api.admin_incidents import router as admin_incidents_router
from app.api.admin_complaints import router as admin_complaints_router
from app.api.admin_allocation_recommendations import router as admin_allocation_recommendations_router
from app.api.admin_assignments import router as admin_assignments_router
from app.domain.incidents import IncidentStatus
from app.domain.complaints import ComplaintCategory, ComplaintStatus

router = APIRouter(prefix="/api/v1")
router.include_router(citizen_router)
router.include_router(admin_dashboard_router)
router.include_router(admin_incidents_router)
router.include_router(admin_complaints_router)
router.include_router(admin_allocation_recommendations_router)
router.include_router(admin_assignments_router)


def to_read(complaint) -> ComplaintRead:
    return ComplaintRead(id=complaint.id, title=complaint.title, description=complaint.description,
        category=complaint.category, location=Location(latitude=complaint.latitude, longitude=complaint.longitude, address=complaint.address),
        zone_id=complaint.zone_id, status=complaint.status, priority_score=complaint.priority_score,
        created_at=complaint.created_at, updated_at=complaint.updated_at,
        image_ids=[image.image_id for image in complaint.images])


@router.post("/complaints", response_model=ComplaintRead, status_code=status.HTTP_201_CREATED, responses={404: {"model": ErrorResponse}})
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db), user_id: str | None = Depends(get_user_id), event_publisher=Depends(get_complaint_event_publisher)):
    try:
        return to_read(ComplaintService(db).create(payload, user_id, event_publisher))
    except ZoneNotFoundError:
        raise HTTPException(404, {"code": "ZONE_NOT_FOUND", "message": "The requested zone was not found."})
    except ValueError:
        raise HTTPException(400, {"code": "USER_REQUIRED", "message": "A valid X-User-Id header is required."})


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    return UserService(db).create(payload)


@router.get("/users", response_model=UserList)
def list_users(db: Session = Depends(get_db)):
    items, total = UserService(db).list()
    return UserList(items=items, total=total)


@router.get("/users/{user_id}", response_model=UserRead, responses={404: {"model": ErrorResponse}})
def get_user(user_id: str, db: Session = Depends(get_db)):
    try:
        return UserService(db).get(user_id)
    except UserNotFoundError:
        raise HTTPException(404, {"code": "USER_NOT_FOUND", "message": "The requested user was not found."})


@router.patch("/users/{user_id}", response_model=UserRead, responses={404: {"model": ErrorResponse}})
def update_user(user_id: str, payload: UserUpdate, db: Session = Depends(get_db)):
    try:
        return UserService(db).update(user_id, payload)
    except UserNotFoundError:
        raise HTTPException(404, {"code": "USER_NOT_FOUND", "message": "The requested user was not found."})


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, responses={404: {"model": ErrorResponse}})
def delete_user(user_id: str, db: Session = Depends(get_db)):
    try:
        UserService(db).delete(user_id)
    except UserNotFoundError:
        raise HTTPException(404, {"code": "USER_NOT_FOUND", "message": "The requested user was not found."})
    return None


@router.post("/zones", response_model=ZoneRead, status_code=status.HTTP_201_CREATED)
def create_zone(payload: ZoneCreate, db: Session = Depends(get_db)):
    try:
        return ZoneService(db).create(payload)
    except ZoneCityNotFoundError:
        raise HTTPException(404, {"code": "CITY_NOT_FOUND", "message": "The requested city was not found."})


@router.get("/zones", response_model=ZoneList)
def list_zones(db: Session = Depends(get_db)):
    items, total = ZoneService(db).list()
    return ZoneList(items=items, total=total)


@router.get("/zones/{zone_id}", response_model=ZoneRead, responses={404: {"model": ErrorResponse}})
def get_zone(zone_id: str, db: Session = Depends(get_db)):
    try:
        return ZoneService(db).get(zone_id)
    except ServiceZoneNotFoundError:
        raise HTTPException(404, {"code": "ZONE_NOT_FOUND", "message": "The requested zone was not found."})


@router.patch("/zones/{zone_id}", response_model=ZoneRead, responses={404: {"model": ErrorResponse}})
def update_zone(zone_id: str, payload: ZoneUpdate, db: Session = Depends(get_db)):
    try:
        return ZoneService(db).update(zone_id, payload)
    except ServiceZoneNotFoundError:
        raise HTTPException(404, {"code": "ZONE_NOT_FOUND", "message": "The requested zone was not found."})
    except ZoneCityNotFoundError:
        raise HTTPException(404, {"code": "CITY_NOT_FOUND", "message": "The requested city was not found."})


@router.delete("/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT, responses={404: {"model": ErrorResponse}})
def delete_zone(zone_id: str, db: Session = Depends(get_db)):
    try:
        ZoneService(db).delete(zone_id)
    except ServiceZoneNotFoundError:
        raise HTTPException(404, {"code": "ZONE_NOT_FOUND", "message": "The requested zone was not found."})
    return None


@router.post("/cities", response_model=CityRead, status_code=status.HTTP_201_CREATED)
def create_city(payload: CityCreate, db: Session = Depends(get_db)):
    try:
        return CityService(db).create(payload)
    except CityAdministratorNotFoundError:
        raise HTTPException(404, {"code": "CITY_ADMIN_NOT_FOUND", "message": "The requested city administrator was not found."})


@router.get("/cities", response_model=CityList)
def list_cities(db: Session = Depends(get_db)):
    items, total = CityService(db).list()
    return CityList(items=items, total=total)


@router.get("/cities/{city_id}", response_model=CityRead, responses={404: {"model": ErrorResponse}})
def get_city(city_id: str, db: Session = Depends(get_db)):
    try:
        return CityService(db).get(city_id)
    except CityNotFoundError:
        raise HTTPException(404, {"code": "CITY_NOT_FOUND", "message": "The requested city was not found."})
    except CityAdministratorNotFoundError:
        raise HTTPException(404, {"code": "CITY_ADMIN_NOT_FOUND", "message": "The requested city administrator was not found."})


@router.patch("/cities/{city_id}", response_model=CityRead, responses={404: {"model": ErrorResponse}})
def update_city(city_id: str, payload: CityUpdate, db: Session = Depends(get_db)):
    try:
        return CityService(db).update(city_id, payload)
    except CityNotFoundError:
        raise HTTPException(404, {"code": "CITY_NOT_FOUND", "message": "The requested city was not found."})


@router.delete("/cities/{city_id}", status_code=status.HTTP_204_NO_CONTENT, responses={404: {"model": ErrorResponse}})
def delete_city(city_id: str, db: Session = Depends(get_db)):
    try:
        CityService(db).delete(city_id)
    except CityNotFoundError:
        raise HTTPException(404, {"code": "CITY_NOT_FOUND", "message": "The requested city was not found."})
    return None


@router.post("/zones/{zone_id}/landmarks", response_model=LandmarkRead, status_code=status.HTTP_201_CREATED, responses={404: {"model": ErrorResponse}})
def create_landmark(zone_id: str, payload: LandmarkCreate, db: Session = Depends(get_db)):
    try:
        return LandmarkService(db).create(zone_id, payload)
    except LandmarkZoneNotFoundError:
        raise HTTPException(404, {"code": "ZONE_NOT_FOUND", "message": "The requested zone was not found."})


@router.get("/zones/{zone_id}/landmarks", response_model=LandmarkList, responses={404: {"model": ErrorResponse}})
def list_landmarks(zone_id: str, db: Session = Depends(get_db)):
    try:
        items, total = LandmarkService(db).list_for_zone(zone_id)
        return LandmarkList(items=items, total=total)
    except LandmarkZoneNotFoundError:
        raise HTTPException(404, {"code": "ZONE_NOT_FOUND", "message": "The requested zone was not found."})


@router.get("/landmarks/{landmark_id}", response_model=LandmarkRead, responses={404: {"model": ErrorResponse}})
def get_landmark(landmark_id: str, db: Session = Depends(get_db)):
    try:
        return LandmarkService(db).get(landmark_id)
    except LandmarkNotFoundError:
        raise HTTPException(404, {"code": "LANDMARK_NOT_FOUND", "message": "The requested landmark was not found."})


@router.patch("/landmarks/{landmark_id}", response_model=LandmarkRead, responses={404: {"model": ErrorResponse}})
def update_landmark(landmark_id: str, payload: LandmarkUpdate, db: Session = Depends(get_db)):
    try:
        return LandmarkService(db).update(landmark_id, payload)
    except LandmarkNotFoundError:
        raise HTTPException(404, {"code": "LANDMARK_NOT_FOUND", "message": "The requested landmark was not found."})


@router.delete("/landmarks/{landmark_id}", status_code=status.HTTP_204_NO_CONTENT, responses={404: {"model": ErrorResponse}})
def delete_landmark(landmark_id: str, db: Session = Depends(get_db)):
    try:
        LandmarkService(db).delete(landmark_id)
    except LandmarkNotFoundError:
        raise HTTPException(404, {"code": "LANDMARK_NOT_FOUND", "message": "The requested landmark was not found."})
    return None


def to_incident_read(incident) -> IncidentRead:
    return IncidentRead(id=incident.id, city_id=incident.city_id, zone_id=incident.zone_id,
        category=incident.category, title=incident.title, description=incident.description,
        status=incident.status, priority_score=incident.priority_score,
        complaint_count=len(incident.complaint_links), created_at=incident.created_at,
        updated_at=incident.updated_at)


@router.get("/incidents", response_model=IncidentList)
def list_incidents(status_filter: IncidentStatus | None = Query(default=None, alias="status"), db: Session = Depends(get_db)):
    items, total = IncidentService(db).list(status_filter)
    return IncidentList(items=[to_incident_read(item) for item in items], total=total)


@router.get("/incidents/{incident_id}", response_model=IncidentRead, responses={404: {"model": ErrorResponse}})
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    try:
        return to_incident_read(IncidentService(db).get(incident_id))
    except IncidentNotFoundError:
        raise HTTPException(404, {"code": "INCIDENT_NOT_FOUND", "message": "The requested incident was not found."})


@router.patch("/incidents/{incident_id}/status", response_model=IncidentRead, responses={403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def update_incident_status(incident_id: str, payload: IncidentStatusUpdate, db: Session = Depends(get_db), user_id: str | None = Depends(get_user_id)):
    try:
        return to_incident_read(IncidentService(db).update_status(incident_id, payload, user_id))
    except IncidentNotFoundError:
        raise HTTPException(404, {"code": "INCIDENT_NOT_FOUND", "message": "The requested incident was not found."})
    except IncidentAdministratorError:
        raise HTTPException(403, {"code": "CITY_ADMIN_REQUIRED", "message": "Only the administrator of this incident's city can update its status."})


@router.get("/complaints", response_model=ComplaintList)
def list_complaints(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), category: ComplaintCategory | None = None, status: ComplaintStatus | None = None, db: Session = Depends(get_db)):
    items, total = ComplaintService(db).list(skip, limit, category, status)
    return ComplaintList(items=[to_read(item) for item in items], skip=skip, limit=limit, total=total)


_IMAGE_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/svg+xml": "svg",
}
_MAX_IMAGE_BYTES = 5_000_000


@router.post("/complaint-images", status_code=status.HTTP_201_CREATED, responses={400: {"model": ErrorResponse}})
async def upload_complaint_image(request: Request, storage=Depends(get_image_storage)):
    content_type = (request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    extension = _IMAGE_EXTENSIONS.get(content_type)
    if extension is None:
        raise HTTPException(400, {"code": "UNSUPPORTED_IMAGE_TYPE", "message": "Upload a JPG, PNG, WEBP, GIF, or SVG image."})
    data = await request.body()
    if not data:
        raise HTTPException(400, {"code": "EMPTY_IMAGE", "message": "The image file is empty."})
    if len(data) > _MAX_IMAGE_BYTES:
        raise HTTPException(400, {"code": "IMAGE_TOO_LARGE", "message": "Images must be 5 MB or smaller."})
    image_id = f"{uuid4().hex}.{extension}"
    mime_type = "image/jpeg" if content_type == "image/jpg" else content_type
    try:
        storage.upload(image_id, data, mime_type)
    except (OSError, ValueError):
        raise HTTPException(503, {"code": "IMAGE_STORAGE_UNAVAILABLE", "message": "Image upload is not available."})
    return {"image_id": image_id}


@router.get("/complaint-images/{image_id:path}", responses={404: {"model": ErrorResponse}})
def get_complaint_image(image_id: str, storage=Depends(get_image_storage)):
    asset = storage.download(image_id)
    if asset is None:
        raise HTTPException(404, {"code": "IMAGE_NOT_FOUND", "message": "The requested image was not found."})
    return Response(content=asset.data, media_type=asset.mime_type, headers={"Cache-Control": "public, max-age=86400"})


@router.get("/complaints/{complaint_id}", response_model=ComplaintRead, responses={404: {"model": ErrorResponse}})
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    try:
        return to_read(ComplaintService(db).get(complaint_id))
    except ComplaintNotFoundError:
        raise HTTPException(404, {"code": "COMPLAINT_NOT_FOUND", "message": "The requested complaint was not found."})

