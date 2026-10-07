import json
import math
from dataclasses import dataclass
from urllib.parse import urlencode
from urllib.request import Request, urlopen


USER_AGENT = "RoadLedgerAssessment/1.0 (trip-planning-demo)"


class RoutingError(Exception):
    pass


@dataclass(frozen=True)
class Place:
    query: str
    name: str
    lat: float
    lon: float


def _get_json(url: str):
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RoutingError("The map service could not be reached. Please try again in a moment.") from exc


def geocode(query: str) -> Place:
    params = urlencode({"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "us"})
    results = _get_json(f"https://nominatim.openstreetmap.org/search?{params}")
    if not results:
        raise RoutingError(f'No location matched "{query}". Add a city, state, or ZIP code and try again.')
    result = results[0]
    return Place(query=query, name=result.get("display_name", query), lat=float(result["lat"]), lon=float(result["lon"]))


def _clean_instruction(step):
    maneuver = step.get("maneuver", {})
    kind = maneuver.get("type", "continue").replace("_", " ")
    modifier = maneuver.get("modifier")
    road = step.get("name") or "the roadway"
    if kind == "depart":
        text = f"Depart on {road}"
    elif kind == "arrive":
        text = "Arrive at the stop"
    elif kind == "roundabout":
        exit_number = maneuver.get("exit")
        text = f"At the roundabout, take exit {exit_number} onto {road}" if exit_number else f"Enter the roundabout toward {road}"
    else:
        action = kind.capitalize()
        text = f"{action}{f' {modifier}' if modifier else ''} onto {road}"
    return {
        "instruction": text,
        "distance_miles": round(step.get("distance", 0) / 1609.344, 1),
        "duration_minutes": round(step.get("duration", 0) / 60),
    }


def route_trip(places: list[Place]):
    coordinates = ";".join(f"{place.lon},{place.lat}" for place in places)
    params = urlencode({"overview": "full", "geometries": "geojson", "steps": "true", "annotations": "false"})
    data = _get_json(f"https://router.project-osrm.org/route/v1/driving/{coordinates}?{params}")
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError("A drivable route could not be calculated for those locations.")
    route = data["routes"][0]
    legs = []
    instructions = []
    for index, leg in enumerate(route["legs"]):
        leg_steps = [_clean_instruction(step) for step in leg.get("steps", []) if step.get("distance", 0) > 15]
        legs.append(
            {
                "distance_miles": leg["distance"] / 1609.344,
                "duration_hours": leg["duration"] / 3600,
                "instructions": leg_steps,
            }
        )
        for step in leg_steps:
            instructions.append({**step, "leg": index})
    return {
        "distance_miles": route["distance"] / 1609.344,
        "duration_hours": route["duration"] / 3600,
        "coordinates": route["geometry"]["coordinates"],
        "legs": legs,
        "instructions": instructions,
    }


def haversine_miles(first, second):
    lon1, lat1 = first
    lon2, lat2 = second
    radius = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def coordinate_at_progress(coordinates, progress):
    if not coordinates:
        return [0, 0]
    if progress <= 0:
        return coordinates[0]
    if progress >= 1:
        return coordinates[-1]
    lengths = [haversine_miles(coordinates[i - 1], coordinates[i]) for i in range(1, len(coordinates))]
    target = sum(lengths) * progress
    travelled = 0.0
    for index, length in enumerate(lengths, start=1):
        if travelled + length >= target:
            ratio = 0 if length == 0 else (target - travelled) / length
            first, second = coordinates[index - 1], coordinates[index]
            return [first[0] + (second[0] - first[0]) * ratio, first[1] + (second[1] - first[1]) * ratio]
        travelled += length
    return coordinates[-1]

