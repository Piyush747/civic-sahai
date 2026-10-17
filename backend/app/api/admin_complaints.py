from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import require_city_admin
from app.db.session import get_db
from app.schemas.admin_complaints import AdminComplaintDetailsResponse
from app.services.admin_complaints import AdminComplaintDetailsService


router = APIRouter(prefix="/admin/complaints", tags=["admin-complaints"])


@router.get("/{complaint_id}", response_model=AdminComplaintDetailsResponse)
def complaint_details(complaint_id: str, admin_context=Depends(require_city_admin), db: Session = Depends(get_db)):
    _, city = admin_context
    result = AdminComplaintDetailsService(db).get(complaint_id, city.id)
    if result is None:
        raise HTTPException(404, {"code": "COMPLAINT_NOT_FOUND", "message": "The requested complaint could not be found."})
    return result
