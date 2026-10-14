from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Protocol

from app.core.config import Settings
from app.db.models import Complaint
from app.integrations.kafka_config import kafka_connection_options

logger = logging.getLogger(__name__)


class ComplaintEventPublisher(Protocol):
    def publish_received(self, complaint: Complaint) -> None: ...


class NoopComplaintEventPublisher:
    def publish_received(self, complaint: Complaint) -> None:
        return None


class KafkaComplaintEventPublisher:
    def __init__(self, settings: Settings):
        from kafka import KafkaProducer

        self.topic = settings.kafka_complaint_topic
        kafka_options = kafka_connection_options(settings)
        self.producer = KafkaProducer(
            **kafka_options,
            acks="all",
            retries=3,
            request_timeout_ms=10000,
            linger_ms=5,
            key_serializer=lambda value: value.encode("utf-8"),
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )

    def publish_received(self, complaint: Complaint) -> None:
        payload = {
            "event_type": "complaint.received",
            "event_version": 1,
            "complaint_id": complaint.id,
            "user_id": complaint.user_id,
            "city_id": complaint.zone.city_id,
            "zone_id": complaint.zone_id,
            "category": complaint.category,
            "title": complaint.title,
            "description": complaint.description,
            "location": {"latitude": complaint.latitude, "longitude": complaint.longitude, "address": complaint.address},
            "image_ids": [image.image_id for image in complaint.images],
            "status": complaint.status,
            "created_at": complaint.created_at.isoformat() if isinstance(complaint.created_at, datetime) else None,
        }
        try:
            # KafkaProducer.send() enqueues the record and returns immediately.
            # The producer's background sender handles broker delivery.
            future = self.producer.send(self.topic, key=complaint.id, value=payload)
            future.add_errback(lambda error: logger.error("Kafka complaint event delivery failed: %s", error))
        except Exception as exc:
            logger.error("Kafka complaint event could not be queued: %s", exc)

