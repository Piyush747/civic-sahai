from __future__ import annotations

from datetime import datetime, timezone
from math import ceil

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ComplaintNotFoundError, ZoneNotFoundError
from app.db.models import Complaint, ComplaintImage, User, Zone
from app.integrations.complaint_events import ComplaintEventPublisher
from app.repositories.complaints import ComplaintRepository
from app.repositories.users import UserRepository
from app.schemas.citizen import CitizenComplaintCreate
from app.services.users import UserNotFoundError


class InvalidComplaintStatusError(Exception):
    pass


_CATEGORY_LABELS = {
    "ROAD_DAMAGE": ("Road damage", "RD"),
    "WASTE": ("Waste management", "WM"),
    "WASTE_MANAGEMENT": ("Waste management", "WM"),
    "STREETLIGHT": ("Streetlight", "SL"),
    "WATER_SUPPLY": ("Water supply", "WS"),
    "DRAINAGE": ("Drainage", "DR"),
    "PUBLIC_SAFETY": ("Public safety", "PS"),
    "OTHER": ("Other", "OT"),
}
_PUBLIC_STATUS = {
    "OPEN": ("SUBMITTED", "Reported"),
    "IN_PROGRESS": ("IN_PROGRESS", "In progress"),
    "RESOLVED": ("RESOLVED", "Resolved"),
    "CLOSED": ("NEEDS_ATTENTION", "Needs attention"),
}
_STORED_STATUS = {
    "ALL": None,
    "SUBMITTED": "OPEN",
    "IN_PROGRESS": "IN_PROGRESS",
    "RESOLVED": "RESOLVED",
    "NEEDS_ATTENTION": "CLOSED",
}
_DETAIL_STATUS_LABEL = {
    "SUBMITTED": "REPORTED",
    "IN_PROGRESS": "IN PROGRESS",
    "RESOLVED": "RESOLVED",
    "NEEDS_ATTENTION": "NEEDS ATTENTION",
}
_IMAGE_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
    "svg": "image/svg+xml",
}


def _iso_z(value: datetime | None) -> str:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _public_category(stored: str) -> str:
    return "WASTE_MANAGEMENT" if stored == "WASTE" else stored


def _category_label(stored: str) -> str:
    return _CATEGORY_LABELS.get(stored, ("Other", "OT"))[0]


def _category_code(stored: str) -> str:
    return _CATEGORY_LABELS.get(stored, ("Other", "OT"))[1]


def _public_status(stored: str) -> tuple[str, str]:
    return _PUBLIC_STATUS.get(stored, ("SUBMITTED", "Reported"))


def _reference(complaint: Complaint) -> str:
    digits = "".join(character for character in complaint.id if character.isdigit())
    short = (digits[-4:] if digits else complaint.id.replace("-", "")[:4]).upper().rjust(4, "0")
    created = complaint.created_at or datetime.now(timezone.utc)
    return f"CS-{created.year}-{short}"


def _title_from_description(description: str) -> str:
    line = description.strip().split("\n", 1)[0]
    return line if len(line) <= 160 else f"{line[:157]}…"


def _portal_header(initials: str | None = None) -> dict:
    header = {
        "brandName": "Civic SahAI",
        "portalLabel": "CITIZEN PORTAL",
        "navigation": [
            {"label": "My complaints", "action": "VIEW_COMPLAINTS"},
            {"label": "Help", "action": "HELP"},
        ],
    }
    if initials is not None:
        header["profileInitials"] = initials
    return header


def _greeting(name: str, now: datetime) -> str:
    hour = now.hour
    if hour < 12:
        period = "Good morning"
    elif hour < 17:
        period = "Good afternoon"
    else:
        period = "Good evening"
    first = name.strip().split()[0]
    return f"{period}, {first}"


def _content_type(image_id: str) -> str:
    extension = image_id.rsplit(".", 1)[-1].lower() if "." in image_id else ""
    return _IMAGE_TYPES.get(extension, "application/octet-stream")


def _contains(boundary: dict, longitude: float, latitude: float) -> bool:
    if boundary.get("type") != "Polygon":
        return False
    rings = boundary.get("coordinates") or []
    if not rings or not isinstance(rings[0], list):
        return False
    ring = rings[0]
    if len(ring) < 3:
        return False
    inside = False
    previous = len(ring) - 1
    for index, point in enumerate(ring):
        xi, yi = point[0], point[1]
        xj, yj = ring[previous][0], ring[previous][1]
        if ((yi > latitude) != (yj > latitude)) and (
            longitude < (xj - xi) * (latitude - yi) / ((yj - yi) or 1e-12) + xi
        ):
            inside = not inside
        previous = index
    return inside


class CitizenPortalService:
    def __init__(self, db: Session):
        self.db = db
        self.complaints = ComplaintRepository(db)

    def homepage(self, user_id: str, now: datetime | None = None) -> dict:
        user = self._user(user_id)
        complaints = self.complaints.list_for_user(user_id)
        counts = self._counts(complaints)
        return {
            "header": _portal_header(user.initials),
            "welcomeSection": {
                "greeting": _greeting(user.name, now or datetime.now().astimezone()),
                "description": "Report civic issues in your area and follow their progress.",
                "primaryAction": {
                    "label": "Report an issue",
                    "subtitle": "Takes about 2 minutes",
                    "action": "SUBMIT_COMPLAINT",
                },
            },
            "summaryCards": [
                {"key": "TOTAL", "title": "Total complaints", "count": len(complaints), "description": "All reports you submitted"},
                {"key": "IN_PROGRESS", "title": "In progress", "count": counts["IN_PROGRESS"], "description": "Teams are working on these"},
                {"key": "RESOLVED", "title": "Resolved", "count": counts["RESOLVED"], "description": "Issues marked as fixed"},
                {"key": "NEEDS_ATTENTION", "title": "Needs attention", "count": counts["NEEDS_ATTENTION"], "description": "Updates or details requested"},
            ],
            "complaintsSection": {
                "title": "Your recent complaints",
                "description": "Track each report and see what happens next.",
                "viewAllLabel": "View all complaints",
                "filters": [
                    {"key": "ALL", "label": "All complaints"},
                    {"key": "IN_PROGRESS", "label": "In progress"},
                    {"key": "RESOLVED", "label": "Resolved"},
                    {"key": "NEEDS_ATTENTION", "label": "Needs attention"},
                ],
                "tableHeaders": ["ISSUE", "LOCATION", "REPORTED", "STATUS"],
                "viewActionLabel": "View",
            },
            "complaints": [self._summary(item, include_code=True) for item in complaints[:20]],
            "informationNote": "Your reports help your local teams understand what needs attention. Similar reports may be grouped internally to coordinate repairs.",
            "footerText": "Civic SahAI · Clear reports. Better civic services.",
        }

    def complaint_form(self) -> dict:
        return {
            "header": _portal_header(),
            "introText": "Tell us what is happening. Your report helps the local team understand what needs attention.",
            "breadcrumbs": [
                {"label": "My complaints", "action": "VIEW_COMPLAINTS"},
                {"label": "Register a complaint", "action": None},
            ],
            "pageTitle": "Register a complaint",
            "pageDescription": "Share the details below. Fields marked * are required.",
            "form": {
                "sectionTitle": "Issue details",
                "fields": [
                    {
                        "name": "category",
                        "label": "Category",
                        "type": "SELECT",
                        "placeholder": "Select an issue category",
                        "required": True,
                        "options": [
                            {"value": "ROAD_DAMAGE", "label": "Road damage"},
                            {"value": "WASTE_MANAGEMENT", "label": "Waste management"},
                            {"value": "STREETLIGHT", "label": "Streetlight"},
                            {"value": "WATER_SUPPLY", "label": "Water supply"},
                            {"value": "DRAINAGE", "label": "Drainage"},
                            {"value": "PUBLIC_SAFETY", "label": "Public safety"},
                            {"value": "OTHER", "label": "Other"},
                        ],
                    },
                    {
                        "name": "description",
                        "label": "Describe the issue",
                        "type": "TEXTAREA",
                        "placeholder": "What happened? Include useful details...",
                        "required": True,
                        "minLength": 10,
                        "maxLength": 2000,
                    },
                    {
                        "name": "location.address",
                        "label": "Location / landmark",
                        "type": "TEXT",
                        "placeholder": "Street, area, nearby landmark",
                        "required": True,
                        "maxLength": 300,
                        "helperText": "Pinpoint the issue as accurately as possible.",
                    },
                    {
                        "name": "attachments",
                        "label": "Photos (optional)",
                        "type": "FILE_UPLOAD",
                        "required": False,
                        "acceptedFormats": ["image/jpeg", "image/png"],
                        "maxFiles": 5,
                    },
                ],
                "mapPreview": {"placeholder": "Map preview · Select location"},
                "privacyNote": "Avoid including sensitive personal information in photos or descriptions.",
                "submitButton": {"label": "Submit complaint", "action": "SUBMIT_COMPLAINT"},
                "cancelButton": {"label": "Cancel", "action": "CANCEL"},
            },
            "nextSteps": {
                "title": "What happens next",
                "steps": [
                    {"step": 1, "text": "We receive your report"},
                    {"step": 2, "text": "The team reviews the issue"},
                    {"step": 3, "text": "You can track progress here"},
                ],
            },
        }

    def create(self, user_id: str, data: CitizenComplaintCreate, event_publisher: ComplaintEventPublisher | None) -> dict:
        self._user(user_id)
        zone_id = self._zone_id(data.location.latitude, data.location.longitude)
        landmark = data.location.landmark.strip() if data.location.landmark else None
        complaint = Complaint(
            user_id=user_id,
            title=_title_from_description(data.description),
            description=data.description.strip(),
            category=data.category.value,
            latitude=data.location.latitude,
            longitude=data.location.longitude,
            address=data.location.address.strip(),
            landmark=landmark,
            zone_id=zone_id,
            status="OPEN",
        )
        complaint.images = [ComplaintImage(image_id=item.file_id.strip()) for item in data.attachments if item.file_id.strip()]
        complaint = self.complaints.create(complaint)
        if event_publisher is not None:
            event_publisher.publish_received(complaint)
        zone = self.db.get(Zone, complaint.zone_id)
        return {
            "complaintId": complaint.id,
            "referenceNumber": _reference(complaint),
            "category": _public_category(complaint.category),
            "description": complaint.description,
            "location": {
                "address": complaint.address,
                "landmark": complaint.landmark,
                "latitude": complaint.latitude,
                "longitude": complaint.longitude,
                "zoneId": complaint.zone_id,
                "zoneName": zone.name if zone is not None else "",
            },
            "attachments": [{"fileId": image.image_id, "status": "ATTACHED"} for image in complaint.images],
            "status": "SUBMITTED",
            "submittedAt": _iso_z(complaint.created_at),
            "message": "Your complaint has been submitted successfully.",
        }

    def complaint(self, user_id: str, complaint_id: str, file_base_url: str) -> dict:
        self._user(user_id)
        complaint = self._owned(user_id, complaint_id)
        status, _label = _public_status(complaint.status)
        return {
            "header": _portal_header(),
            "pageContent": {
                "introText": "Track the status and updates for your submitted complaint.",
                "breadcrumb": {"parentLabel": "My complaints", "currentLabel": _reference(complaint)},
                "similarComplaintsTitle": "Similar complaints",
                "similarComplaintsDescription": "These reports were grouped with your complaint because they appear to describe the same local issue. Progress is tracked together.",
                "sameIssueLabel": "SAME ISSUE",
                "privateReporterLabel": "Reporter details are private",
                "informationSection": {
                    "title": "Need to add information?",
                    "description": "Contact the civic team if the location or issue details need to be corrected.",
                    "actionLabel": "Contact civic team",
                    "action": "CONTACT_CIVIC_TEAM",
                },
            },
            "complaint": {
                "complaintId": complaint.id,
                "referenceNumber": _reference(complaint),
                "title": complaint.title,
                "category": _public_category(complaint.category),
                "categoryLabel": _category_label(complaint.category),
                "location": {"address": complaint.address, "landmark": complaint.landmark},
                "description": complaint.description,
                "status": status,
                "statusLabel": _DETAIL_STATUS_LABEL[status],
                "reportedAt": _iso_z(complaint.created_at),
                "lastUpdatedAt": _iso_z(complaint.updated_at),
                "attachments": [
                    {
                        "attachmentId": image.id,
                        "contentType": _content_type(image.image_id),
                        "url": f"{file_base_url}/api/v1/complaint-images/{image.image_id}",
                    }
                    for image in complaint.images
                ],
            },
            "progressSection": {"title": "Progress updates", "events": self._events(complaint)},
            "similarComplaints": [self._similar_summary(item) for item in self.complaints.similar(complaint)],
        }

    def list_complaints(self, user_id: str, search: str | None, status: str | None, page: int, page_size: int) -> dict:
        self._user(user_id)
        if status is not None and status not in _STORED_STATUS:
            raise InvalidComplaintStatusError(status)
        complaints = self.complaints.list_for_user(user_id)
        counts = self._counts(complaints)
        stored_status = _STORED_STATUS.get(status) if status else None
        filtered = complaints
        if stored_status is not None:
            filtered = [item for item in filtered if item.status == stored_status]
        term = (search or "").strip().lower()
        if term:
            filtered = [item for item in filtered if self._matches(item, term)]
        total = len(filtered)
        total_pages = ceil(total / page_size) if total else 0
        start = (page - 1) * page_size
        page_items = filtered[start : start + page_size]
        if total == 0:
            display = "Showing 0–0 of 0"
        else:
            display = f"Showing {start + 1}–{start + len(page_items)} of {total}"
        return {
            "header": _portal_header(),
            "pageContent": {
                "introText": "Review every report you have submitted and check its latest status.",
                "breadcrumb": {"parentLabel": "My complaints", "currentLabel": "All complaints"},
                "pageTitle": "All complaints",
                "registerButton": {"label": "Register a complaint", "action": "SUBMIT_COMPLAINT"},
                "searchPlaceholder": "Search by reference, issue, or location",
                "filterTitle": "Filter by status",
                "viewDetailsLabel": "View details",
            },
            "summary": {
                "totalCount": len(complaints),
                "statusCounts": [
                    {"status": "ALL", "label": "All", "count": len(complaints)},
                    {"status": "SUBMITTED", "label": "Reported", "count": counts["SUBMITTED"]},
                    {"status": "IN_PROGRESS", "label": "In progress", "count": counts["IN_PROGRESS"]},
                    {"status": "RESOLVED", "label": "Resolved", "count": counts["RESOLVED"]},
                    {"status": "NEEDS_ATTENTION", "label": "Needs attention", "count": counts["NEEDS_ATTENTION"]},
                ],
            },
            "complaints": [self._summary(item, include_code=False) for item in page_items],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "totalItems": total,
                "totalPages": total_pages,
                "hasPrevious": page > 1 and total_pages > 0,
                "hasNext": page < total_pages,
                "previousPage": page - 1 if page > 1 and total_pages > 0 else None,
                "nextPage": page + 1 if page < total_pages else None,
                "displayText": display,
            },
        }

    def _user(self, user_id: str) -> User:
        user = UserRepository(self.db).get(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def _owned(self, user_id: str, complaint_id: str) -> Complaint:
        complaint = self.complaints.get(complaint_id)
        if complaint is None or complaint.user_id != user_id:
            raise ComplaintNotFoundError(complaint_id)
        return complaint

    def _zone_id(self, latitude: float, longitude: float) -> str:
        zones = list(self.db.scalars(select(Zone).order_by(Zone.id)))
        if not zones:
            raise ZoneNotFoundError("none")
        for zone in zones:
            if isinstance(zone.boundary, dict) and _contains(zone.boundary, longitude, latitude):
                return zone.id
        return zones[0].id

    def _counts(self, complaints: list[Complaint]) -> dict[str, int]:
        counts = {"SUBMITTED": 0, "IN_PROGRESS": 0, "RESOLVED": 0, "NEEDS_ATTENTION": 0}
        for complaint in complaints:
            status, _label = _public_status(complaint.status)
            counts[status] += 1
        return counts

    def _summary(self, complaint: Complaint, *, include_code: bool) -> dict:
        status, label = _public_status(complaint.status)
        item = {
            "complaintId": complaint.id,
            "referenceNumber": _reference(complaint),
            "title": complaint.title,
            "category": _public_category(complaint.category),
            "categoryLabel": _category_label(complaint.category),
            "location": {"address": complaint.address},
            "reportedAt": _iso_z(complaint.created_at),
            "status": status,
            "statusLabel": label,
        }
        if include_code:
            item["categoryCode"] = _category_code(complaint.category)
        return item

    def _similar_summary(self, complaint: Complaint) -> dict:
        status, label = _public_status(complaint.status)
        return {
            "complaintId": complaint.id,
            "referenceNumber": _reference(complaint),
            "title": complaint.title,
            "category": _public_category(complaint.category),
            "location": {"address": complaint.address},
            "reportedAt": _iso_z(complaint.created_at),
            "status": status,
            "statusLabel": label,
            "reporterDetailsVisibility": "PRIVATE",
        }

    def _matches(self, complaint: Complaint, term: str) -> bool:
        zone_name = complaint.zone.name if complaint.zone is not None else ""
        haystack = " ".join(
            [
                complaint.title,
                complaint.description,
                complaint.address,
                complaint.landmark or "",
                zone_name,
                _reference(complaint),
                _category_label(complaint.category),
            ]
        ).lower()
        return term in haystack

    def _events(self, complaint: Complaint) -> list[dict]:
        status, _label = _public_status(complaint.status)
        created = _iso_z(complaint.created_at)
        updated = _iso_z(complaint.updated_at)
        steps = [
            ("evt-1", "REPORT_RECEIVED", "Report received", created, "Your complaint was submitted."),
            ("evt-2", "REVIEWED", "Reviewed by the team", created, "The issue was reviewed."),
            ("evt-3", "TEAM_ASSIGNED", "Team assigned", updated, "A civic team was assigned."),
            ("evt-4", "WORK_IN_PROGRESS", "Work in progress", updated, "The team has started work."),
        ]
        if status == "RESOLVED":
            steps.append(("evt-5", "RESOLVED", "Resolved", updated, "The issue has been marked as fixed."))
        if status == "NEEDS_ATTENTION":
            steps[3] = ("evt-4", "NEEDS_ATTENTION", "Needs attention", updated, "More information or follow-up may be needed.")
        active = {"SUBMITTED": 0, "IN_PROGRESS": 3, "RESOLVED": 4, "NEEDS_ATTENTION": 3}[status]
        events = []
        for index, (event_id, event_type, title, timestamp, description) in enumerate(steps):
            if index > active:
                break
            events.append(
                {
                    "eventId": event_id,
                    "type": event_type,
                    "title": title,
                    "timestamp": timestamp,
                    "description": description,
                    "status": "CURRENT" if index == active else "COMPLETED",
                }
            )
        return events
