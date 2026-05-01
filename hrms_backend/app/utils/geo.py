"""Geo-fencing helpers."""
from __future__ import annotations

import math
from dataclasses import dataclass

from app.config import settings

EARTH_RADIUS_M = 6_371_000


def haversine_distance_m(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """Great-circle distance in meters between two lat/lng pairs."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


@dataclass
class GeoFenceCheck:
    inside: bool
    distance_m: int
    office_lat: float
    office_lng: float
    radius_m: int


def check_office_geofence(
    lat: float,
    lng: float,
    *,
    office_lat: float | None = None,
    office_lng: float | None = None,
    radius_m: int | None = None,
) -> GeoFenceCheck:
    olat = office_lat if office_lat is not None else settings.OFFICE_LAT
    olng = office_lng if office_lng is not None else settings.OFFICE_LNG
    rad = radius_m if radius_m is not None else settings.OFFICE_RADIUS_M
    distance = haversine_distance_m(lat, lng, olat, olng)
    return GeoFenceCheck(
        inside=distance <= rad,
        distance_m=int(round(distance)),
        office_lat=olat,
        office_lng=olng,
        radius_m=rad,
    )
