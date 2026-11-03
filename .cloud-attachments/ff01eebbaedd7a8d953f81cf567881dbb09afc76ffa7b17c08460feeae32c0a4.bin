# Phase 1 — Skeleton (Guided check)

Complete the [requirements](requirements.md) first. Use this document if you are stuck or to check that your layout, commands, and contracts match. Tooling files below are scaffolding; application code is shown as **signatures and expected shapes**, not a complete solution.

**Time estimate:** 2–4 hours if tools are already installed.

---

## Target repository layout (end state)

```text
yourpath\project\
├── README.md
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 001_baseline.py
│   └── src/
│       ├── main.py
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       │   ├── settings.py
│       │   └── db.py
│       └── interfaces/api/
│           └── health.py
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── .env.example
    └── src/
        ├── main.tsx
        ├── index.css
        ├── App.tsx
        ├── services/api.ts
        ├── components/
        │   ├── AppLayout.tsx
        │   └── HealthStatus.tsx
        └── pages/
            └── DashboardPage.tsx
```

Stack: **FastAPI + SQLAlchemy + Alembic**, **Scalar** at `/scalar`, **Vite + React + TypeScript + Tailwind CSS v4**.

---

## Step 0 — Open the project root

```powershell
cd "yourpath\project\"
```

Replace `yourpath\project\` with **your** clone path (the folder that contains `docker-compose.yml`, `backend/`, and `frontend/`). All commands below assume that folder is the current directory.

---

## Step 1 — Root files and PostgreSQL

### 1.1 `.gitignore`

```gitignore
.env
.venv/
__pycache__/
*.pyc
.pytest_cache/
node_modules/
frontend/dist/
backend/.venv/
.DS_Store
```

### 1.2 `.env.example`

```env
POSTGRES_USER=greenhouse
POSTGRES_PASSWORD=greenhouse
POSTGRES_DB=greenhouse
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DATABASE_URL=postgresql+psycopg://greenhouse:greenhouse@localhost:5432/greenhouse
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173
```

```powershell
Copy-Item .env.example .env
```

### 1.3 `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: greenhouse-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-greenhouse}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-greenhouse}
      POSTGRES_DB: ${POSTGRES_DB:-greenhouse}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - greenhouse_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-greenhouse} -d ${POSTGRES_DB:-greenhouse}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  greenhouse_pgdata:
```

```powershell
docker compose up -d
docker compose ps
```

**Check:** container `greenhouse-postgres` is `healthy`. Optional: `docker exec -it greenhouse-postgres psql -U greenhouse -d greenhouse -c "SELECT 1;"`.

---

## Step 2 — Backend folders, settings, database

```powershell
New-Item -ItemType Directory -Force -Path @(
  "backend/src/domain",
  "backend/src/application",
  "backend/src/infrastructure",
  "backend/src/interfaces/api",
  "backend/alembic/versions"
)
```

Add `__init__.py` under `backend/src` packages. Create a venv in `backend/` and install from `pyproject.toml`:

```toml
[project]
name = "greenhouse-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.32.0",
  "sqlalchemy>=2.0.36",
  "psycopg[binary]>=3.2.0",
  "alembic>=1.14.0",
  "pydantic-settings>=2.6.0",
  "scalar-fastapi>=1.8.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "httpx>=0.27.0", "ruff>=0.8.0"]
```

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

**`infrastructure/settings.py`** — `Settings` from `pydantic-settings` with `database_url`, `api_host`, `api_port`, `cors_origins`. Load `.env`.

**`infrastructure/db.py`** — engine + session factory from `settings.database_url`, plus:

```python
def check_database() -> bool:
    ...
```

Run uvicorn from `backend/src` so imports like `infrastructure.db` resolve (or set `PYTHONPATH=src`).

---

## Step 3 — Health route, app entry, Scalar

**`interfaces/api/health.py`** — router tagged `health`. Your handler should return this shape when Postgres is up:

```json
{"status":"ok","db":"ok"}
```

When the database is down: `"status": "degraded"` and `"db": "fail"`.

**`main.py`** skeleton (fill CORS, Scalar, and router include yourself):

```python
from fastapi import FastAPI

app = FastAPI(
    title="Smart Greenhouse API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
)

# CORS from settings.cors_origins (comma-separated)
# include health router
# GET /  → {"message": "...", "api_reference": "/scalar", "openapi": "/openapi.json"}
# GET /scalar (include_in_schema=False) → get_scalar_api_reference(...)
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000/scalar | Interactive API reference |
| http://localhost:8000/openapi.json | OpenAPI schema |
| http://localhost:8000/docs | Must **not** exist |

```powershell
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Check:** `curl http://localhost:8000/health` matches the JSON above. Scalar shows `GET /health`. Execute it from the UI.

---

## Step 4 — Alembic baseline

From `backend/` with venv active:

```powershell
alembic init alembic
```

In `alembic.ini`, comment out `sqlalchemy.url` (URL comes from settings in `env.py`).

**`alembic/env.py`** — add `src` to `sys.path`, read `settings.database_url`, set `config.set_main_option("sqlalchemy.url", ...)`. For Phase 1, `target_metadata = None` is fine.

**`alembic/versions/001_baseline.py`:**

```python
revision = "001"
down_revision = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
```

Ensure Alembic/settings can find `.env` (copy to `backend/.env` if needed).

```powershell
alembic upgrade head
alembic current
```

**Check:** current revision is `001`. `\dt` in psql shows `alembic_version` and **no** `devices` table.

---

## Step 5 — Frontend (Vite + Tailwind)

```powershell
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install react-router-dom
npm install -D tailwindcss @tailwindcss/vite
```

**`vite.config.ts`** — React plugin + Tailwind plugin. Optional proxy `/api` → `http://localhost:8000`.

**`src/index.css`:**

```css
@import "tailwindcss";

@layer base {
  body {
    @apply min-h-screen bg-slate-50 text-slate-900 antialiased;
  }
}
```

Import `./index.css` from `main.tsx`. Remove `App.css`. Verify a heading with `className="text-2xl font-bold text-emerald-600"` actually styles.

**`frontend/.env.example`:** `VITE_API_BASE_URL=http://localhost:8000` (or `/api` if you use the proxy).

**`services/api.ts`** — type and function you should have (implement the fetch):

```typescript
export type HealthResponse = { status: string; db: "ok" | "fail" };

export async function fetchHealth(): Promise<HealthResponse> {
  ...
}
```

**`HealthStatus`** — badge label like `API: ok · DB: ok` (or `Checking…` / `API: unreachable`). Use emerald / amber / red rings for ok / degraded / error.

**`AppLayout`** — header: title “Smart Greenhouse”, `HealthStatus`, nav Home + Dashboard. `<Outlet />` in main.

**`DashboardPage`** — placeholder `id`s (keep these; later phases mount into them):

```text
sensors, config, automation, overview, controls, events
```

**`App.tsx`** — `BrowserRouter` with layout route: `/` home, `/dashboard` dashboard.

```powershell
npm run dev
```

**Check:** http://localhost:5173/dashboard shows six placeholder cards and a healthy badge when backend + Postgres are up.

---

## Step 6 — Root README

Include: one-liner, prerequisites, first-time setup, daily start (three terminals), URLs (API, Scalar, OpenAPI, UI), link to `docs/phases/README.md`.

```text
Terminal 1: docker compose up -d
Terminal 2: cd backend && .venv\Scripts\Activate.ps1 && cd src && uvicorn main:app --reload --port 8000
Terminal 3: cd frontend && npm run dev
```

---

## Step 7 — Optional smoke test

**`backend/tests/test_health.py`** — `TestClient` against `GET /health`: status 200; body has `status` and `db` in `("ok", "fail")`. Run with `PYTHONPATH=src` from `backend/` (or equivalent).

---

## Phase 1 completion checklist

Mark each item before starting [Phase 2 requirements](../phase-02/requirements.md):

- [ ] `docker compose up -d` — Postgres healthy
- [ ] `alembic upgrade head` — revision `001` applied
- [ ] `GET /health` returns `"db": "ok"`
- [ ] Scalar at `/scalar` documents `/health`; `/docs` disabled
- [ ] No business tables yet
- [ ] Tailwind utilities render
- [ ] Dashboard has six placeholder sections
- [ ] `HealthStatus` reflects `/health`
- [ ] Root README documents start order
- [ ] `.env` gitignored; `.env.example` committed

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `db: fail` | Postgres down or wrong `DATABASE_URL` | `docker compose ps`; match `.env` |
| Port 5432 in use | Local Postgres | Change `POSTGRES_PORT` |
| Alembic cannot connect | `.env` not loaded from `backend/` | Copy `.env` to `backend/.env` |
| `ModuleNotFoundError: infrastructure` | Wrong cwd | Run uvicorn from `backend/src` |
| CORS error | Direct call :8000 from :5173 | Vite proxy or `CORS_ORIGINS` |
| Tailwind has no effect | Plugin or CSS import missing | `@tailwindcss/vite` + `import "./index.css"` |
| Scalar blank | OpenAPI unreachable | Open `/openapi.json`; keep `scalar_proxy_url` |

---

## Non-goals (Phase 1)

- Business schema, sensors, actuators, automation, WebSockets, authentication
- Design pattern implementations (start in Phase 2)

---

## Next

→ [Phase 2 — Factory Method (requirements)](../phase-02/requirements.md) · [guided check](../phase-02/guided-check.md)
