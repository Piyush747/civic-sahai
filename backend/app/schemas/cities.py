from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CityCreate(BaseModel):
    admin_user_id: str = Field(min_length=1, max_length=36)
    name: str = Field(min_length=1, max_length=120)


class CityUpdate(BaseModel):
    admin_user_id: str | None = Field(default=None, min_length=1, max_length=36)
    name: str | None = Field(default=None, min_length=1, max_length=120)


class CityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    admin_user_id: str
    created_at: datetime


class CityList(BaseModel):
    items: list[CityRead]
    total: int

