from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ZoneCreate(BaseModel):
    city_id: str = Field(min_length=1, max_length=36)
    name: str = Field(min_length=1, max_length=120)
    population: int = Field(default=0, ge=0)
    boundary: dict[str, Any] | None = None

    @model_validator(mode="after")
    def boundary_is_polygon(self):
        validate_boundary(self.boundary)
        return self


class ZoneUpdate(BaseModel):
    city_id: str | None = Field(default=None, min_length=1, max_length=36)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    population: int | None = Field(default=None, ge=0)
    boundary: dict[str, Any] | None = None

    @model_validator(mode="after")
    def boundary_is_polygon(self):
        validate_boundary(self.boundary)
        return self


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    city_id: str
    name: str
    population: int
    boundary: dict[str, Any] | None
    created_at: datetime


class ZoneList(BaseModel):
    items: list[ZoneRead]
    total: int


def validate_boundary(boundary: dict[str, Any] | None) -> None:
    if boundary is None:
        return
    if boundary.get("type") != "Polygon":
        raise ValueError("boundary.type must be Polygon")
    coordinates = boundary.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates or not isinstance(coordinates[0], list):
        raise ValueError("boundary.coordinates must contain a polygon ring")
    ring = coordinates[0]
    if len(ring) < 4 or ring[0] != ring[-1]:
        raise ValueError("the polygon boundary ring must have at least four closed points")
    for point in ring:
        if not isinstance(point, list) or len(point) < 2 or not all(isinstance(value, (int, float)) for value in point[:2]):
            raise ValueError("polygon points must be [longitude, latitude] coordinates")
        longitude, latitude = point[:2]
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise ValueError("polygon coordinates are outside valid geographic ranges")

