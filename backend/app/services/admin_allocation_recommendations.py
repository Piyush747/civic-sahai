from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import AllocationRecommendation, Complaint, Incident, IncidentComplaint, Zone
from app.schemas.admin_allocation_recommendations import (
    AllocationRecommendationData, AllocationRecommendationResponse, HistoricalPattern,
    RecommendationHeader, RecommendationIncident, RecommendationIncidentType,
    RecommendationPriority, RecommendationSla, RecommendationStrategy, RecommendationZone,
    RationaleItem, ResidentLocalityImpact, TradeoffItem, Tradeoffs,
)
from app.services.admin_dashboard import AdminDashboardService


class AdminAllocationRecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.dashboard = AdminDashboardService(db)

    def get(self, recommendation_id: str, city_id: str) -> AllocationRecommendationResponse | None:
        recommendation = self.db.scalar(
            select(AllocationRecommendation).join(AllocationRecommendation.incident)
            .where(AllocationRecommendation.id == recommendation_id, Incident.city_id == city_id)
            .options(
                selectinload(AllocationRecommendation.incident).selectinload(Incident.complaint_links).selectinload(IncidentComplaint.complaint).selectinload(Complaint.images),
                selectinload(AllocationRecommendation.source_zone), selectinload(AllocationRecommendation.resource_type),
            )
        )
        if recommendation is None:
            return None
        incident = recommendation.incident
        destination = self.db.scalar(select(Zone).where(Zone.id == incident.zone_id, Zone.city_id == city_id))
        if destination is None:
            return None
        complaints = {link.complaint.id: link.complaint for link in incident.complaint_links}
        source, resource = recommendation.source_zone, recommendation.resource_type
        tradeoffs, impact, history = recommendation.trade_offs or {}, recommendation.resident_locality_impact or {}, recommendation.historical_pattern or {}
        return AllocationRecommendationResponse(
            data=AllocationRecommendationData(
                recommendation=RecommendationHeader(id=recommendation.id, reference_number=recommendation.reference_number, status=recommendation.status.lower(), generated_at=recommendation.generated_at, strategy=RecommendationStrategy(type=recommendation.strategy_type, summary=recommendation.strategy_summary, source_zone=RecommendationZone(id=source.id, name=source.name) if source else None, destination_zone=RecommendationZone(id=destination.id, name=destination.name), resource_type=resource.name if resource else None, quantity=recommendation.quantity, quantity_unit=resource.unit if resource else None), priority_score=RecommendationPriority(value=recommendation.priority_score, scale_max=100 if recommendation.priority_score is not None else None, label=self.dashboard._priority_name(recommendation.priority_score))),
                incident=RecommendationIncident(id=incident.id, reference_number=None, title=incident.title, description=incident.description, incident_type=RecommendationIncidentType(id=incident.category, name=self.dashboard._category_name(incident.category)), status=incident.status.lower(), priority=self.dashboard._priority_name(incident.priority_score), zone=RecommendationZone(id=destination.id, name=destination.name), linked_complaint_count=len(complaints), waiting_duration_seconds=None, sla=RecommendationSla(status=incident.sla_status, response_due_at=incident.response_due_at)),
                rationale=[RationaleItem(**item) for item in recommendation.rationale or []],
                trade_offs=Tradeoffs(benefits=[TradeoffItem(**item) for item in tradeoffs.get("benefits", [])], costs_and_risks=[TradeoffItem(**item) for item in tradeoffs.get("costs_and_risks", [])], comparison_summary=tradeoffs.get("comparison_summary")),
                resident_locality_impact=ResidentLocalityImpact(**impact) if impact else ResidentLocalityImpact(radius_meters=None, estimated_resident_count=None, nearby_landmark_count=None, access_routes_at_risk_count=None, landmarks=[], access_routes=[], availability="unavailable", estimated_at=None),
                historical_pattern=HistoricalPattern(**history) if history else HistoricalPattern(location_label=None, window_start=None, window_end=None, prior_occurrence_count=None, outcome_counts={}, occurrences=[], availability="unavailable"),
            ), meta={"data_as_of": datetime.now(timezone.utc)},
        )
