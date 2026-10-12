from __future__ import annotations

from functools import lru_cache

from fastapi import Header
from app.core.config import get_settings
from app.integrations.complaint_events import ComplaintEventPublisher, KafkaComplaintEventPublisher, NoopComplaintEventPublisher


def get_user_id(x_user_id: str | None = Header(default=None)) -> str | None:
    return x_user_id.strip() if x_user_id else None


@lru_cache
def get_complaint_event_publisher() -> ComplaintEventPublisher:
    settings = get_settings()
    return KafkaComplaintEventPublisher(settings) if settings.kafka_enabled else NoopComplaintEventPublisher()

