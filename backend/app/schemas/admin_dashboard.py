from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Period = Literal["7d", "15d", "30d", "90d"]


class PolygonGeometry(BaseModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[float]]]

    @field_validator("coordinates")
    @classmethod
    def validate_polygon(cls, rings: list[list[list[float]]]) -> list[list[list[float]]]:
        if not rings or len(rings[0]) < 4 or rings[0][0] != rings[0][-1]:
            raise ValueError("Polygon rings must contain at least four coordinates and be closed")
        for ring in rings:
            for point in ring:
                if len(point) != 2 or not (-180 <= point[0] <= 180 and -90 <= point[1] <= 90):
                    raise ValueError("Polygon coordinates must be [longitude, latitude]")
        return rings


class ZonePressure(BaseModel):
    zone_id: str
    zone_name: str
    open_incidents: int = Field(ge=0)
    available_teams: float = Field(ge=0)
    deployed_teams: float = Field(ge=0)
    total_teams: float = Field(ge=0)
    pressure_level: Literal["overloaded", "under_pressure", "balanced", "spare_capacity"]
    boundary: PolygonGeometry | None


class IncidentTrend(BaseModel):
    date: date
    reported: int = Field(ge=0)
    resolved: int = Field(ge=0)


class DashboardSummary(BaseModel):
    open_incidents: int = Field(ge=0)
    in_progress_incidents: int = Field(ge=0)
    resolved_incidents: int = Field(ge=0)
    waiting_too_long_incidents: int = Field(ge=0)


class CityOverviewResponse(BaseModel):
    summary: DashboardSummary
    zone_pressure: list[ZonePressure]
    incident_trends: list[IncidentTrend]
    period: Period | None
    from_date: date
    to_date: date
    timezone: str
    data_as_of: datetime


class ZoneOverviewZone(BaseModel):
    id: str
    name: str
    city_id: str
    pressure_level: Literal["overloaded", "under_pressure", "balanced", "spare_capacity"]


class IncidentTypeSummary(BaseModel):
    incident_type_id: str
    name: str
    incident_count: int = Field(ge=0)


class AssignmentQueueItem(BaseModel):
    incident_id: str
    incident_type_id: str
    incident_type: str
    priority: str | None
    created_at: datetime
    waiting_too_long: bool


class AssignmentQueue(BaseModel):
    total_count: int = Field(ge=0)
    items: list[AssignmentQueueItem]


class ResponseHealth(BaseModel):
    available_teams: int = Field(ge=0)
    deployed_teams: int = Field(ge=0)
    total_teams: int = Field(ge=0)
    pressure_level: Literal["overloaded", "under_pressure", "balanced", "spare_capacity"]


class ZoneOverviewData(BaseModel):
    zone: ZoneOverviewZone
    summary: DashboardSummary
    incident_types: list[IncidentTypeSummary]
    incident_trends: list[IncidentTrend]
    assignment_queue: AssignmentQueue
    response_health: ResponseHealth


class ZoneOverviewMeta(BaseModel):
    period: Period | None
    from_date: date
    to_date: date
    timezone: str
    data_as_of: datetime


class ZoneOverviewResponse(BaseModel):
    data: ZoneOverviewData
    meta: ZoneOverviewMeta
