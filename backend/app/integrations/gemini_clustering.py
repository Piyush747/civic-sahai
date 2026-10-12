from __future__ import annotations

import json
from dataclasses import dataclass

from app.db.models import Complaint, Incident
from app.integrations.image_storage import ImageAsset


class GeminiClusteringError(RuntimeError):
    pass


@dataclass(frozen=True)
class ClusteringCandidate:
    incident: Incident
    algorithm_score: float
    distance_meters: float


@dataclass(frozen=True)
class ClusteringDecision:
    decision: str
    incident_id: str | None
    confidence: float
    reason_codes: list[str]
    summary: str | None


class GeminiClusteringAnalyzer:
    def __init__(self, api_key: str, model: str):
        from google import genai

        self._genai = genai
        self._model = model
        self._client = genai.Client(api_key=api_key)

    def analyze(
        self,
        complaint: Complaint,
        candidates: list[ClusteringCandidate],
        images: dict[str, list[ImageAsset]],
    ) -> ClusteringDecision:
        from google.genai import types

        prompt = self._prompt(complaint, candidates)
        parts = [types.Part.from_text(text=prompt)]
        for label, assets in images.items():
            parts.append(types.Part.from_text(text=f"Images for {label}:"))
            for asset in assets:
                parts.append(types.Part.from_bytes(data=asset.data, mime_type=asset.mime_type))

        response = self._client.models.generate_content(
            model=self._model,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        try:
            result = json.loads(response.text)
            decision = result["decision"]
            incident_id = result.get("incident_id")
            confidence = float(result["confidence"])
            if decision not in {"LINK_EXISTING", "CREATE_NEW"}:
                raise ValueError("unsupported decision")
            if not 0 <= confidence <= 1:
                raise ValueError("confidence must be between 0 and 1")
            if decision == "LINK_EXISTING" and incident_id not in {candidate.incident.id for candidate in candidates}:
                raise ValueError("Gemini selected an incident outside the candidate set")
            return ClusteringDecision(
                decision=decision,
                incident_id=incident_id,
                confidence=confidence,
                reason_codes=list(result.get("reason_codes", [])),
                summary=result.get("summary"),
            )
        except (TypeError, KeyError, ValueError, json.JSONDecodeError) as exc:
            raise GeminiClusteringError("Gemini returned an invalid clustering decision") from exc

    @staticmethod
    def _prompt(complaint: Complaint, candidates: list[ClusteringCandidate]) -> str:
        candidate_data = [
            {
                "incident_id": candidate.incident.id,
                "category": candidate.incident.category,
                "title": candidate.incident.title,
                "description": candidate.incident.description,
                "status": candidate.incident.status,
                "distance_meters": round(candidate.distance_meters, 1),
                "algorithm_score": round(candidate.algorithm_score, 3),
                "linked_complaints": [
                    {"title": link.complaint.title, "description": link.complaint.description}
                    for link in candidate.incident.complaint_links[:3]
                ],
            }
            for candidate in candidates
        ]
        return (
            "You are deciding whether a civic complaint belongs to one of the candidate incidents. "
            "Use classification, location, text, and images. Do not use age as a rejection condition. "
            "Return JSON only with decision (LINK_EXISTING or CREATE_NEW), incident_id (required only "
            "for LINK_EXISTING), confidence from 0 to 1, reason_codes array, and summary.\n\n"
            + json.dumps(
                {
                    "complaint": {
                        "id": complaint.id,
                        "category": complaint.category,
                        "title": complaint.title,
                        "description": complaint.description,
                        "latitude": complaint.latitude,
                        "longitude": complaint.longitude,
                    },
                    "candidates": candidate_data,
                }
            )
        )
