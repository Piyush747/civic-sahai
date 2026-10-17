from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from app.db.base import Base
from app.db.models import (
    Complaint,
    Incident,
    IncidentComplaint,
    Landmark,
    Zone,
)


def constraint_names(model):
    return {constraint.name for constraint in model.__table__.constraints if constraint.name}


def test_model_tables_are_registered():
    assert {"users", "cities", "zones", "landmarks", "complaints", "complaint_images", "incidents", "incident_complaints", "incident_status_history"} <= set(Base.metadata.tables)
    assert not ({"resource_types", "zone_resources", "incident_resource_requirements", "resource_allocations", "allocation_recommendations", "teams", "incident_assignments"} & set(Base.metadata.tables))


def test_incident_enforces_city_zone_ownership():
    assert any(isinstance(constraint, ForeignKeyConstraint) and constraint.name == "fk_incidents_city_zone" for constraint in Incident.__table__.constraints)
    assert "uq_zones_city_id_id" in constraint_names(Zone)
    assert {"priority_version", "priority_metadata"} <= {column.name for column in Incident.__table__.columns}


def test_model_constraints_cover_status_coordinates_and_quantities():
    assert "ck_complaints_status" in constraint_names(Complaint)
    assert "ck_incidents_status" in constraint_names(Incident)
    assert {"ck_landmarks_latitude", "ck_landmarks_longitude", "ck_landmarks_criticality_weight"} <= constraint_names(Landmark)


def test_incident_complaint_link_is_constrained():
    assert "ck_incident_complaints_relationship_type" in constraint_names(IncidentComplaint)
