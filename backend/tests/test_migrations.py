from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.core.config import get_settings
from app.db import models  # noqa: F401
from app.db.base import Base

BACKEND = Path(__file__).resolve().parents[1]


def test_upgrade_head_matches_models(tmp_path, monkeypatch):
    database_path = tmp_path / "schema.db"
    monkeypatch.chdir(BACKEND)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    get_settings.cache_clear()
    config = Config(str(BACKEND / "alembic.ini"))

    try:
        command.upgrade(config, "head")
        engine = create_engine(f"sqlite:///{database_path}")
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            assert compare_metadata(context, Base.metadata) == []
        constraints = inspect(engine).get_unique_constraints("incident_complaints")
        assert {"uq_incident_complaints_complaint_id"} <= {item["name"] for item in constraints}

        command.downgrade(config, "base")
        assert inspect(engine).get_table_names() == ["alembic_version"]
    finally:
        get_settings.cache_clear()
