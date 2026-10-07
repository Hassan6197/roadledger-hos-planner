# RoadLedger

RoadLedger is a full-stack trip planner for property-carrying drivers. It converts an origin, pickup, drop-off, and current 70-hour cycle usage into:

- a mapped route with pickup, fuel, break, sleeper-berth, and delivery stops;
- an Hours of Service schedule based on the 11-hour, 14-hour, 30-minute break, and 70-hour/8-day limits; and
- one completed driver's daily log for every calendar day touched by the trip.

The app uses React and MapLibre in the browser, CARTO/OpenStreetMap for map tiles, OpenStreetMap Nominatim for geocoding, and the public OSRM service for route geometry and directions. No map API key is required.

## Assumptions

- The driver is operating a property-carrying CMV under the 70-hour/8-day rule.
- The trip begins after at least 10 consecutive hours off duty, so the 11-hour and 14-hour clocks are fresh.
- `Current cycle used` is the driver's on-duty total for the current rolling eight-day period. A 34-hour restart is scheduled if the remaining cycle is exhausted.
- Pickup and drop-off each take one hour on duty.
- Fuel is scheduled at least every 1,000 route miles. A 30-minute fuel stop also satisfies the 30-minute break rule.
- Public OSRM provides car-profile routing, so the result is a planning aid and not a substitute for commercial truck navigation or a certified ELD.

## Local development

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite serves the interface at `http://localhost:5173` and proxies `/api` calls to Django on port 8000.

## Tests and production build

```bash
source .venv/bin/activate
python backend/manage.py test planner
cd frontend
npm test -- --run
npm run build
```

After `npm run build`, Django serves the compiled app and API together. Run it locally with:

```bash
gunicorn --chdir backend roadledger.wsgi:application
```

## Docker

```bash
docker build -t roadledger .
docker run --rm -p 8000:8000 \
  -e DJANGO_SECRET_KEY=local-only \
  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
  roadledger
```

Open `http://localhost:8000`.

## API

`POST /api/plan/`

```json
{
  "current_location": "Chicago, IL",
  "pickup_location": "Omaha, NE",
  "dropoff_location": "Denver, CO",
  "current_cycle_used": 12,
  "departure_at": "2026-10-07T06:00"
}
```

`departure_at` is optional. When omitted, the backend starts at the next quarter hour.

## Deployment

The included `Dockerfile` and `render.yaml` deploy the frontend and backend as one web service. Set a strong `DJANGO_SECRET_KEY`; `PORT` and the external hostname are supplied by the host.

## Attribution

Map data © OpenStreetMap contributors, served by CARTO. Routing is provided by the OSRM demo service. Geocoding is provided by Nominatim. The daily log format and HOS rules are based on the supplied FMCSA guide and log sheet.
