# Smart Greenhouse

A full-stack greenhouse monitoring and automation system built with FastAPI, React, and PostgreSQL.

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20 LTS
- npm

## First-time Setup

```bash
# 1. Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 2. Start PostgreSQL
docker compose up -d

# 3. Backend setup
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
python seed.py  # optional: idempotent demo location, devices, and reading

# 4. Frontend setup
cd ../frontend
npm install
```

## Daily Start (Three Terminals)

**Terminal 1 — Database**
```bash
docker compose up -d
```

**Terminal 2 — Backend API**
```bash
cd backend
.\.venv\Scripts\Activate.ps1
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3 — Frontend**
```bash
cd frontend
npm run dev
```

## URLs

| Service | URL |
|---------|-----|
| Frontend UI | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Scalar API Reference | http://localhost:8000/scalar |
| OpenAPI Schema | http://localhost:8000/openapi.json |
| WebSocket feed | ws://localhost:8000/api/ws |

## API and realtime

- All REST resources used by the UI live under `/api/...` (health stays at `/health`).
- `WS /api/ws` streams the same domain events the Phase 11 bus publishes.
  Messages are JSON envelopes: `{ "type": "alert.created", "payload": { ... } }`.
  Supported types: `reading.created`, `actuator.state_changed`, `alert.created`.
- The dashboard header shows the socket state (`connected` / `connecting` / `down`).
  `EventFeed` applies pushed alerts immediately and keeps a 30-second GET poll as
  a fallback; the socket is read-only, alerts are still persisted by the Observer
  subscriber.

Smoke test the feed from the browser console:

```js
const ws = new WebSocket("ws://localhost:8000/api/ws");
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

Trigger a reading in the dashboard (or `POST /api/sensors/{id}/read`) and the
console should print `reading.created` before the UI refreshes.

See [docs/schema.md](docs/schema.md) for the migration chain, indexing, FK
`ON DELETE` policies, and the idempotent seed.

## Dashboard polish (Phase 13, optional)

- `GET /api/sensors/{id}/readings?from=<iso>&to=<iso>` returns readings
  oldest-first for a chart window; without `from`/`to` it stays newest-first
  for the history panel.
- The dashboard adds a historical moisture trend chart, a 12-reading sparkline
  on each sensor card, an active/all alert filter with severity sorting,
  loading skeletons, a route-level error boundary, and reconnect backoff
  capped at 15 seconds.
- The existing `sensor_readings (device_id, recorded_at DESC)` index covers
  chart range queries, so Phase 13 adds no migration.
- Deferred in this phase: editing an existing location configuration, and
  resolving alerts (this build has no `PATCH /api/alerts/{id}`).

## Quality Checks

```bash
# Backend tests & lint
cd backend
.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
python -m ruff check src tests alembic

# Frontend type-check & build
cd ../frontend
npm run build
```

## Documentation

See [docs/phases/README.md](docs/phases/README.md) for the phase-by-phase development guide and [docs/schema.md](docs/schema.md) for the schema and realtime notes.

## Environment Variables

All `.env` files are gitignored. Use `.env.example` as templates.