from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class CitizenCategory(str, Enum):
    ROAD_DAMAGE = "ROAD_DAMAGE"
    WASTE_MANAGEMENT = "WASTE_MANAGEMENT"
    STREETLIGHT = "STREETLIGHT"
    WATER_SUPPLY = "WATER_SUPPLY"
    DRAINAGE = "DRAINAGE"
    PUBLIC_SAFETY = "PUBLIC_SAFETY"
    OTHER = "OTHER"


class CitizenLocationIn(BaseModel):
    address: str = Field(min_length=1, max_length=300)
    landmark: str | None = Field(default=None, max_length=160)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class CitizenAttachmentIn(BaseModel):
    file_id: str = Field(min_length=1, max_length=255, alias="fileId")

    @field_validator("file_id")
    @classmethod
    def require_file_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("A photo is required")
        return cleaned


class CitizenComplaintCreate(BaseModel):
    category: CitizenCategory
    description: str = Field(min_length=10, max_length=2000)
    location: CitizenLocationIn
    attachments: list[CitizenAttachmentIn] = Field(min_length=1, max_length=5)
