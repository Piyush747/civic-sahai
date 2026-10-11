from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
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

