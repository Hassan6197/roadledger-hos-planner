# RoadLedger 4 Minute Walkthrough

Use this outline while recording the required Loom. Keep the browser and editor side by side and speak naturally rather than reading every line.

## 0:00 to 0:30 Introduction

“RoadLedger is a Django and React trip planner for property-carrying drivers. It takes the current location, pickup, drop-off, and current 70-hour cycle usage, then returns a mapped route, a compliant duty schedule, and completed daily log sheets.”

Mention that the planner assumes a fresh 11-hour and 14-hour clock after 10 consecutive hours off duty, as the assessment does not provide the previous duty-status timeline.

## 0:30 to 1:25 Live planning flow

1. Open the hosted app.
2. Use Chicago, Illinois as the current location; Omaha, Nebraska as pickup; Denver, Colorado as drop-off; and 12 hours as current cycle used.
3. Click **Plan compliant trip**.
4. Point out the keyless map, route distance, driving time, arrival, daily resets, and cycle hours remaining.
5. Identify the colored map markers for the origin, pickup, break, sleeper-berth reset, fuel, and delivery.

## 1:25 to 2:15 Hours of Service logic

Show the duty schedule and explain:

- driving is limited to 11 hours inside a 14-hour window;
- a 30-minute non-driving period is inserted after eight cumulative driving hours;
- pickup and delivery each add one on-duty hour;
- a 10-hour sleeper-berth period resets the daily clocks;
- a 34-hour restart is inserted when the 70-hour cycle is exhausted; and
- fueling is scheduled at least every 1,000 route miles.

Switch to **Directions** and briefly show the turn-by-turn route instructions.

## 2:15 to 2:55 Daily logs

Scroll to **Daily logs**. Show that the trip creates multiple sheets when it crosses calendar days. Point out the blue duty-status line, daily mileage, duty-status totals, remarks, and cycle recap values. Mention that **Print daily logs** creates a clean one-sheet-per-page print view.

## 2:55 to 3:45 Code tour

Open these files:

1. `backend/planner/services/routing.py` - geocoding, OSRM route geometry, directions, and progress-to-coordinate conversion.
2. `backend/planner/services/scheduler.py` - HOS state machine, stop insertion, daily splitting, and recap calculations.
3. `backend/planner/views.py` - validation and the JSON API.
4. `frontend/src/App.tsx` - main planning flow and result views.
5. `frontend/src/components/MapView.tsx` and `EldLog.tsx` - route rendering and filled log sheets.

## 3:45 to 4:15 Verification and close

Show the backend and frontend test commands in the README. Mention that the production dependency audit has zero known production vulnerabilities and that the app is packaged as a single Docker service with a Render blueprint.

Close with: “The app is a planning aid rather than a certified ELD or truck-specific navigation product, so that limitation is stated clearly in the interface and README.”

