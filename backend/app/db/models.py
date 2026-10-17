from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    initials: Mapped[str] = mapped_column(String(8), nullable=False)
    user_type: Mapped[str] = mapped_column(String(32), nullable=False, default="CITIZEN", index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="user")


class City(Base):
    __tablename__ = "cities"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    admin_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    zones: Mapped[list["Zone"]] = relationship(back_populates="city")
    administrator: Mapped[User] = relationship(foreign_keys=[admin_user_id])


class Zone(Base):
    __tablename__ = "zones"
    __table_args__ = (UniqueConstraint("city_id", "id", name="uq_zones_city_id_id"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    city_id: Mapped[str] = mapped_column(ForeignKey("cities.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    population: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    boundary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    complaints: Mapped[list["Complaint"]] = relationship(back_populates="zone")
    city: Mapped[City] = relationship(back_populates="zones")
    landmarks: Mapped[list["Landmark"]] = relationship(back_populates="zone")
    resources: Mapped[list["ZoneResource"]] = relationship(back_populates="zone")


class Landmark(Base):
    __tablename__ = "landmarks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    landmark_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    criticality_weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    zone: Mapped[Zone] = relationship(back_populates="landmarks")
    __table_args__ = (
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="ck_landmarks_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="ck_landmarks_longitude"),
        CheckConstraint("criticality_weight >= 0", name="ck_landmarks_criticality_weight"),
    )


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        CheckConstraint("status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')", name="ck_complaints_status"),
        Index("ix_complaints_user_created_at", "user_id", "created_at"),
        Index("ix_complaints_zone_status", "zone_id", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    landmark: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN", index=True)
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    zone: Mapped[Zone] = relationship(back_populates="complaints")
    user: Mapped[User] = relationship(back_populates="complaints")
    images: Mapped[list["ComplaintImage"]] = relationship(back_populates="complaint", cascade="all, delete-orphan")
    incident_link: Mapped[Optional["IncidentComplaint"]] = relationship(
        back_populates="complaint",
        uselist=False,
    )


class ComplaintImage(Base):
    __tablename__ = "complaint_images"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    image_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    complaint: Mapped[Complaint] = relationship(back_populates="images")


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        ForeignKeyConstraint(("city_id", "zone_id"), ("zones.city_id", "zones.id"), name="fk_incidents_city_zone"),
        CheckConstraint("status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED')", name="ck_incidents_status"),
        Index("ix_incidents_city_status", "city_id", "status"),
        Index("ix_incidents_priority", "priority_score"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    city_id: Mapped[str] = mapped_column(String(36), nullable=False)
    zone_id: Mapped[str] = mapped_column(String(64), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    locality: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN", index=True)
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    priority_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    priority_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    response_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    sla_breached_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recurrence_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    complaint_links: Mapped[list["IncidentComplaint"]] = relationship(back_populates="incident", cascade="all, delete-orphan")
    resource_requirements: Mapped[list["IncidentResourceRequirement"]] = relationship(back_populates="incident")
    allocations: Mapped[list["ResourceAllocation"]] = relationship(back_populates="incident")
    assignments: Mapped[list["IncidentAssignment"]] = relationship(back_populates="incident", cascade="all, delete-orphan")
    status_history: Mapped[list["IncidentStatusHistory"]] = relationship(back_populates="incident", cascade="all, delete-orphan")
    recommendations: Mapped[list["AllocationRecommendation"]] = relationship(back_populates="incident", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    city_id: Mapped[str] = mapped_column(ForeignKey("cities.id"), nullable=False, index=True)
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    availability_status: Mapped[str] = mapped_column(String(32), nullable=False, default="AVAILABLE")
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IncidentAssignment(Base):
    __tablename__ = "incident_assignments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), nullable=False, index=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    unassigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), nullable=True)
    recommendation_id: Mapped[Optional[str]] = mapped_column(ForeignKey("allocation_recommendations.id"), nullable=True)
    incident: Mapped[Incident] = relationship(back_populates="assignments")
    team: Mapped[Team] = relationship()


class IncidentStatusHistory(Base):
    __tablename__ = "incident_status_history"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    incident: Mapped[Incident] = relationship(back_populates="status_history")


class IncidentComplaint(Base):
    __tablename__ = "incident_complaints"
    __table_args__ = (
        UniqueConstraint("complaint_id", name="uq_incident_complaints_complaint_id"),
        CheckConstraint("relationship_type IN ('PRIMARY', 'DUPLICATE')", name="ck_incident_complaints_relationship_type"),
        CheckConstraint("match_score IS NULL OR (match_score >= 0 AND match_score <= 1)", name="ck_incident_complaints_match_score"),
        Index("ix_incident_complaints_complaint_id", "complaint_id"),
    )
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.id", ondelete="CASCADE"), primary_key=True)
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False, default="PRIMARY")
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    matched_by: Mapped[str] = mapped_column(String(32), nullable=False, default="SYSTEM")
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    incident: Mapped[Incident] = relationship(back_populates="complaint_links")
    complaint: Mapped[Complaint] = relationship(back_populates="incident_link")


class ResourceType(Base):
    __tablename__ = "resource_types"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    zone_resources: Mapped[list["ZoneResource"]] = relationship(back_populates="resource_type")
    requirements: Mapped[list["IncidentResourceRequirement"]] = relationship(back_populates="resource_type")
    allocations: Mapped[list["ResourceAllocation"]] = relationship(back_populates="resource_type")


class ZoneResource(Base):
    __tablename__ = "zone_resources"
    __table_args__ = (
        UniqueConstraint("zone_id", "resource_type_id", name="uq_zone_resources_zone_type"),
        CheckConstraint("initial_capacity >= 0", name="ck_zone_resources_initial_capacity"),
        CheckConstraint("available_capacity >= 0 AND available_capacity <= initial_capacity", name="ck_zone_resources_available_capacity"),
        Index("ix_zone_resources_resource_type_id", "resource_type_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"), nullable=False)
    resource_type_id: Mapped[str] = mapped_column(ForeignKey("resource_types.id"), nullable=False)
    initial_capacity: Mapped[float] = mapped_column(Float, nullable=False)
    available_capacity: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    zone: Mapped[Zone] = relationship(back_populates="resources")
    resource_type: Mapped[ResourceType] = relationship(back_populates="zone_resources")


class IncidentResourceRequirement(Base):
    __tablename__ = "incident_resource_requirements"
    __table_args__ = (
        UniqueConstraint("incident_id", "resource_type_id", name="uq_incident_requirements_incident_type"),
        CheckConstraint("required_quantity >= 0", name="ck_incident_requirements_required_quantity"),
        CheckConstraint("allocated_quantity >= 0 AND allocated_quantity <= required_quantity", name="ck_incident_requirements_allocated_quantity"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type_id: Mapped[str] = mapped_column(ForeignKey("resource_types.id"), nullable=False, index=True)
    required_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    allocated_quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    incident: Mapped[Incident] = relationship(back_populates="resource_requirements")
    resource_type: Mapped[ResourceType] = relationship(back_populates="requirements")


class ResourceAllocation(Base):
    __tablename__ = "resource_allocations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_resource_allocations_quantity"),
        CheckConstraint("status IN ('PROPOSED', 'COMMITTED', 'RELEASED', 'CANCELLED')", name="ck_resource_allocations_status"),
        Index("ix_resource_allocations_incident_status", "incident_id", "status"),
        Index("ix_resource_allocations_source_zone_id", "source_zone_id"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), nullable=False)
    source_zone_id: Mapped[str] = mapped_column(ForeignKey("zones.id"), nullable=False)
    resource_type_id: Mapped[str] = mapped_column(ForeignKey("resource_types.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PROPOSED")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    incident: Mapped[Incident] = relationship(back_populates="allocations")
    source_zone: Mapped[Zone] = relationship()
    resource_type: Mapped[ResourceType] = relationship(back_populates="allocations")


class AllocationRecommendation(Base):
    __tablename__ = "allocation_recommendations"
    __table_args__ = (
        CheckConstraint("status IN ('AWAITING_DECISION', 'APPROVED', 'REJECTED', 'EXPIRED')", name="ck_allocation_recommendations_status"),
        Index("ix_allocation_recommendations_incident_status", "incident_id", "status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    reference_number: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, unique=True)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="AWAITING_DECISION")
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    strategy_type: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_zone_id: Mapped[Optional[str]] = mapped_column(ForeignKey("zones.id"), nullable=True)
    resource_type_id: Mapped[Optional[str]] = mapped_column(ForeignKey("resource_types.id"), nullable=True)
    quantity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rationale: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    trade_offs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    resident_locality_impact: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    historical_pattern: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    incident: Mapped[Incident] = relationship(back_populates="recommendations")
    source_zone: Mapped[Optional[Zone]] = relationship(foreign_keys=[source_zone_id])
    resource_type: Mapped[Optional[ResourceType]] = relationship()

