from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class LandmarkCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    landmark_type: str = Field(min_length=1, max_length=64)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    criticality_weight: float = Field(default=1.0, ge=0)


class LandmarkUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    landmark_type: str | None = Field(default=None, min_length=1, max_length=64)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    criticality_weight: float | None = Field(default=None, ge=0)


class LandmarkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    zone_id: str
    name: str
    landmark_type: str
    latitude: float
    longitude: float
    criticality_weight: float
    created_at: datetime


class LandmarkList(BaseModel):
    items: list[LandmarkRead]
    total: int

