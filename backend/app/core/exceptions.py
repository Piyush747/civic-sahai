class ComplaintNotFoundError(Exception):
    pass


class ZoneNotFoundError(Exception):
    pass


class LocationOutsideServiceAreaError(Exception):
    def __init__(self, city_name: str):
        self.city_name = city_name

