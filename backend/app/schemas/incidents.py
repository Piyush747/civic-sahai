from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.domain.complaints import ComplaintCategory
from app.domain.incidents import IncidentStatus


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    city_id: str
    zone_id: str
    category: ComplaintCategory
    title: str
    description: str
    status: IncidentStatus
    priority_score: float | None
    complaint_count: int
    created_at: datetime
    updated_at: datetime


class IncidentList(BaseModel):
    items: list[IncidentRead]
    total: int


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus
