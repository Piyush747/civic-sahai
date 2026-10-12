from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from app.db.base import Base
from app.db.models import (
    Complaint,
    Incident,
    IncidentComplaint,
    IncidentResourceRequirement,
    Landmark,
    ResourceAllocation,
    ResourceType,
    Zone,
    ZoneResource,
)


def constraint_names(model):
    return {constraint.name for constraint in model.__table__.constraints if constraint.name}


def test_model_tables_are_registered():
    assert {"users", "cities", "zones", "landmarks", "complaints", "complaint_images", "incidents", "incident_complaints", "resource_types", "zone_resources", "incident_resource_requirements", "resource_allocations"} <= set(Base.metadata.tables)


def test_incident_enforces_city_zone_ownership():
    assert any(isinstance(constraint, ForeignKeyConstraint) and constraint.name == "fk_incidents_city_zone" for constraint in Incident.__table__.constraints)
    assert "uq_zones_city_id_id" in constraint_names(Zone)
    assert {"priority_version", "priority_metadata"} <= {column.name for column in Incident.__table__.columns}


def test_model_constraints_cover_status_coordinates_and_quantities():
    assert "ck_complaints_status" in constraint_names(Complaint)
    assert "ck_incidents_status" in constraint_names(Incident)
    assert {"ck_landmarks_latitude", "ck_landmarks_longitude", "ck_landmarks_criticality_weight"} <= constraint_names(Landmark)
    assert {"ck_zone_resources_initial_capacity", "ck_zone_resources_available_capacity"} <= constraint_names(ZoneResource)
    assert {"ck_incident_requirements_required_quantity", "ck_incident_requirements_allocated_quantity"} <= constraint_names(IncidentResourceRequirement)
    assert {"ck_resource_allocations_quantity", "ck_resource_allocations_status"} <= constraint_names(ResourceAllocation)


def test_uniqueness_constraints_prevent_duplicate_resource_assignments():
    assert "uq_zone_resources_zone_type" in constraint_names(ZoneResource)
    assert "uq_incident_requirements_incident_type" in constraint_names(IncidentResourceRequirement)
    assert "ck_incident_complaints_relationship_type" in constraint_names(IncidentComplaint)
