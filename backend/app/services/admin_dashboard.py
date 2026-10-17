from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import case, distinct, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import City, Incident, ResourceAllocation, Zone, ZoneResource
from app.schemas.admin_dashboard import (AssignmentQueue, AssignmentQueueItem, CityOverviewResponse, DashboardSummary,
    IncidentTrend, IncidentTypeSummary, PolygonGeometry, ResponseHealth, ZoneOverviewData, ZoneOverviewMeta,
    ZoneOverviewResponse, ZoneOverviewZone, ZonePressure)


class AdminDashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.tz_name = getattr(self.settings, "city_timezone", "Asia/Kolkata")
        self.tz = ZoneInfo(self.tz_name)

    def overview(self, city: City, period: str | None, from_date: date | None, to_date: date | None) -> CityOverviewResponse:
        start, end, selected_period = self._resolve_dates(period, from_date, to_date)
        start_dt = datetime.combine(start, time.min, self.tz).astimezone(timezone.utc)
        end_dt = datetime.combine(end + timedelta(days=1), time.min, self.tz).astimezone(timezone.utc)
        incidents = list(self.db.scalars(select(Incident).where(Incident.city_id == city.id)))
        open_states = {"OPEN", "IN_PROGRESS"}
        current_open = [item for item in incidents if item.status == "OPEN"]
        current_progress = [item for item in incidents if item.status == "IN_PROGRESS"]
        resolved = [item for item in incidents if item.status in {"RESOLVED", "CLOSED"} and item.updated_at and start_dt <= self._aware(item.updated_at) < end_dt]
        waiting = [item for item in incidents if item.status in open_states and self._waiting_too_long(item)]
        zones = list(self.db.scalars(select(Zone).where(Zone.city_id == city.id).order_by(Zone.name)))
        pressure = [self._zone_pressure(zone, incidents) for zone in zones]
        trends = [self._trend(day, incidents) for day in self._dates(start, end)]
        return CityOverviewResponse(
            summary=DashboardSummary(open_incidents=len(current_open), in_progress_incidents=len(current_progress), resolved_incidents=len(resolved), waiting_too_long_incidents=len(waiting)),
            zone_pressure=pressure,
            incident_trends=trends,
            period=selected_period,
            from_date=start,
            to_date=end,
            timezone=self.tz_name,
            data_as_of=datetime.now(timezone.utc),
        )

    def zone_overview(self, city: City, zone: Zone, period: str | None, from_date: date | None, to_date: date | None) -> ZoneOverviewResponse:
        start, end, selected_period = self._resolve_dates(period, from_date, to_date)
        start_dt = datetime.combine(start, time.min, self.tz).astimezone(timezone.utc)
        end_dt = datetime.combine(end + timedelta(days=1), time.min, self.tz).astimezone(timezone.utc)
        incidents = list(self.db.scalars(select(Incident).where(Incident.city_id == city.id, Incident.zone_id == zone.id)))
        open_incidents = [item for item in incidents if item.status == "OPEN"]
        in_progress = [item for item in incidents if item.status == "IN_PROGRESS"]
        resolved = [item for item in incidents if item.status in {"RESOLVED", "CLOSED"} and item.updated_at and start_dt <= self._aware(item.updated_at) < end_dt]
        waiting = [item for item in incidents if item.status in {"OPEN", "IN_PROGRESS"} and self._waiting_too_long(item)]
        pressure = self._zone_pressure(zone, incidents)
        type_counts: dict[str, int] = {}
        for item in incidents:
            created = self._aware(item.created_at)
            if start_dt <= created < end_dt:
                type_counts[item.category] = type_counts.get(item.category, 0) + 1
        incident_types = [IncidentTypeSummary(incident_type_id=key, name=self._category_name(key), incident_count=count) for key, count in sorted(type_counts.items(), key=lambda pair: (-pair[1], self._category_name(pair[0]), pair[0]))[:5]]
        allocations = list(self.db.scalars(select(ResourceAllocation).where(ResourceAllocation.incident_id.in_([item.id for item in incidents])))) if incidents else []
        active_assignment_ids = {item.incident_id for item in allocations if item.status == "COMMITTED"}
        queue = [item for item in incidents if item.status in {"OPEN", "IN_PROGRESS"} and item.id not in active_assignment_ids]
        queue.sort(key=lambda item: (not self._waiting_too_long(item), -(item.priority_score or 0), self._aware(item.created_at), item.id))
        queue_items = [AssignmentQueueItem(incident_id=item.id, incident_type_id=item.category, incident_type=self._category_name(item.category), priority=self._priority_name(item.priority_score), created_at=self._aware(item.created_at), waiting_too_long=self._waiting_too_long(item)) for item in queue[:10]]
        return ZoneOverviewResponse(
            data=ZoneOverviewData(
                zone=ZoneOverviewZone(id=zone.id, name=zone.name, city_id=zone.city_id, pressure_level=pressure.pressure_level),
                summary=DashboardSummary(open_incidents=len(open_incidents), in_progress_incidents=len(in_progress), resolved_incidents=len(resolved), waiting_too_long_incidents=len(waiting)),
                incident_types=incident_types,
                incident_trends=[self._trend(day, incidents) for day in self._dates(start, end)],
                assignment_queue=AssignmentQueue(total_count=len(queue), items=queue_items),
                response_health=ResponseHealth(available_teams=int(pressure.available_teams), deployed_teams=int(pressure.deployed_teams), total_teams=int(pressure.total_teams), pressure_level=pressure.pressure_level),
            ),
            meta=ZoneOverviewMeta(period=selected_period, from_date=start, to_date=end, timezone=self.tz_name, data_as_of=datetime.now(timezone.utc)),
        )

    @staticmethod
    def _category_name(category: str) -> str:
        return {"ROAD_DAMAGE": "Road Damage", "WASTE": "Waste Management", "WASTE_MANAGEMENT": "Waste Management", "STREETLIGHT": "Streetlight", "WATER_SUPPLY": "Water Supply", "DRAINAGE": "Drainage", "PUBLIC_SAFETY": "Public Safety", "OTHER": "Other"}.get(category, category.replace("_", " ").title())

    @staticmethod
    def _priority_name(score: float | None) -> str | None:
        if score is None:
            return None
        return "critical" if score >= 80 else "high" if score >= 55 else "normal"

    def _resolve_dates(self, period: str | None, from_date: date | None, to_date: date | None) -> tuple[date, date, str | None]:
        if period and (from_date or to_date):
            raise HTTPException(422, {"code": "CONFLICTING_DATE_FILTERS", "message": "period cannot be combined with custom dates."})
        if bool(from_date) != bool(to_date):
            raise HTTPException(422, {"code": "INCOMPLETE_DATE_RANGE", "message": "Both from_date and to_date are required."})
        today = datetime.now(self.tz).date()
        if from_date and to_date:
            if from_date > to_date:
                raise HTTPException(422, {"code": "INVALID_DATE_RANGE", "message": "from_date must be earlier than or equal to to_date."})
            maximum = getattr(self.settings, "admin_dashboard_max_custom_days", 90)
            if (to_date - from_date).days + 1 > maximum:
                raise HTTPException(422, {"code": "DATE_RANGE_TOO_LARGE", "message": "The requested date range is too large."})
            return from_date, to_date, None
        days = {None: 15, "7d": 7, "15d": 15, "30d": 30, "90d": 90}.get(period)
        if days is None:
            raise HTTPException(422, {"code": "INVALID_PERIOD", "message": "period must be one of 7d, 15d, 30d, or 90d."})
        return today - timedelta(days=days - 1), today, period or "15d"

    def _zone_pressure(self, zone: Zone, incidents: list[Incident]) -> ZonePressure:
        resources = list(self.db.scalars(select(ZoneResource).where(ZoneResource.zone_id == zone.id)))
        total = sum(float(item.initial_capacity) for item in resources)
        available = sum(float(item.available_capacity) for item in resources)
        deployed = max(total - available, 0)
        demand = sum(1 for item in incidents if item.zone_id == zone.id and item.status in {"OPEN", "IN_PROGRESS"})
        ratio = demand / total if total else 0
        thresholds = self.settings
        if total == 0 and demand > 0:
            level = "overloaded"
        elif total == 0:
            level = "balanced"
        elif ratio >= thresholds.admin_dashboard_pressure_overloaded_ratio:
            level = "overloaded"
        elif ratio >= thresholds.admin_dashboard_pressure_under_pressure_ratio:
            level = "under_pressure"
        elif ratio <= thresholds.admin_dashboard_pressure_spare_ratio:
            level = "spare_capacity"
        else:
            level = "balanced"
        boundary = None
        if isinstance(zone.boundary, dict) and zone.boundary.get("type") == "Polygon":
            try:
                boundary = PolygonGeometry.model_validate(zone.boundary)
            except ValueError:
                boundary = None
        return ZonePressure(zone_id=zone.id, zone_name=zone.name, open_incidents=sum(1 for item in incidents if item.zone_id == zone.id and item.status == "OPEN"), available_teams=available, deployed_teams=deployed, total_teams=total, pressure_level=level, boundary=boundary)

    def _waiting_too_long(self, incident: Incident) -> bool:
        created = self._aware(incident.created_at)
        return (datetime.now(timezone.utc) - created).total_seconds() > self.settings.admin_dashboard_default_sla_hours * 3600

    def _trend(self, day: date, incidents: list[Incident]) -> IncidentTrend:
        reported = sum(1 for item in incidents if self._local_date(item.created_at) == day)
        resolved = sum(1 for item in incidents if item.status in {"RESOLVED", "CLOSED"} and self._local_date(item.updated_at) == day)
        return IncidentTrend(date=day, reported=reported, resolved=resolved)

    def _local_date(self, value: datetime | None) -> date | None:
        return self._aware(value).astimezone(self.tz).date() if value else None

    @staticmethod
    def _aware(value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

    @staticmethod
    def _dates(start: date, end: date):
        return (start + timedelta(days=offset) for offset in range((end - start).days + 1))
