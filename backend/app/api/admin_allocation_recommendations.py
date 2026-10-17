from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import require_city_admin
from app.db.session import get_db
from app.schemas.admin_allocation_recommendations import AllocationRecommendationResponse
from app.services.admin_allocation_recommendations import AdminAllocationRecommendationService


router = APIRouter(prefix="/admin/allocation-recommendations", tags=["admin-allocation-recommendations"])


@router.get("/{recommendation_id}", response_model=AllocationRecommendationResponse)
def allocation_recommendation_details(recommendation_id: str, admin_context=Depends(require_city_admin), db: Session = Depends(get_db)):
    _, city = admin_context
    result = AdminAllocationRecommendationService(db).get(recommendation_id, city.id)
    if result is None:
        raise HTTPException(404, {"code": "RECOMMENDATION_NOT_FOUND", "message": "The requested recommendation was not found."})
    return result
