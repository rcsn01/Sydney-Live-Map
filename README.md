# Sydney Live Map (Prototype)

Interactive web app concept visualising Sydney traffic and pedestrian activity as a living, breathing pulsing map.

This prototype includes:

* Frontend: React + TypeScript + Vite + Leaflet (pulsing markers + time slider + details panel)
* Backend: FastAPI (Python) + SQLAlchemy + PostgreSQL
* REST API returning JSON payloads consumed by the frontend
* Mock seeded data (4 live-style counters + generated hourly metrics for last 24h)
* Docker Compose setup for `db`, `backend`, `frontend`

---

## High-Level Architecture

```
┌──────────┐    HTTP (JSON)    ┌────────────┐    SQL    ┌─────────────┐
│ Frontend │ <---------------- │  Backend   │ <-------> │ PostgreSQL  │
│  React   │  /api/...         │  FastAPI   │           │  (mock data)│
└──────────┘                   └────────────┘           └─────────────┘
```

Endpoints (initial set):

* `GET /api/health` – service status
* `GET /api/locations?at=ISO_TIMESTAMP` – list locations + intensity at (or latest)
* `GET /api/locations/{id}` – location base info
* `GET /api/locations/{id}/metrics?hours=24` – time series (hourly) counts

Intensity is derived from pedestrian + traffic counts (simple normalization heuristic for now).

---

## Quick Start (Docker)

Prereqs: Docker + Docker Compose.

```bash
docker compose up --build
docker compose down -v
```

Services:

* Frontend: http://localhost:5173
* Backend (API docs): http://localhost:8000/docs
* Postgres: port 5433 (inside: 5432)
Visit http://localhost:8000/api/health and http://localhost:8000/api/locations to verify API still fine.

First startup auto-seeds mock data.

---

## Importing traffic CSVs

If you have raw traffic CSVs (for example City of Sydney / NSW traffic extracts) with columns like:

```
the_geom	station_id	road_name	suburb	cardinal_direction_name	classification_type	year	period	traffic_count	wgs84_latitude	wgs84_longitude
```

Use the included transformer script to convert them into the simple CSV formats accepted by the backend importer.

1. Transform the raw file into `locations.csv` and `metrics.csv`:

```powershell
python tools\TrafficVolumeViewer_Transform.py C:\path\to\raw_traffic.tsv
```

The transformer will write two files next to the input file (or in the same folder):

- `locations.csv` with headers: `name,latitude,longitude,type`
- `metrics.csv` with headers: `timestamp,pedestrian_count,traffic_count,location_name`

Notes about the mapping the transformer performs:
- `name` is formed as `station_id - road_name` to keep a stable, searchable identifier.
- `latitude` / `longitude` come from `wgs84_latitude` / `wgs84_longitude`.
- `type` comes from `classification_type` and is normalized to `all_vehicles`, `light_vehicles`, or `heavy_vehicles`.
- `timestamp` is created from the `year` field (first day of the year at UTC midnight). If `year` is missing or invalid the transformer uses the current UTC time.
- `pedestrian_count` is set to `0` because the source file contains only vehicle counts; change this if you have pedestrian counts.

2. Import locations into the database (creates or updates locations by name):

```powershell
python -m backend\app\import_csv.py --mode locations --file locations.csv --update
```

3. Import metrics (match locations by `name` created in step 1):

```powershell
python backend\app\import_csv.py --mode metrics --file metrics.csv --by name
```

Aggregation guidance:
- The sample raw CSV often includes one row per vehicle classification (ALL / LIGHT / HEAVY) for a station/year. If you want a single metric per station/year, aggregate `traffic_count` across classification rows for the same `station_id` and `year` before importing. The transformer writes one metric row per input row; you can modify it to sum values if you prefer aggregated import.

Schema note:
- The current `Location` model doesn't store the original `station_id` separately. The transformer includes `station_id` in the `name` so you can locate rows later by name. If you'd like a dedicated `external_id` column in the DB, I can add that and update the importer.


## Local Dev (Without Docker)

### Backend

1. Create & activate a virtual environment (Python 3.11+ recommended)
2. Install deps:
	```bash
	python -m venv .venv
	.\.venv\Scripts\activate (windows)
	source .venv/bin/activate (mac)
	python -m pip install --upgrade pip
	pip install -r backend/requirements.txt
	```
3. Start a local Postgres (or use Docker):
	```bash
	docker run --name sydney-map-db -e POSTGRES_PASSWORD=dev -e POSTGRES_USER=dev -e POSTGRES_DB=sydmap -p 5433:5432 -d postgres:16
	```
4. Export env vars (optional – defaults match compose file):
	```bash
	export DATABASE_URL=postgresql+psycopg://dev:dev@localhost:5433/sydmap
	```
5. Run API:
	```bash
	uvicorn app.main:app --reload --port 8000 --app-dir backend/app
	```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
backend/
	app/
		main.py            # FastAPI app and startup events
		database.py        # Engine, Session, Base
		models.py          # SQLAlchemy models
		schemas.py         # Pydantic schemas
		crud.py            # Data access helpers
		deps.py            # Dependency injection (DB session)
		seed.py            # Mock data generation
	requirements.txt
frontend/
	src/
		main.tsx
		App.tsx
		components/
			MapView.tsx
			LocationDetails.tsx
		api.ts
		types.ts
		styles.css
	index.html
	package.json
docker-compose.yml
```

---

## Mock Data Logic

Four seed locations approximating Sydney CBD pedestrian/traffic counters. For each: last 24h of hourly metrics. On startup if DB empty, metrics are procedurally generated with mild randomness and daily pattern curve.

---

## Future Enhancements (Not Yet Implemented)

* Real ingestion from City of Sydney & NSW Traffic APIs
* Websocket / Server-Sent Events for near real-time updates
* Caching layer & rate limiting
* Historical replay scrub with prefetch
* Visualization improvements (clusters, heatmaps, charts)
* Alerting & anomaly detection

---

## API Examples

List current intensities:

```bash
curl http://localhost:8000/api/locations
```

Metrics for a location:

```bash
curl http://localhost:8000/api/locations/1/metrics?hours=12
```

---

## Frontend Overview

* Leaflet map centered on Sydney
* Pulsing circle markers – pulse speed inversely proportional to computed intensity interval
* Sidebar with details + simple time slider controlling the snapshot time (queries backend with `?at=`)

---

## Environment Variables

Backend (defaults shown):

* `DATABASE_URL=postgresql+psycopg://dev:dev@db:5432/sydmap`
* `API_PREFIX=/api`
* `SEED_ON_START=1`

Frontend:

* `VITE_API_BASE=http://localhost:8000/api`

---

## License

Prototype – add a license of your choice.

---

## Contributing

PRs and issues welcome. Please keep scope small & focused.

---

## Status

MVP scaffolding with mock data – ready for iterative expansion.

# Sydney-Live-Map