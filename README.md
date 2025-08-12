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
```

Services:

* Frontend: http://localhost:5173
* Backend (API docs): http://localhost:8000/docs
* Postgres: port 5433 (inside: 5432)

First startup auto-seeds mock data.

---

## Local Dev (Without Docker)

### Backend

1. Create & activate a virtual environment (Python 3.11+ recommended)
2. Install deps:
	```bash
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