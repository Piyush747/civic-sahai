from __future__ import annotations

import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

USER_AGENT = "CivicSahAI/1.0 (complaint location picker)"
_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
_NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
_ADDRESS_KINDS = (
    "amenity",
    "shop",
    "tourism",
    "leisure",
    "road",
    "neighbourhood",
    "suburb",
)
_TAG_KINDS = ("amenity", "shop", "tourism", "leisure", "railway")


def search_places(query: str, latitude: float | None = None, longitude: float | None = None) -> list[dict]:
    """Places whose names match what the citizen typed, near the map pin when provided."""
    text = " ".join(query.split())
    if len(text) < 2:
        return []
    fields: dict[str, str | int] = {
        "q": text,
        "format": "jsonv2",
        "limit": 15,
        "addressdetails": 1,
    }
    ref_lat, ref_lon = latitude, longitude
    if ref_lat is not None and ref_lon is not None:
        delta = 0.22
        fields["viewbox"] = (
            f"{ref_lon - delta},{ref_lat + delta},{ref_lon + delta},{ref_lat - delta}"
        )
        fields["bounded"] = 1
    params = urllib.parse.urlencode(fields)
    request = urllib.request.Request(
        f"{_SEARCH_URL}?{params}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            payload = json.loads(response.read().decode())
    except (OSError, ValueError) as exc:
        raise OSError("location search failed") from exc
    places = places_from_search(payload)
    if ref_lat is not None and ref_lon is not None:
        places.sort(
            key=lambda item: _rough_distance(ref_lat, ref_lon, item["latitude"], item["longitude"])
        )
    return places[:8]


def places_from_search(payload: object) -> list[dict]:
    if not isinstance(payload, list):
        return []
    places = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        label = str(item.get("display_name") or "").strip()
        name = label.split(",")[0].strip()
        if not name or label.casefold() in seen:
            continue
        try:
            latitude = float(item["lat"])
            longitude = float(item["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        seen.add(label.casefold())
        places.append(
            {"name": name[:160], "label": label[:300], "latitude": latitude, "longitude": longitude}
        )
        if len(places) == 8:
            break
    return places


def search_nearby_places(latitude: float, longitude: float) -> list[dict]:
    """Named places around a pin. Saved landmarks are loaded separately."""
    pool = ThreadPoolExecutor(max_workers=2)
    try:
        overpass = pool.submit(_fetch_overpass, latitude, longitude)
        nominatim = pool.submit(_fetch_nominatim, latitude, longitude)
        places = _result(overpass, 2.5)
        if places:
            return places
        return _result(nominatim, 4)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def places_from_overpass(payload: dict, latitude: float, longitude: float) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    places = []
    seen: set[str] = set()
    for element in payload.get("elements") or []:
        tags = element.get("tags") or {}
        name = str(tags.get("name") or "").strip()
        lat = element.get("lat")
        lon = element.get("lon")
        if not name or lat is None or lon is None or name.casefold() in seen:
            continue
        kind = next((str(tags[key]) for key in _TAG_KINDS if tags.get(key)), "place")
        seen.add(name.casefold())
        places.append(
            {
                "name": name[:160],
                "kind": kind.replace("_", " ")[:64],
                "latitude": float(lat),
                "longitude": float(lon),
            }
        )
    places.sort(key=lambda item: _rough_distance(latitude, longitude, item["latitude"], item["longitude"]))
    return places[:6]


def places_from_nominatim(payload: dict) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    address = payload.get("address") or {}
    try:
        latitude = float(payload["lat"])
        longitude = float(payload["lon"])
    except (KeyError, TypeError, ValueError):
        return []
    places = []
    seen: set[str] = set()
    for kind in _ADDRESS_KINDS:
        name = str(address.get(kind) or "").strip()
        if not name or name.casefold() in seen:
            continue
        seen.add(name.casefold())
        places.append({"name": name[:160], "kind": kind, "latitude": latitude, "longitude": longitude})
    return places[:6]


def _result(future, timeout: float) -> list[dict]:
    try:
        places = future.result(timeout=timeout)
    except (OSError, ValueError, TimeoutError):
        return []
    return places if isinstance(places, list) else []


def _fetch_overpass(latitude: float, longitude: float) -> list[dict]:
    lat = float(latitude)
    lon = float(longitude)
    query = (
        f"[out:json][timeout:8];("
        f'node(around:700,{lat:.6f},{lon:.6f})["name"]["amenity"];'
        f'node(around:700,{lat:.6f},{lon:.6f})["name"]["shop"];'
        f'node(around:700,{lat:.6f},{lon:.6f})["name"]["tourism"];'
        f'node(around:700,{lat:.6f},{lon:.6f})["name"]["leisure"];'
        f'node(around:700,{lat:.6f},{lon:.6f})["name"]["railway"];'
        ");out body 12;"
    )
    body = urllib.parse.urlencode({"data": query}).encode()
    request = urllib.request.Request(
        _OVERPASS_URL,
        data=body,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=2.5) as response:
        payload = json.loads(response.read().decode())
    return places_from_overpass(payload, lat, lon)


def _fetch_nominatim(latitude: float, longitude: float) -> list[dict]:
    query = urllib.parse.urlencode(
        {"format": "jsonv2", "lat": latitude, "lon": longitude, "zoom": 18, "addressdetails": 1}
    )
    request = urllib.request.Request(
        f"{_NOMINATIM_URL}?{query}",
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=4) as response:
        payload = json.loads(response.read().decode())
    return places_from_nominatim(payload)


def _rough_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return (lat1 - lat2) ** 2 + (lon1 - lon2) ** 2
