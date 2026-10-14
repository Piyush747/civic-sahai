from enum import Enum


class UserType(str, Enum):
    CITIZEN = "CITIZEN"
    CITY_ADMIN = "CITY_ADMIN"

