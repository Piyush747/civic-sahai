from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_city_admin
from app.db.session import get_db
from app.schemas.admin_dashboard import CityOverviewResponse, ZoneOverviewResponse
from app.services.admin_dashboard import AdminDashboardService

router = APIRouter(prefix="/admin", tags=["admin-dashboard"])


@router.get("/dashboard/overview", response_model=CityOverviewResponse)
def overview(
    period: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    admin_context=Depends(require_city_admin),
    db: Session = Depends(get_db),
):
    _, city = admin_context
    return AdminDashboardService(db).overview(city, period, from_date, to_date)


@router.get("/zones/{zone_id}/overview", response_model=ZoneOverviewResponse)
def zone_overview(
    zone_id: str,
    period: str | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    admin_context=Depends(require_city_admin),
    db: Session = Depends(get_db),
):
    _, city = admin_context
    from fastapi import HTTPException
    from app.db.models import Zone
    zone = db.get(Zone, zone_id)
    if zone is None or zone.city_id != city.id:
        raise HTTPException(404, {"code": "ZONE_NOT_FOUND", "message": "The requested zone was not found."})
    return AdminDashboardService(db).zone_overview(city, zone, period, from_date, to_date)
