# Phase 5 — Adapter (Requirements)

This is the **assignment**. Implement from these requirements. If you get stuck or want to check your design, use the [guided check](guided-check.md) (signatures and partial snippets — not a complete solution).

After you implement, answer the [questions](./questions.md).

## Purpose

Read sensors through **port** abstractions and **adapters**, then **store each reading** so history and later Strategy use real persisted data rather than one-off in-memory values. Simulation and vendor-stub adapters are the course’s **mocked** device drivers—no lab hardware required.

## Scope and naming rules

- Adapters translate vendor or simulation APIs into a unified reading shape. Domain/application code talks to **ports**, not vendor SDKs.
- Persist every successful read in `sensor_readings` keyed by `device_id`.
- Keep `location_id` as the site scope from Phase 4; do not introduce `greenhouse_id`.
- Domain ports must not depend on FastAPI, SQLAlchemy, or Pydantic.

## Outcome required at end of phase

- At least two adapters implement the same sensor port (simulation plus a stub “vendor”).
- `ActuatorPort` and a **simulation actuator adapter** exist (in-memory apply or log-only—no GPIO); Phase 9 Decorator wraps this port.
- `POST` read on a sensor triggers an adapter, inserts a reading, and returns a normalized DTO.
- Sensor cards can “Read now” and show value + source; history survives refresh.
- Scalar documents the read/history endpoints.
- Pattern note exists at `docs/patterns/adapter.md`.

---

## Prerequisites

Before starting, all of the following must be true:

- Phase 4 completed: `locations` / `zones` with `location_id`.
- Phase 2–3: sensor `device_id`s exist in `devices`.
- Alembic is at Phase 4 head.

If any prerequisite is missing, fix it first.

---

## Required architecture for this phase

- **Domain layer**
  - `SensorPort` and `ActuatorPort` defining unified read/apply operations (actuator: simulation adapter only—no real GPIO).
  - Normalized reading value object (value, unit, source, timestamp).
  - No HTTP or ORM types.

- **Application layer**
  - Use case: resolve device → pick adapter → read → persist → map to DTO.
  - Reading request/response DTOs.

- **Infrastructure layer**
  - Concrete sensor adapters (simulation; vendor stub with a different raw shape).
  - `SimulationActuatorAdapter` implementing `ActuatorPort` (stub apply for Phases 9–10).
  - ORM for `sensor_readings` and a readings repository.
  - Adapter selection by device family, protocol, or an explicit source flag — document your rule.

- **API layer**
  - Trigger read and list recent readings under `/api/sensors/...`.
  - Missing device → 404; adapter/domain errors → 400-level with detail.

- **Frontend**
  - Read action on sensor cards; value + source badge; optional last-reading fetch.

---

## Suggested file locations

Paths are relative to **`yourpath\project\`**.

```text
yourpath\project\
├── backend/src/
│   ├── domain/sensors/ports.py              # SensorPort
│   ├── domain/actuators/ports.py            # ActuatorPort
│   ├── domain/sensors/reading.py            # Reading
│   ├── application/readings/dto.py
│   ├── application/readings/service.py
│   ├── infrastructure/adapters/sensors/       # simulation.py, vendor_stub.py
│   ├── infrastructure/adapters/actuators/simulation.py  # SimulationActuatorAdapter
│   ├── infrastructure/persistence/models.py # ReadingRow
│   ├── infrastructure/persistence/reading_repository.py
│   └── interfaces/api/sensors.py            # + read/history
└── frontend/src/features/sensors/           # Read now on existing cards
```

## Type hints

Domain `Reading`:

| Field | Hint |
|-------|------|
| `device_id` | `UUID` |
| `value` | `float` |
| `unit` | `str` (e.g. `vwc`, `lux`) |
| `source` | `str` — `"simulation"` or `"vendor"` |
| `recorded_at` | timezone-aware `datetime` |

ORM `sensor_readings`:

| Column | SQL hint |
|--------|----------|
| `id` | UUID PK |
| `device_id` | UUID FK → `devices` |
| `value` | NUMERIC |
| `unit` | VARCHAR |
| `source` | VARCHAR |
| `recorded_at` | timestamptz |
| Index | `(device_id, recorded_at DESC)` |

API `ReadingDto` JSON: `{ device_id, value: number, unit, source, recorded_at: ISO-8601 string }`.

---

## Step-by-step implementation requirements

## Step 1 — Database model

`sensor_readings` table:

| Column | Intent |
|--------|--------|
| Identifier | Primary key |
| `device_id` | FK → `devices` |
| `value` | Numeric reading |
| `unit` | Unit string |
| `source` | `simulation` or `vendor` (or equivalent) |
| `recorded_at` | Timestamptz |

Index `(device_id, recorded_at)` (descending if your dialect supports it) for latest-row and later charts.

Acceptance criteria:

- FK from readings to devices exists.
- Index supports “latest reading per device”.

## Step 2 — Generate migration via Alembic

Autogenerate from the ORM model (message such as `sensor_readings`). Review create table + index + FK. Apply. Do not edit applied revisions.

Acceptance criteria:

- `alembic current` is the new revision.
- Table inspection shows `sensor_readings`.

## Step 3 — Ports and adapters

Define a sensor port with a read operation that returns a normalized reading.

Implement:

- **Simulation adapter** — produces a plausible value/unit for the device type (moisture vs light).
- **Vendor stub adapter** — accepts a different raw payload or internal structure and **translates** it to the same normalized type. Translation is the point of Adapter.
- **Actuator port + simulation actuator adapter** — define `ActuatorPort.apply(device_id, command, payload)` and a `SimulationActuatorAdapter` that records intent in memory or logs only (no GPIO). Phase 9 will wrap this port with decorators.

Acceptance criteria:

- Application code depends on the port, not on adapter classes (except a factory/selector).
- Two sensor adapters can yield different `source` values for the same logical read.
- `ActuatorPort` and `SimulationActuatorAdapter` compile and can be called from a test or thin demo route (full command flow comes in Phases 9–10).

## Step 4 — Persistence and application service

Repository inserts a reading and lists recent readings for a device (limit / latest).

Service:

- Load device; 404-equivalent if missing.
- Select adapter; call port; persist; return DTO.

Acceptance criteria:

- Each successful API read appends a row (not overwrite-only unless you also keep history another way — history must exist).
- DTO includes value, unit, source, recorded_at, device_id.

## Step 5 — API endpoints

- Trigger read: e.g. `POST /api/sensors/{id}/read`.
- Optional: `GET /api/sensors/{id}/readings?limit=`.

HTTP: 200/201 on success; 404 missing device; 400 adapter/validation failures.

Acceptance criteria:

- Scalar documents the endpoints and reading schema.
- Repeated reads increase row count.

## Step 6 — Frontend

On sensor cards (Phase 2 list or equivalent):

- “Read now” calls the read endpoint.
- Show latest value and a **source** badge.
- Optional last-reading GET for display after refresh.
- Tailwind conventions; loading and error states.

Acceptance criteria:

- Refresh still shows the last stored value (from DB, not only React state).

## Step 7 — Tests

- Adapter unit tests: vendor/raw shape maps to normalized fields.
- Integration: read inserts a `sensor_readings` row.

Acceptance criteria:

- Translation tests do not require HTTP.

## Step 8 — Documentation

`docs/patterns/adapter.md`: problem (incompatible APIs), solution (port + adapters), where in code, extension (third vendor).

---

## Definition of done

Phase 5 is done when all items below are true:

- `sensor_readings` exists with FK and index.
- At least two adapters implement the sensor port.
- `ActuatorPort` and `SimulationActuatorAdapter` exist (stub apply; no GPIO).
- Read API persists and returns a normalized DTO.
- UI can trigger a read and show value + source from persisted data.
- Tests cover translation and insert.
- Pattern doc exists.

---

## Common pitfalls to avoid

- Calling vendor-shaped types from the API router.
- Storing readings only in memory.
- Skipping the index needed for “latest” queries.
- One adapter class with `if source ==` sprawl instead of separate adapter types.

---

## Handoff to next phases

- Phase 6 (Strategy) will use latest readings plus zone thresholds per `location_id` (readings remain adapter-produced; still simulated/stubbed).
- Phase 9 (Decorator) wraps the **Phase 5 `ActuatorPort`**—do not skip the simulation actuator adapter.
- Phase 11 (Observer) will publish `reading.created` from this pipeline.
- Optional Phase 13 charts query this table.

### Beyond the course (real hardware)

When you add physical sensors or actuators later, keep application services unchanged:

1. Add new adapter classes implementing `SensorPort` / `ActuatorPort` (e.g. GPIO, Modbus, DMX).
2. Extend the selector: map `device_family`, `protocol`, or env flag to the live adapter.
3. Optionally add a live `DeviceFamilyFactory` or `edge-live` family; keep `sensor_readings` schema as-is.
4. Do not move irrigation policy or state rules into adapters—translation and apply only.

→ [Phase 6 — Strategy (requirements)](../phase-06/requirements.md) · [guided check](../phase-06/guided-check.md)
