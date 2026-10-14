from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql+psycopg://civic_sahai:civic_sahai@localhost:5432/civic_sahai"
    cors_allowed_origins: list[str] = ["http://localhost:5173"]
    gcp_project_id: str | None = None
    gcp_region: str | None = None
    ai_enabled: bool = False
    kafka_enabled: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_security_protocol: str = "PLAINTEXT"
    kafka_sasl_mechanism: str = "SCRAM-SHA-256"
    kafka_sasl_username: str | None = None
    kafka_sasl_password: str | None = None
    kafka_ssl_cafile: str | None = None
    kafka_ssl_certfile: str | None = None
    kafka_ssl_keyfile: str | None = None
    kafka_ssl_insecure: bool = False
    kafka_complaint_topic: str = "civic-sahai.complaint-received"
    kafka_consumer_group: str = "civic-sahai.incident-clustering"
    kafka_dead_letter_topic: str = "civic-sahai.complaint-clustering-dlq"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    clustering_top_k: int = 5
    clustering_min_candidate_score: float = 0.45
    clustering_max_distance_meters: float = 1000.0
    image_storage_provider: str = "noop"
    image_storage_base_url: str | None = None
    filebase_endpoint_url: str = "https://s3.filebase.io"
    filebase_access_key_id: str | None = None
    filebase_secret_access_key: str | None = None
    filebase_region: str = "auto"
    filebase_signature_version: str = "v4"
    filebase_bucket: str = "civic-sahai-complaints"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        return [item.strip() for item in value.split(",") if item.strip()] if isinstance(value, str) else value


@lru_cache
def get_settings() -> Settings:
    return Settings()

