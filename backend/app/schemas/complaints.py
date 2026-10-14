from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.domain.complaints import ComplaintCategory, ComplaintStatus


class Location(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str = Field(min_length=3, max_length=255)


class ComplaintCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=5000)
    category: ComplaintCategory
    location: Location
    zone_id: str = Field(min_length=1, max_length=64)
    image_ids: list[str] = Field(min_length=1, max_length=5)

    @field_validator("image_ids")
    @classmethod
    def require_photos(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("At least one photo is required")
        return cleaned


class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str
    category: ComplaintCategory
    location: Location
    zone_id: str
    status: ComplaintStatus
    priority_score: float | None
    created_at: datetime
    updated_at: datetime
    image_ids: list[str] = Field(default_factory=list)


class ComplaintList(BaseModel):
    items: list[ComplaintRead]
    skip: int
    limit: int
    total: int


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorBody

