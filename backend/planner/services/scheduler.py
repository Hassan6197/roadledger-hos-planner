from dataclasses import dataclass
from datetime import datetime, time, timedelta

from .routing import coordinate_at_progress


EPSILON = 1 / 120


@dataclass
class Segment:
    start: datetime
    end: datetime
    status: str
    label: str
    location: str
    miles: float = 0
    coordinate: list[float] | None = None
    kind: str = "duty"

    @property
    def duration_hours(self):
        return (self.end - self.start).total_seconds() / 3600

    def as_dict(self):
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "status": self.status,
            "label": self.label,
            "location": self.location,
            "duration_hours": round(self.duration_hours, 2),
            "miles": round(self.miles, 1),
            "coordinate": self.coordinate,
            "kind": self.kind,
        }


def _add_segment(segments, cursor, hours, status, label, location, miles=0, coordinate=None, kind="duty"):
    segment = Segment(cursor, cursor + timedelta(hours=hours), status, label, location, miles, coordinate, kind)
    segments.append(segment)
    return segment.end


def build_schedule(route, places, departure_at: datetime, current_cycle_used: float):
    segments = []
    stops = []
    cursor = departure_at
    total_distance = route["distance_miles"]
    miles_complete = 0.0
    miles_since_fuel = 0.0
    daily_drive = 0.0
    drive_since_break = 0.0
    duty_window = 0.0
    cycle_used = current_cycle_used
    initial_cycle = current_cycle_used

    def location_at(miles):
        coordinate = coordinate_at_progress(route["coordinates"], 0 if total_distance == 0 else miles / total_distance)
        return coordinate

    def rest(kind):
        nonlocal cursor, daily_drive, drive_since_break, duty_window, cycle_used
        coordinate = location_at(miles_complete)
        if kind == "restart":
            hours, label = 34.0, "34-hour cycle restart"
            cycle_used = 0.0
        else:
            hours, label = 10.0, "10-hour sleeper-berth reset"
        cursor = _add_segment(segments, cursor, hours, "sleeper", label, "Safe rest location", coordinate=coordinate, kind=kind)
        stops.append({"type": kind, "label": label, "at": segments[-1].start.isoformat(), "coordinate": coordinate})
        daily_drive = 0.0
        drive_since_break = 0.0
        duty_window = 0.0

    def add_service(label, location_name, hours, kind, coordinate):
        nonlocal cursor, duty_window, cycle_used, drive_since_break
        cursor = _add_segment(segments, cursor, hours, "on_duty", label, location_name, coordinate=coordinate, kind=kind)
        duty_window += hours
        cycle_used += hours
        if hours >= 0.5:
            drive_since_break = 0.0
        stops.append({"type": kind, "label": label, "at": segments[-1].start.isoformat(), "coordinate": coordinate})

    def drive_leg(leg, destination_name, destination_coordinate):
        nonlocal cursor, miles_complete, miles_since_fuel, daily_drive, drive_since_break, duty_window, cycle_used
        hours_remaining = leg["duration_hours"]
        miles_remaining = leg["distance_miles"]
        average_speed = miles_remaining / hours_remaining if hours_remaining else 50.0

        while hours_remaining > EPSILON:
            if cycle_used >= 70 - EPSILON:
                rest("restart")
                continue
            if daily_drive >= 11 - EPSILON or duty_window >= 14 - EPSILON:
                rest("sleeper")
                continue
            if drive_since_break >= 8 - EPSILON:
                coordinate = location_at(miles_complete)
                cursor = _add_segment(segments, cursor, 0.5, "off_duty", "30-minute rest break", "Safe parking area", coordinate=coordinate, kind="break")
                stops.append({"type": "break", "label": "30-minute rest break", "at": segments[-1].start.isoformat(), "coordinate": coordinate})
                duty_window += 0.5
                drive_since_break = 0.0
                continue
            if miles_since_fuel >= 1000 - 0.1:
                add_service("Fuel stop and inspection", "Fuel station", 0.5, "fuel", location_at(miles_complete))
                miles_since_fuel = 0.0
                continue

            hours_to_fuel = (1000 - miles_since_fuel) / average_speed
            available = min(
                hours_remaining,
                11 - daily_drive,
                8 - drive_since_break,
                14 - duty_window,
                70 - cycle_used,
                hours_to_fuel,
            )
            if available <= EPSILON:
                continue
            driven_miles = min(miles_remaining, average_speed * available)
            start_coordinate = location_at(miles_complete)
            cursor = _add_segment(
                segments,
                cursor,
                available,
                "driving",
                f"Drive toward {destination_name}",
                destination_name,
                miles=driven_miles,
                coordinate=start_coordinate,
                kind="drive",
            )
            hours_remaining -= available
            miles_remaining -= driven_miles
            miles_complete += driven_miles
            miles_since_fuel += driven_miles
            daily_drive += available
            drive_since_break += available
            duty_window += available
            cycle_used += available

        miles_complete = min(total_distance, miles_complete)
        if segments and segments[-1].kind == "drive":
            segments[-1].coordinate = destination_coordinate

    origin, pickup, dropoff = places
    stops.append({"type": "origin", "label": "Trip start", "at": cursor.isoformat(), "coordinate": [origin.lon, origin.lat]})
    drive_leg(route["legs"][0], pickup.name, [pickup.lon, pickup.lat])
    add_service("Pickup and secure load", pickup.name, 1.0, "pickup", [pickup.lon, pickup.lat])
    drive_leg(route["legs"][1], dropoff.name, [dropoff.lon, dropoff.lat])
    add_service("Unload and post-trip", dropoff.name, 1.0, "dropoff", [dropoff.lon, dropoff.lat])

    return {
        "segments": [segment.as_dict() for segment in segments],
        "stops": stops,
        "cycle": {
            "initial_used": round(initial_cycle, 1),
            "final_used": round(cycle_used, 1),
            "remaining": round(max(0, 70 - cycle_used), 1),
        },
        "elapsed_hours": round((cursor - departure_at).total_seconds() / 3600, 1),
        "arrival_at": cursor.isoformat(),
        "logs": build_daily_logs(segments, departure_at, origin.name, dropoff.name, initial_cycle),
    }


def build_daily_logs(segments, departure_at, origin_name, destination_name, initial_cycle):
    if not segments:
        return []
    first_day = departure_at.date()
    last_day = segments[-1].end.date()
    logs = []
    day = first_day
    running_cycle = initial_cycle

    while day <= last_day:
        day_start = datetime.combine(day, time.min, tzinfo=departure_at.tzinfo)
        day_end = day_start + timedelta(days=1)
        entries = []
        miles = 0.0
        on_duty = 0.0
        cursor = day_start
        cycle_before = running_cycle

        for segment in segments:
            start = max(segment.start, day_start)
            end = min(segment.end, day_end)
            if end <= start:
                continue
            if start > cursor:
                entries.append({"start_hour": (cursor - day_start).total_seconds() / 3600, "end_hour": (start - day_start).total_seconds() / 3600, "status": "off_duty", "label": "Off duty"})
            duration = (end - start).total_seconds() / 3600
            entries.append(
                {
                    "start_hour": round((start - day_start).total_seconds() / 3600, 4),
                    "end_hour": round((end - day_start).total_seconds() / 3600, 4),
                    "status": segment.status,
                    "label": segment.label,
                    "location": segment.location,
                }
            )
            fraction = duration / segment.duration_hours if segment.duration_hours else 0
            miles += segment.miles * fraction
            if segment.status in {"driving", "on_duty"}:
                on_duty += duration
                running_cycle += duration
            if segment.kind == "restart" and segment.end <= day_end and segment.end > day_start:
                running_cycle = 0.0
            cursor = end
        if cursor < day_end:
            entries.append({"start_hour": (cursor - day_start).total_seconds() / 3600, "end_hour": 24, "status": "off_duty", "label": "Off duty"})

        totals = {status: round(sum(item["end_hour"] - item["start_hour"] for item in entries if item["status"] == status), 2) for status in ("off_duty", "sleeper", "driving", "on_duty")}
        remarks = []
        for item in entries:
            if item["label"] in {"Off duty"} or item["status"] == "driving":
                continue
            hour = item["start_hour"]
            clock = (day_start + timedelta(hours=hour)).strftime("%-I:%M %p")
            remarks.append(f"{clock} - {item['label']}")
        logs.append(
            {
                "date": day.isoformat(),
                "from": origin_name if day == first_day else "En route",
                "to": destination_name if day == last_day else "En route",
                "total_miles": round(miles),
                "entries": entries,
                "totals": totals,
                "remarks": remarks[:5],
                "cycle_before": round(cycle_before, 1),
                "on_duty_today": round(on_duty, 1),
                "cycle_after": round(running_cycle, 1),
            }
        )
        day += timedelta(days=1)
    return logs
