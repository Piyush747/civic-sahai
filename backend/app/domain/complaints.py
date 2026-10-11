from enum import StrEnum


class ComplaintCategory(StrEnum):
    ROAD_DAMAGE = "ROAD_DAMAGE"
    WASTE = "WASTE"
    WATER_SUPPLY = "WATER_SUPPLY"
    STREETLIGHT = "STREETLIGHT"
    DRAINAGE = "DRAINAGE"
    OTHER = "OTHER"


class ComplaintStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

