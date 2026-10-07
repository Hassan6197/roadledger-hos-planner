from datetime import datetime, timezone
from types import SimpleNamespace

from django.test import SimpleTestCase

from planner.services.scheduler import build_schedule


def place(name, lon, lat):
    return SimpleNamespace(name=name, lon=lon, lat=lat)


class SchedulerTests(SimpleTestCase):
    def setUp(self):
        self.places = [place("Chicago", -87.6, 41.8), place("Omaha", -96.0, 41.2), place("Denver", -104.9, 39.7)]
        self.departure = datetime(2026, 10, 7, 6, tzinfo=timezone.utc)

    def route(self, hours=(7.0, 7.0), miles=(470.0, 540.0)):
        return {
            "distance_miles": sum(miles),
            "duration_hours": sum(hours),
            "coordinates": [[-87.6, 41.8], [-96.0, 41.2], [-104.9, 39.7]],
            "legs": [
                {"duration_hours": hours[0], "distance_miles": miles[0]},
                {"duration_hours": hours[1], "distance_miles": miles[1]},
            ],
        }

    def test_long_trip_adds_break_fuel_and_daily_reset(self):
        result = build_schedule(self.route(), self.places, self.departure, 0)
        kinds = [segment["kind"] for segment in result["segments"]]
        self.assertIn("fuel", kinds)
        self.assertIn("sleeper", kinds)
        self.assertGreaterEqual(len(result["logs"]), 2)
        for log in result["logs"]:
            self.assertAlmostEqual(sum(log["totals"].values()), 24, places=1)

    def test_cycle_limit_triggers_34_hour_restart(self):
        result = build_schedule(self.route(hours=(2, 2), miles=(100, 100)), self.places, self.departure, 69)
        self.assertIn("restart", [segment["kind"] for segment in result["segments"]])

    def test_never_drives_more_than_eight_hours_without_break(self):
        result = build_schedule(self.route(hours=(10, 10), miles=(500, 500)), self.places, self.departure, 0)
        running = 0
        for segment in result["segments"]:
            if segment["status"] == "driving":
                running += segment["duration_hours"]
                self.assertLessEqual(running, 8.01)
            elif segment["duration_hours"] >= 0.5:
                running = 0
