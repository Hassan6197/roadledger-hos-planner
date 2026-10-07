import json
from datetime import datetime, timedelta, timezone

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .services.routing import RoutingError, geocode, route_trip
from .services.scheduler import build_schedule


@require_GET
def health(_request):
    return JsonResponse({"status": "ok"})


def _parse_departure(value):
    if value:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    rounded = now.replace(second=0, microsecond=0)
    return rounded + timedelta(minutes=(15 - rounded.minute % 15) % 15)


@csrf_exempt
@require_POST
def plan_trip(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Request body must be valid JSON."}, status=400)

    required = ["current_location", "pickup_location", "dropoff_location", "current_cycle_used"]
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        return JsonResponse({"error": f"Missing required field: {missing[0].replace('_', ' ')}."}, status=400)
    try:
        cycle_used = float(payload["current_cycle_used"])
    except (TypeError, ValueError):
        return JsonResponse({"error": "Current cycle used must be a number from 0 to 70."}, status=400)
    if not 0 <= cycle_used <= 70:
        return JsonResponse({"error": "Current cycle used must be between 0 and 70 hours."}, status=400)

    try:
        departure_at = _parse_departure(payload.get("departure_at"))
        places = [geocode(str(payload[field]).strip()) for field in required[:3]]
        route = route_trip(places)
        schedule = build_schedule(route, places, departure_at, cycle_used)
    except (RoutingError, ValueError) as exc:
        return JsonResponse({"error": str(exc)}, status=422)

    return JsonResponse(
        {
            "trip": {
                "places": [{"query": place.query, "name": place.name, "lat": place.lat, "lon": place.lon} for place in places],
                "distance_miles": round(route["distance_miles"]),
                "drive_hours": round(route["duration_hours"], 1),
                "coordinates": route["coordinates"],
                "instructions": route["instructions"],
                "departure_at": departure_at.isoformat(),
                **schedule,
            },
            "assumptions": [
                "Property-carrying driver using the 70-hour/8-day cycle",
                "Fresh 11-hour and 14-hour clocks after 10 consecutive hours off duty",
                "One hour each for pickup and drop-off",
                "Fuel at least once every 1,000 route miles",
                "No adverse-driving-condition exception",
            ],
            "attribution": "Map data © OpenStreetMap contributors; routing by OSRM.",
        }
    )

