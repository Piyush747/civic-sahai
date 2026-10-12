from __future__ import annotations

import math
import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Complaint, Incident, IncidentComplaint
from app.integrations.gemini_clustering import (
    ClusteringCandidate,
    ClusteringDecision,
)

ACTIVE_STATUSES = ("OPEN", "IN_PROGRESS")


def haversine_meters(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    radius = 6_371_000
    lat_a, lat_b = math.radians(latitude_a), math.radians(latitude_b)
    delta_lat = math.radians(latitude_b - latitude_a)
    delta_lon = math.radians(longitude_b - longitude_a)
    value = math.sin(delta_lat / 2) ** 2 + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def text_similarity(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"[a-z0-9]+", left.lower()))
    right_tokens = set(re.findall(r"[a-z0-9]+", right.lower()))
    token_score = len(left_tokens & right_tokens) / max(len(left_tokens | right_tokens), 1)
    sequence_score = SequenceMatcher(None, left.lower(), right.lower()).ratio()
    return 0.6 * token_score + 0.4 * sequence_score


@dataclass(frozen=True)
class CandidateSearch:
    candidates: list[ClusteringCandidate]


class IncidentCandidateSelector:
    def __init__(self, db: Session, top_k: int, minimum_score: float, maximum_distance_meters: float):
        self.db = db
        self.top_k = top_k
        self.minimum_score = minimum_score
        self.maximum_distance_meters = maximum_distance_meters

    def find(self, complaint: Complaint) -> CandidateSearch:
        incidents = self.db.scalars(
            select(Incident)
            .options(
                selectinload(Incident.complaint_links)
                .selectinload(IncidentComplaint.complaint)
                .selectinload(Complaint.images)
            )
            .where(
                Incident.city_id == complaint.zone.city_id,
                Incident.zone_id == complaint.zone_id,
                Incident.category == complaint.category,
                Incident.status.in_(ACTIVE_STATUSES),
            )
        ).all()
        ranked: list[ClusteringCandidate] = []
        for incident in incidents:
            complaint_locations = [
                link.complaint
                for link in incident.complaint_links
                if link.complaint is not None
            ]
            if not complaint_locations:
                continue
            distance = min(
                haversine_meters(complaint.latitude, complaint.longitude, item.latitude, item.longitude)
                for item in complaint_locations
            )
            if distance > self.maximum_distance_meters:
                continue
            location_score = max(0.0, 1.0 - distance / self.maximum_distance_meters)
            best_text_score = max(
                text_similarity(
                    f"{complaint.title} {complaint.description}",
                    f"{item.title} {item.description}",
                )
                for item in complaint_locations
            )
            score = 0.7 * location_score + 0.3 * best_text_score
            if score >= self.minimum_score:
                ranked.append(ClusteringCandidate(incident, score, distance))
        ranked.sort(key=lambda item: item.algorithm_score, reverse=True)
        return CandidateSearch(ranked[: self.top_k])


class IncidentClusteringService:
    def __init__(self, db: Session):
        self.db = db

    def process(self, complaint_id: str, analyzer, image_storage) -> Incident:
        complaint = self.db.scalar(
            select(Complaint)
            .options(selectinload(Complaint.zone), selectinload(Complaint.images), selectinload(Complaint.incident_link))
            .where(Complaint.id == complaint_id)
        )
        if complaint is None:
            raise ValueError(f"Complaint {complaint_id} was not found")
        if complaint.incident_link:
            return complaint.incident_link.incident

        search = analyzer.select_candidates(complaint)
        candidates = search.candidates
        if not candidates:
            incident = self._create_incident(complaint)
        else:
            images = self._download_images(complaint, candidates, image_storage)
            decision: ClusteringDecision = analyzer.decide(complaint, candidates, images)
            incident = self._apply_decision(complaint, candidates, decision)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def _create_incident(self, complaint: Complaint) -> Incident:
        incident = Incident(
            city_id=complaint.zone.city_id,
            zone_id=complaint.zone_id,
            category=complaint.category,
            title=complaint.title,
            description=complaint.description,
            status="OPEN",
        )
        incident.complaint_links.append(
            IncidentComplaint(
                complaint=complaint,
                relationship_type="PRIMARY",
                match_score=1.0,
                matched_by="ALGORITHM",
            )
        )
        self.db.add(incident)
        return incident

    def _apply_decision(self, complaint: Complaint, candidates: list[ClusteringCandidate], decision: ClusteringDecision) -> Incident:
        if decision.decision == "CREATE_NEW":
            return self._create_incident(complaint)
        selected = next(candidate for candidate in candidates if candidate.incident.id == decision.incident_id)
        selected.incident.complaint_links.append(
            IncidentComplaint(
                complaint=complaint,
                relationship_type="DUPLICATE",
                match_score=decision.confidence,
                matched_by="GEMINI",
            )
        )
        complaint.status = selected.incident.status
        return selected.incident

    @staticmethod
    def _download_images(complaint: Complaint, candidates: list[ClusteringCandidate], image_storage) -> dict:
        image_ids = [image.image_id for image in complaint.images]
        images = {"new_complaint": [asset for image_id in image_ids if (asset := image_storage.download(image_id))]}
        for candidate in candidates:
            assets = []
            for link in candidate.incident.complaint_links[:3]:
                for image in link.complaint.images[:3]:
                    asset = image_storage.download(image.image_id)
                    if asset:
                        assets.append(asset)
            images[f"incident_{candidate.incident.id}"] = assets
        return images
