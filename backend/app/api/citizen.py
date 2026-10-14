from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.dependencies import get_complaint_event_publisher, require_user_id
from app.core.exceptions import ComplaintNotFoundError, ZoneNotFoundError
from app.db.session import get_db
from app.schemas.citizen import CitizenComplaintCreate
from app.services.citizen_portal import CitizenPortalService, InvalidComplaintStatusError
from app.services.users import UserNotFoundError

router = APIRouter(prefix="/citizen", tags=["citizen"])


def _call(action):
    try:
        return action()
    except UserNotFoundError:
        raise HTTPException(404, {"code": "USER_NOT_FOUND", "message": "The requested user was not found."})
    except ComplaintNotFoundError:
        raise HTTPException(404, {"code": "COMPLAINT_NOT_FOUND", "message": "The requested complaint was not found."})
    except ZoneNotFoundError:
        raise HTTPException(404, {"code": "ZONE_NOT_FOUND", "message": "The requested zone was not found."})
    except InvalidComplaintStatusError:
        raise HTTPException(400, {"code": "INVALID_STATUS", "message": "Status filter is not recognized."})


def _file_base(request: Request) -> str:
    return str(request.base_url).rstrip("/")


@router.get("/homepage")
def homepage(db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    return {"data": _call(lambda: CitizenPortalService(db).homepage(user_id))}


@router.get("/complaint-form")
def complaint_form(db: Session = Depends(get_db)):
    return {"data": CitizenPortalService(db).complaint_form()}


@router.post("/complaint", status_code=201)
def create_complaint(
    payload: CitizenComplaintCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
    event_publisher=Depends(get_complaint_event_publisher),
):
    return {"data": _call(lambda: CitizenPortalService(db).create(user_id, payload, event_publisher))}


@router.get("/complaints")
def list_complaints(
    search: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(5, alias="pageSize", ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_user_id),
):
    return {"data": _call(lambda: CitizenPortalService(db).list_complaints(user_id, search, status, page, page_size))}


@router.get("/{complaint_id}")
def get_complaint(complaint_id: str, request: Request, db: Session = Depends(get_db), user_id: str = Depends(require_user_id)):
    return {"data": _call(lambda: CitizenPortalService(db).complaint(user_id, complaint_id, _file_base(request)))}
