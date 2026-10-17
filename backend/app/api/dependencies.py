from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, Header, HTTPException
from app.core.config import get_settings
from app.integrations.complaint_events import ComplaintEventPublisher, KafkaComplaintEventPublisher, NoopComplaintEventPublisher
from app.integrations.image_storage import open_image_storage
from app.db.models import City, User
from app.db.session import get_db
from app.domain.users import UserType
from sqlalchemy.orm import Session
from sqlalchemy import select


def get_user_id(x_user_id: str | None = Header(default=None)) -> str | None:
    return x_user_id.strip() if x_user_id else None


def require_user_id(x_user_id: str | None = Header(default=None)) -> str:
    if x_user_id is None or not x_user_id.strip():
        raise HTTPException(400, {"code": "USER_ID_REQUIRED", "message": "X-User-Id header is required."})
    return x_user_id.strip()


def require_city_admin(x_user_id: str | None = Header(default=None), db: Session = Depends(get_db)) -> tuple[User, City]:
    if x_user_id is None:
        raise HTTPException(400, {"code": "MISSING_USER_ID", "message": "X-User-Id header is required."})
    user_id = x_user_id.strip()
    if not user_id:
        raise HTTPException(400, {"code": "INVALID_USER_ID", "message": "X-User-Id header is invalid."})
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, {"code": "USER_NOT_FOUND", "message": "The requested user was not found."})
    if user.user_type != UserType.CITY_ADMIN.value:
        raise HTTPException(403, {"code": "FORBIDDEN", "message": "City administrator permission is required."})
    city = db.scalar(select(City).where(City.admin_user_id == user.id))
    if city is None:
        raise HTTPException(403, {"code": "FORBIDDEN", "message": "The administrator is not assigned to a city."})
    return user, city


@lru_cache
def get_image_storage():
    return open_image_storage(get_settings())


@lru_cache
def get_complaint_event_publisher() -> ComplaintEventPublisher:
    settings = get_settings()
    return KafkaComplaintEventPublisher(settings) if settings.kafka_enabled else NoopComplaintEventPublisher()

