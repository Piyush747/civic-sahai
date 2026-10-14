from __future__ import annotations

import json
import logging

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.integrations.gemini_clustering import GeminiClusteringAnalyzer
from app.integrations.image_storage import FilebaseImageStorage, HttpImageStorage, NoopImageStorage
from app.services.clustering import IncidentCandidateSelector, IncidentClusteringService

logger = logging.getLogger(__name__)


class ConsumerAnalyzer:
    def __init__(self, settings):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is required for the clustering consumer")
        self.gemini = GeminiClusteringAnalyzer(settings.gemini_api_key, settings.gemini_model)
        self.settings = settings

    def select_candidates(self, complaint):
        return IncidentCandidateSelector(
            db=self._db,
            top_k=self.settings.clustering_top_k,
            minimum_score=self.settings.clustering_min_candidate_score,
            maximum_distance_meters=self.settings.clustering_max_distance_meters,
        ).find(complaint)

    def decide(self, complaint, candidates, images):
        return self.gemini.analyze(complaint, candidates, images)

    def bind_db(self, db):
        self._db = db
        return self


def run() -> None:
    from kafka import KafkaConsumer, TopicPartition
    from kafka.structs import OffsetAndMetadata

    settings = get_settings()
    if not settings.kafka_enabled:
        raise RuntimeError("KAFKA_ENABLED must be true to run the clustering consumer")
    analyzer = ConsumerAnalyzer(settings)
    if settings.image_storage_provider.lower() == "filebase":
        if not settings.filebase_access_key_id or not settings.filebase_secret_access_key:
            raise RuntimeError("FILEBASE_ACCESS_KEY_ID and FILEBASE_SECRET_ACCESS_KEY are required")
        image_storage = FilebaseImageStorage(
            endpoint_url=settings.filebase_endpoint_url,
            access_key_id=settings.filebase_access_key_id,
            secret_access_key=settings.filebase_secret_access_key,
            region=settings.filebase_region,
            signature_version=settings.filebase_signature_version,
            bucket=settings.filebase_bucket,
        )
    elif settings.image_storage_base_url:
        image_storage = HttpImageStorage(settings.image_storage_base_url)
    else:
        image_storage = NoopImageStorage()
    consumer = KafkaConsumer(
        settings.kafka_complaint_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group,
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        auto_offset_reset="earliest",
    )
    logger.info("Listening for complaint events on %s", settings.kafka_complaint_topic)
    for message in consumer:
        event = message.value
        complaint_id = event.get("complaint_id") if isinstance(event, dict) else None
        partition = TopicPartition(message.topic, message.partition)
        next_offset = {partition: OffsetAndMetadata(message.offset + 1, None)}
        if not complaint_id:
            logger.error("Invalid complaint event at offset %s; acknowledging malformed message", message.offset)
            consumer.commit(next_offset)
            continue
        db = SessionLocal()
        try:
            IncidentClusteringService(db).process(complaint_id, analyzer.bind_db(db), image_storage)
            consumer.commit(next_offset)
            logger.info("Clustered complaint %s", complaint_id)
        except Exception:
            db.rollback()
            consumer.seek(partition, message.offset)
            logger.exception("Complaint clustering failed for %s; Kafka message will be retried", complaint_id)
        finally:
            db.close()


if __name__ == "__main__":
    run()
