from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_user_id
from app.core.exceptions import ComplaintNotFoundError, ZoneNotFoundError
from app.db.session import get_db
from app.schemas.complaints import ComplaintCreate, ComplaintList, ComplaintRead, ErrorResponse, Location
from app.services.complaints import ComplaintService
from app.domain.complaints import ComplaintCategory, ComplaintStatus

router = APIRouter(prefix="/api/v1")


def to_read(complaint) -> ComplaintRead:
    return ComplaintRead(id=complaint.id, title=complaint.title, description=complaint.description,
        category=complaint.category, location=Location(latitude=complaint.latitude, longitude=complaint.longitude, address=complaint.address),
        zone_id=complaint.zone_id, status=complaint.status, priority_score=complaint.priority_score,
        created_at=complaint.created_at, updated_at=complaint.updated_at)


@router.post("/complaints", response_model=ComplaintRead, status_code=status.HTTP_201_CREATED, responses={404: {"model": ErrorResponse}})
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db), user_id: str | None = Depends(get_user_id)):
    try:
        return to_read(ComplaintService(db).create(payload, user_id))
    except ZoneNotFoundError:
        raise HTTPException(404, {"code": "ZONE_NOT_FOUND", "message": "The requested zone was not found."})


@router.get("/complaints", response_model=ComplaintList)
def list_complaints(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), category: ComplaintCategory | None = None, status: ComplaintStatus | None = None, db: Session = Depends(get_db)):
    items, total = ComplaintService(db).list(skip, limit, category, status)
    return ComplaintList(items=[to_read(item) for item in items], skip=skip, limit=limit, total=total)


@router.get("/complaints/{complaint_id}", response_model=ComplaintRead, responses={404: {"model": ErrorResponse}})
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    try:
        return to_read(ComplaintService(db).get(complaint_id))
    except ComplaintNotFoundError:
        raise HTTPException(404, {"code": "COMPLAINT_NOT_FOUND", "message": "The requested complaint was not found."})

