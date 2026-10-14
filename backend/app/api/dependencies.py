from __future__ import annotations

from functools import lru_cache

from fastapi import Header, HTTPException
from app.core.config import get_settings
from app.integrations.complaint_events import ComplaintEventPublisher, KafkaComplaintEventPublisher, NoopComplaintEventPublisher
from app.integrations.image_storage import open_image_storage


def get_user_id(x_user_id: str | None = Header(default=None)) -> str | None:
    return x_user_id.strip() if x_user_id else None


def require_user_id(x_user_id: str | None = Header(default=None)) -> str:
    if x_user_id is None or not x_user_id.strip():
        raise HTTPException(400, {"code": "USER_ID_REQUIRED", "message": "X-User-Id header is required."})
    return x_user_id.strip()


@lru_cache
def get_image_storage():
    return open_image_storage(get_settings())


@lru_cache
def get_complaint_event_publisher() -> ComplaintEventPublisher:
    settings = get_settings()
    return KafkaComplaintEventPublisher(settings) if settings.kafka_enabled else NoopComplaintEventPublisher()

