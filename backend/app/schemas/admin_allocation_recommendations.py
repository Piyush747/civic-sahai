from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RecommendationZone(BaseModel):
    id: str
    name: str


class RecommendationIncidentType(BaseModel):
    id: str
    name: str


class RecommendationPriority(BaseModel):
    value: float | None
    scale_max: int | None
    label: str | None


class RecommendationStrategy(BaseModel):
    type: str
    summary: str | None
    source_zone: RecommendationZone | None
    destination_zone: RecommendationZone | None
    resource_type: str | None
    quantity: float | None
    quantity_unit: str | None


class RecommendationHeader(BaseModel):
    id: str
    reference_number: str | None
    status: str
    generated_at: datetime | None
    strategy: RecommendationStrategy
    priority_score: RecommendationPriority


class RecommendationSla(BaseModel):
    status: str | None
    response_due_at: datetime | None


class RecommendationIncident(BaseModel):
    id: str
    reference_number: str | None
    title: str
    description: str | None
    incident_type: RecommendationIncidentType
    status: str
    priority: str | None
    zone: RecommendationZone
    linked_complaint_count: int = Field(ge=0)
    waiting_duration_seconds: int | None = Field(default=None, ge=0)
    sla: RecommendationSla


class RationaleItem(BaseModel):
    type: str
    label: str
    explanation: str | None
    value: float | str | None
    unit: str | None
    availability: Literal["available", "unavailable"]


class TradeoffItem(BaseModel):
    description: str
    value: float | str | None
    unit: str | None
    availability: Literal["available", "unavailable"]


class Tradeoffs(BaseModel):
    benefits: list[TradeoffItem]
    costs_and_risks: list[TradeoffItem]
    comparison_summary: str | None


class ResidentLocalityImpact(BaseModel):
    radius_meters: float | None
    estimated_resident_count: int | None
    nearby_landmark_count: int | None
    access_routes_at_risk_count: int | None
    landmarks: list[dict]
    access_routes: list[dict]
    availability: Literal["available", "unavailable"]
    estimated_at: datetime | None


class HistoricalPattern(BaseModel):
    location_label: str | None
    window_start: datetime | None
    window_end: datetime | None
    prior_occurrence_count: int | None
    outcome_counts: dict[str, int]
    occurrences: list[dict]
    availability: Literal["available", "unavailable"]


class AllocationRecommendationData(BaseModel):
    recommendation: RecommendationHeader
    incident: RecommendationIncident
    rationale: list[RationaleItem]
    trade_offs: Tradeoffs
    resident_locality_impact: ResidentLocalityImpact
    historical_pattern: HistoricalPattern


class AllocationRecommendationResponse(BaseModel):
    data: AllocationRecommendationData
    meta: dict[str, datetime]
