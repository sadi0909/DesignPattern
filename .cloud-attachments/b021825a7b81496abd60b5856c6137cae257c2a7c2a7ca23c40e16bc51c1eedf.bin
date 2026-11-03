# Phase 6 — Strategy (Requirements)

This is the **assignment**. Implement from these requirements. If you get stuck or want to check your design, use the [guided check](guided-check.md) (signatures and partial snippets — not a complete solution).

After you implement, answer the [questions](./questions.md).

## Purpose

Add **pluggable automation strategies** that decide irrigation (or equivalent) from **latest DB readings** and **zone thresholds**, and persist which strategy applies per **location**.

## Scope and naming rules

- Evaluate **per `location_id`**, using `zones` thresholds from Phase 4 and `sensor_readings` from Phase 5.
- Do not hard-code “if moisture < 0.3” in the API handler. Algorithms live in strategy classes behind a common interface.
- `location_id` naming only — no `greenhouse_id`.

## Outcome required at end of phase

- At least two strategies produce different recommendations for the same context.
- Active strategy key is persisted per location.
- Evaluate endpoint returns a recommendation DTO.
- Dashboard strategy panel can save a key and trigger evaluate.
- Scalar documents automation endpoints.
- Pattern note at `docs/patterns/strategy.md`.

---

## Prerequisites

- Phase 5: `sensor_readings` populated by reads.
- Phase 4: zones with moisture thresholds and `location_id`.
- Alembic at Phase 5 head.

---

## Required architecture for this phase

- **Domain:** strategy interface `decide(context)`; concrete strategies; context object built from readings + thresholds (plain Python).
- **Application:** DTOs for strategy key + evaluation result; service loads context from repositories, selects strategy, returns recommendation.
- **Infrastructure:** persist `strategy_key` (dedicated `automation_rules` table **or** columns on `locations` — pick one and document it); repositories for rules and for assembling context.
- **API:** save strategy; evaluate for a location.
- **Frontend:** dropdown + evaluate; show recommendation.

---

## Suggested file locations

Paths are relative to **`yourpath\project\`**.

```text
yourpath\project\
├── backend/src/
│   ├── domain/automation/strategy.py     # AutomationStrategy + concrete strategies
│   ├── domain/automation/context.py      # LocationAutomationContext
│   ├── application/automation/dto.py
│   ├── application/automation/service.py
│   ├── infrastructure/persistence/models.py
│   ├── infrastructure/persistence/automation_repository.py
│   └── interfaces/api/automation.py
└── frontend/src/.../StrategyPanel.tsx    # mount in #automation
```

## Type hints

Domain:

| Type | Fields |
|------|--------|
| `LocationAutomationContext` | `location_id: UUID`, latest moisture `float` (optional light `float`), zone `low`/`high` `float` |
| `Recommendation` | `action: str` (e.g. `irrigate` \| `wait`), `reason: str`, optional `score: float` |
| Strategy key | `str` — `"conservative"` \| `"aggressive"` |

ORM `automation_rules` (preferred):

| Column | SQL hint |
|--------|----------|
| `id` | UUID PK |
| `location_id` | UUID FK → `locations`, **UNIQUE** |
| `strategy_key` | VARCHAR |
| `parameters` | JSONB, optional |
| `updated_at` | timestamptz |

Evaluate response JSON: `{ location_id, strategy_key, action, reason }`. Save body: `{ "strategy_key": string }`.

---

## Step-by-step implementation requirements

## Step 1 — Persistence of strategy choice

Either:

- Table `automation_rules`: id, **`location_id`** FK unique, `strategy_key`, optional `parameters` JSON, `updated_at`; or
- Columns `strategy_key` + `parameters` on `locations`.

Autogenerate and apply. Index/unique so one active strategy per location.

Acceptance criteria:

- Changing strategy in the API updates persisted data.
- No `greenhouse_id` in schema.

## Step 2 — Strategy domain

Interface with `decide(context)` returning a recommendation (action, reason, optional intensity).

At least:

- Conservative moisture strategy.
- Aggressive moisture strategy.

Context includes latest moisture (and optionally light) plus zone low/high thresholds for that location.

Acceptance criteria:

- Same context, different strategy keys → observably different recommendations (document the difference).
- Unknown strategy key is rejected before calling `decide`.

## Step 3 — Application orchestration

Build context from SQL (latest reading per relevant sensor + zones for `location_id`). Do not pass raw ORM rows into strategy classes.

Map recommendation to a DTO.

Acceptance criteria:

- Strategies stay free of SQLAlchemy.
- Missing location → not-found style error.

## Step 4 — API

- Upsert strategy for a location (PUT/PATCH or POST).
- `POST /api/locations/{location_id}/automation/evaluate` (or equivalent) → recommendation.

400 for unknown keys; 404 for missing location.

Acceptance criteria:

- Scalar shows schemas.
- Evaluate uses the **persisted** key, not only a query param (query override is optional extra).

## Step 5 — Frontend

**Strategy panel** in `#automation`:

- Dropdown of known keys; save to API.
- Evaluate button; display action + reason.
- Tailwind; error/success states.

Acceptance criteria:

- Change strategy → next evaluate differs for the same moisture (seed or read first).

## Step 6 — Tests and docs

- Unit tests with a fake context for both strategies.
- Optional integration with seeded readings + zones.
- `docs/patterns/strategy.md`: problem, interface, where in code, add-a-third-strategy exercise.

---

## Definition of done

- Strategy key persisted per location.
- Two algorithms behind one interface.
- Evaluate API + UI work against DB readings and zone thresholds.
- Tests and pattern doc complete.

---

## Common pitfalls to avoid

- `if strategy == "conservative"` in the router instead of polymorphism.
- Reading thresholds from hardcoded constants instead of `zones`.
- Evaluating without persisting the selected key.

---

## Handoff to next phases

- Phase 7 (Facade) will aggregate latest readings, strategy key, and last recommendation into one overview DTO.

→ [Phase 7 — Facade (requirements)](../phase-07/requirements.md) · [guided check](../phase-07/guided-check.md)
