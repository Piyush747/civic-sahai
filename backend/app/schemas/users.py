from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.domain.users import UserType


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    user_type: UserType = UserType.CITIZEN


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    user_type: UserType | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    initials: str
    user_type: UserType
    email: EmailStr
    created_at: datetime


class UserList(BaseModel):
    items: list[UserRead]
    total: int

