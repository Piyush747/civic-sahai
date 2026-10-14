from enum import Enum


class ComplaintCategory(str, Enum):
    ROAD_DAMAGE = "ROAD_DAMAGE"
    WASTE = "WASTE"
    WASTE_MANAGEMENT = "WASTE_MANAGEMENT"
    WATER_SUPPLY = "WATER_SUPPLY"
    STREETLIGHT = "STREETLIGHT"
    DRAINAGE = "DRAINAGE"
    PUBLIC_SAFETY = "PUBLIC_SAFETY"
    OTHER = "OTHER"


class ComplaintStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

