# Phase 1 — Skeleton (Requirements)

This is the **assignment**. Implement from these requirements. If you get stuck or want to check your design, use the [guided check](guided-check.md) (tooling snippets and expected shapes — not a complete solution).

After you implement, answer the [questions](./questions.md).

## Purpose

Establish a runnable **three-tier** project: Python backend, PostgreSQL with **migration tooling**, and a React + TypeScript shell. When you finish this phase, Phase 2 can add the `devices` table and sensor API without restructuring the repo.

This phase does **not** implement a design pattern.

## Scope and naming rules

- Product context is a **smart greenhouse**; keep that language in titles, README, and UI copy.
- Stack for this course: **FastAPI + SQLAlchemy + Alembic** (backend), **Scalar** at `/scalar` for API docs, **Vite + React + TypeScript + Tailwind CSS v4** (frontend).
- Use **Tailwind utility classes** for all UI from this phase onward. Do not add per-component CSS files unless you have a strong reason.
- No business tables yet (`devices`, `locations`, and so on). Alembic exists only to prove migrations run against PostgreSQL.

## Outcome required at end of phase

- PostgreSQL runs via Docker Compose and is reachable from the backend.
- FastAPI serves `GET /health` that reports API and database status.
- Scalar API reference is available at `/scalar`; built-in Swagger `/docs` is disabled.
- Alembic is initialized with a baseline revision that creates no business tables.
- React dashboard loads with a health badge and placeholder sections for later phases.
- Root README documents how to start the stack.

---

## Prerequisites

Before starting, all of the following must be true:

| Tool | Minimum version | Verify |
|------|-------------------|--------|
| Python | 3.11+ | `python --version` |
| Node.js | 20 LTS | `node --version` |
| Docker Desktop | current | `docker --version` |
| Git | any | `git --version` |

Optional: `uv` or `pip`, VS Code, Postman/curl.

If any required tool is missing, install it first; this phase assumes a working toolchain.

---

## Required architecture for this phase

Implement the phase with clean layer separation, even though most folders are empty:

- **Domain layer**
  - Package exists (`backend/src/domain/`).
  - No business entities yet.

- **Application layer**
  - Package exists (`backend/src/application/`).
  - No use cases yet.

- **Infrastructure layer**
  - Owns settings (environment), database engine/session, and connectivity check.
  - Must not put HTTP routing in this layer.

- **API layer**
  - FastAPI app entry and health route.
  - CORS configured for the Vite origin.
  - Scalar mounted at `GET /scalar`.

- **Frontend**
  - Layout, routing, health badge, dashboard placeholders.
  - API client isolated in a services module (not scattered fetch calls in pages).

---

## Suggested file locations

Paths are relative to **`yourpath\project\`** (replace with your clone path).

```text
yourpath\project\
├── README.md
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/env.py
│   ├── alembic/versions/001_baseline.py
│   └── src/
│       ├── main.py
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       │   ├── settings.py
│       │   └── db.py
│       └── interfaces/api/health.py
└── frontend/src/
    ├── main.tsx
    ├── index.css
    ├── App.tsx
    ├── services/api.ts
    ├── components/AppLayout.tsx
    ├── components/HealthStatus.tsx
    └── pages/DashboardPage.tsx
```

## Type hints

No business entities in this phase. Contracts to match:

| Name | Fields / types |
|------|----------------|
| Settings | `database_url: str`, `api_host: str`, `api_port: int`, `cors_origins: str` |
| `GET /health` JSON | `status: str` (`ok` or `degraded`), `db: str` (`ok` or `fail`) |
| Frontend `HealthResponse` | `{ status: string; db: "ok" \| "fail" }` |
| `DATABASE_URL` | `postgresql+psycopg://...` (SQLAlchemy URL, not a raw `postgres://` DSN) |

---

## Step-by-step implementation requirements

## Step 1 — Repository root and PostgreSQL

Create root files that make local development repeatable:

- `.gitignore` covering virtualenvs, Python cache, `node_modules`, frontend build output, and `.env`.
- `.env.example` with PostgreSQL credentials, `DATABASE_URL`, API host/port, and CORS origins. Copy to `.env` for local work; do **not** commit `.env`.
- `docker-compose.yml` running PostgreSQL 16 with a named volume, port mapping, and a healthcheck.

Start Compose and confirm the database container becomes healthy.

Acceptance criteria:

- `docker compose ps` shows a healthy Postgres service.
- `.env` is gitignored; `.env.example` is committed.

## Step 2 — Backend project and layered folders

Create a Python project under `backend/` with:

- Virtual environment and dependencies: FastAPI, Uvicorn, SQLAlchemy 2, psycopg, Alembic, pydantic-settings, scalar-fastapi, plus optional dev extras (pytest, httpx, ruff).
- Layered packages: `domain`, `application`, `infrastructure`, `interfaces/api`.
- Settings loaded from environment / `.env`.
- Database module that can execute `SELECT 1` and report success or failure.

Acceptance criteria:

- Backend installs in editable mode with dev extras.
- Settings and engine share the same `DATABASE_URL` as Compose.

## Step 3 — Health API, CORS, and Scalar

Expose:

- `GET /health` returning JSON with overall status and a database field (`ok` / `fail`).
- `GET /` with a short discovery payload pointing at Scalar and OpenAPI.
- Scalar UI at `GET /scalar` (not included in the OpenAPI schema as a business operation).
- CORS allowing the Vite origin (`http://localhost:5173` or equivalent from settings).
- Built-in Swagger `/docs` and ReDoc disabled.

Acceptance criteria:

- With Postgres running, `GET /health` reports `"db": "ok"`.
- http://localhost:8000/scalar loads and documents `/health`.
- http://localhost:8000/openapi.json is available.
- `/docs` is not served.

## Step 4 — Alembic baseline (no business tables)

Initialize Alembic and wire it to the same settings/`DATABASE_URL` as the app.

- Baseline revision upgrade is empty (no `devices` or other product tables).
- `target_metadata` may remain unset until Phase 2 introduces ORM models.
- Apply the baseline to the local database.

Acceptance criteria:

- `alembic current` points at the baseline revision.
- Database inspection shows `alembic_version` and **no** business tables.

## Step 5 — Frontend shell

Scaffold Vite + React + TypeScript. Install React Router and Tailwind CSS v4 via the Vite plugin.

Required UI:

- Global styles via `@import "tailwindcss"` (no leftover Vite `App.css` styling).
- Environment-based API base URL (direct backend URL or Vite proxy).
- Typed health fetch in a dedicated API module.
- Header layout with project title, navigation (home + dashboard), and a health badge that reflects API + DB.
- Dashboard page with placeholder sections that later phases will fill: sensors, configuration, automation, overview, controls, events. Use stable element `id`s so later phases can target them.
- Tailwind-only styling consistent with later phases (cards, spacing, status colors).

Acceptance criteria:

- http://localhost:5173/dashboard renders the placeholders in a responsive grid.
- Health badge shows API and DB status when backend and Postgres are running.
- Tailwind utilities visibly apply (for example status color on a healthy badge).

## Step 6 — Root README

Document at the repository root:

- One-line project description.
- Prerequisites.
- First-time setup (env, Compose, backend install, Alembic upgrade, frontend install).
- Daily start (database + backend + frontend).
- URLs: API, Scalar, OpenAPI, UI.
- Link to `docs/phases/README.md` for phase order.

Acceptance criteria:

- A new teammate can start the stack from README alone.

## Step 7 — Optional quality tooling

Recommended but not required to finish the phase:

- Ruff check/format for Python.
- One smoke test that `GET /health` returns 200 and a `db` field of `ok` or `fail`.

Acceptance criteria (if you add the test):

- Test runs from the backend project with a documented `PYTHONPATH` or equivalent.

---

## Definition of done

Phase 1 is done when all items below are true:

- Postgres is healthy via Compose.
- Alembic baseline is applied; no business tables exist.
- `GET /health` returns `"db": "ok"` with the stack running.
- Scalar documents `/health`; Swagger `/docs` is disabled.
- Dashboard shows placeholder sections and a working health badge.
- Root README documents start order.
- `.env` is gitignored; `.env.example` is committed.

---

## Common pitfalls to avoid

- Putting ORM models or business tables in this phase.
- Leaving Swagger `/docs` enabled instead of Scalar.
- Running Uvicorn from the wrong directory so `infrastructure` imports fail.
- Committing `.env`.
- Styling with leftover Vite CSS instead of Tailwind.
- Skipping Alembic because “there are no tables yet” — the baseline exists to prove the toolchain.

---

## Handoff to next phases

- Phase 2 (Factory Method) will add `devices`, sensor creators, `/api/sensors`, and fill the **Sensors** dashboard section.
- Keep the layered folders and Alembic wiring; Phase 2 should not need a repo restructure.

→ [Phase 2 — Factory Method (requirements)](../phase-02/requirements.md) · [guided check](../phase-02/guided-check.md)
