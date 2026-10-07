import json
from unittest.mock import patch

from django.test import SimpleTestCase

from planner.services.routing import Place


class PlanViewTests(SimpleTestCase):
    def test_rejects_invalid_cycle(self):
        response = self.client.post(
            "/api/plan/",
            data=json.dumps({"current_location": "A", "pickup_location": "B", "dropoff_location": "C", "current_cycle_used": 71}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("planner.views.route_trip")
    @patch("planner.views.geocode")
    def test_returns_plan(self, geocode_mock, route_mock):
        geocode_mock.side_effect = [
            Place("A", "Chicago", 41.8, -87.6),
            Place("B", "Omaha", 41.2, -96.0),
            Place("C", "Denver", 39.7, -104.9),
        ]
        route_mock.return_value = {
            "distance_miles": 200,
            "duration_hours": 4,
            "coordinates": [[-87.6, 41.8], [-96, 41.2], [-104.9, 39.7]],
            "legs": [
                {"distance_miles": 100, "duration_hours": 2},
                {"distance_miles": 100, "duration_hours": 2},
            ],
            "instructions": [],
        }
        response = self.client.post(
            "/api/plan/",
            data=json.dumps({"current_location": "A", "pickup_location": "B", "dropoff_location": "C", "current_cycle_used": 5, "departure_at": "2026-10-07T06:00:00+00:00"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["trip"]["distance_miles"], 200)
        self.assertEqual(len(body["trip"]["logs"]), 1)

