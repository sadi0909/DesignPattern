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

See [docs/phases/README.md](docs/phases/README.md) for phase-by-phase development guide.

## Environment Variables

All `.env` files are gitignored. Use `.env.example` as templates.