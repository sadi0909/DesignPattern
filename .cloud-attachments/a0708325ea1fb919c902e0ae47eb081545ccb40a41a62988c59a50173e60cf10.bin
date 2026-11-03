# Phase 4 — Builder (Requirements)

This is the **assignment**. Implement from these requirements. If you get stuck or want to check your design, use the [guided check](guided-check.md) (signatures and partial snippets — not a complete solution).

After you implement, answer the [questions](./questions.md).

## Purpose

This phase introduces the **Builder** pattern for creating a valid **location configuration** and persists it into PostgreSQL.

## Scope and naming rules

- Use **location** terminology in data and APIs.
- Use **`location_id`** in zones and related records.
- Do **not** introduce `greenhouse_id` in this phase.
- Keep the product context as smart greenhouse; only the relational resource naming changes to location.

## Outcome required at end of phase

- A Builder workflow can create one location with one or more zones.
- Builder validation blocks invalid configurations before persistence.
- A persisted location configuration can be retrieved by location id.
- Dashboard has a configuration UI for creating location + zones.
- API reference (Scalar) documents the location config endpoints and schemas.

---

## Prerequisites

Before starting, all of the following must be true:

- Phase 3 completed successfully.
- Devices and family provisioning endpoints are functional.
- Alembic is configured and the database is at Phase 3 head revision.
- Dashboard has a placeholder configuration section.

If any prerequisite is missing, fix it first; this phase assumes that foundation.

---

## Required architecture for this phase

Implement the phase with clean layer separation:

- **Domain layer**
  - Owns the Builder and validation rules.
  - Contains location/zone configuration entities.
  - Must not depend on FastAPI, SQLAlchemy, or Pydantic.

- **Application layer**
  - Defines request/response DTOs for location configuration.
  - Maps DTOs to Builder calls and maps persistence results back to DTOs.
  - Orchestrates save/retrieve use cases through repositories.

- **Infrastructure layer**
  - Owns ORM models and repository persistence logic.
  - Persists location and zones transactionally.

- **API layer**
  - Exposes endpoints under `/api/locations/...`.
  - Uses DTOs as request/response contracts.
  - Converts domain/application errors to HTTP responses.

---

## Suggested file locations

Paths are relative to **`yourpath\project\`**.

```text
yourpath\project\
├── backend/src/
│   ├── domain/locations/entity.py            # Location, Zone, LocationConfig
│   ├── domain/locations/config_builder.py
│   ├── domain/locations/errors.py            # ConfigurationError
│   ├── application/locations/dto.py
│   ├── application/locations/mappers.py
│   ├── application/locations/config_service.py
│   ├── infrastructure/persistence/models.py  # LocationRow, ZoneRow
│   ├── infrastructure/persistence/location_repository.py
│   └── interfaces/api/locations.py
└── frontend/src/components/config/LocationConfigWizard.tsx
```

## Type hints

Domain:

| Type | Fields |
|------|--------|
| `Zone` | `name: str`, `moisture_threshold_low: float`, `moisture_threshold_high: float`, `schedule: dict`, `id: UUID \| None` |
| `Location` | `name: str`, `zones: tuple[Zone, ...]`, `id: UUID \| None` |
| `LocationConfig` | `location: Location` (builder output) |
| `ConfigurationError` | subclass of `ValueError` |

ORM:

| Table / column | SQL / mapping hint |
|----------------|-------------------|
| `locations.id` | UUID PK |
| `locations.name` | `String(128)`, not null |
| `locations.created_at` | timestamptz |
| `zones.id` | UUID PK |
| `zones.location_id` | UUID FK → `locations.id`, not null, index |
| `zones.name` | `String(128)` |
| `zones.moisture_threshold_low` / `_high` | `Numeric` (e.g. 5,4) stored as float in domain |
| `zones.schedule` | JSONB |
| `devices.location_id` | optional UUID FK, nullable |

API JSON:

| DTO | Fields |
|-----|--------|
| Request | `location_name: str`, `zones: [{ name, moisture_threshold_low: number, moisture_threshold_high: number, schedule?: object }]` |
| Response | `location: { id: UUID, name: str }`, `zones: [{ id, location_id, name, moisture_threshold_low, moisture_threshold_high, schedule }]` |

Thresholds in this product: `float` in **0.0–1.0** (VWC); low must be strictly less than high.

---

## Step-by-step implementation requirements

## Step 1 — Database model design

Define the relational model needed for location configuration:

- `locations`
  - Identifier, name, created timestamp.
- `zones`
  - Identifier, **`location_id`** foreign key to `locations`.
  - Zone name.
  - Moisture threshold low/high values.
  - Schedule payload (JSON).
- Optional extension in this phase:
  - `devices.location_id` nullable foreign key for future linking.

Validation and constraints expectations:

- Each zone belongs to exactly one location.
- `zones.location_id` must reference an existing location.
- Index zones by `location_id` for reads.

Acceptance criteria:

- Schema design uses `location_id` consistently.
- No schema artifact contains `greenhouse_id`.

## Step 2 — Generate migration via Alembic

Use Alembic autogenerate from model changes:

- Generate a new revision with a clear message such as `locations_and_zones`.
- Review generated migration carefully:
  - `locations` table creation exists.
  - `zones` table creation exists.
  - FK is from `zones.location_id` to `locations.id`.
  - Optional `devices.location_id` appears only if modeled.
- Apply migration to the local database.

Acceptance criteria:

- `alembic current` points to the new revision.
- Database inspection shows `zones.location_id`.
- Migration chain is forward-only; no edits to already-applied revisions.

## Step 3 — Builder domain behavior

Implement the Builder behavior in domain logic with these guarantees:

- Builder can set location name.
- Builder can add one or more zones.
- `build()` validates and either returns a complete configuration or raises a configuration error.

Required validation rules:

- Location name is required and non-empty.
- At least one zone is required.
- For each zone, low threshold must be strictly less than high threshold.
- Threshold ranges must be constrained to your selected domain limits (for example 0–1 for VWC).

Acceptance criteria:

- Invalid config is rejected before any database write.
- Valid config builds deterministically.

## Step 4 — DTO contracts

Define DTOs for this phase in application/API contracts:

- Request DTO for creating a location configuration:
  - Location name.
  - List of zones with thresholds and schedule.
- Response DTO for location configuration:
  - Location metadata.
  - Zone list including **`location_id`**.

Requirements:

- DTO names should clearly indicate intent (request/read models).
- DTO field names must match API JSON contract.
- Domain entities and DTOs remain separate.

Acceptance criteria:

- Endpoint contracts are typed and documented in Scalar.
- Zone response includes `location_id` in every row.

## Step 5 — Repository and transaction semantics

Implement persistence behavior with a transaction boundary:

- Save location first.
- Save all zones linked by `location_id`.
- Commit as one unit; failures rollback all writes.

Read behavior:

- Retrieve full config by location id including child zones.

Acceptance criteria:

- Partial writes do not occur on invalid or failed saves.
- Fetch returns consistent location + zones payload.

## Step 6 — API endpoints

Expose location configuration endpoints:

- Create config endpoint under `/api/locations/...`.
- Read config endpoint under `/api/locations/{location_id}/...`.

HTTP behavior requirements:

- Validation/configuration errors return 400-level responses with useful details.
- Missing location returns 404.
- Successful create returns created representation.

Acceptance criteria:

- Endpoints visible in Scalar.
- Endpoints return DTO schemas exactly as defined.

## Step 7 — Frontend configuration wizard

Implement a dashboard config wizard in the configuration section:

- Collect location name.
- Collect one or more zones with thresholds and schedule.
- Submit to location config create endpoint.
- Display saved result (including returned location id and zone list).

UI requirements:

- Show inline validation messages for obvious user input issues.
- Show API error state and success state.
- Preserve Tailwind conventions established in earlier phases.

Acceptance criteria:

- User can create a location config end-to-end from UI.
- UI reflects server validation failures clearly.

## Step 8 — Test requirements

Minimum test set:

- Builder unit tests:
  - Success path.
  - Missing location.
  - No zones.
  - Invalid threshold ordering.
- Integration/API tests:
  - Create config persists location + zones.
  - Get config returns expected structure with `location_id`.
  - Invalid payload handled with 400.

Migration checks:

- CI or local check runs migrations from empty DB to head.

Acceptance criteria:

- Tests pass reliably.
- Migration from empty database succeeds.

## Step 9 — Documentation requirements

Update learning docs:

- Add/refresh `docs/patterns/builder.md` with:
  - Builder intent in this project.
  - Why this is Builder (not Factory Method / Abstract Factory).
  - Where validation lives.
  - Why `location_id` naming is used.

Update phase references where needed:

- Ensure adjacent phases refer to location/location_id consistently.

---

## Definition of done

Phase 4 is done when all items below are true:

- Database has `locations` and `zones` with FK `zones.location_id`.
- Builder enforces required validations before persistence.
- Location config DTOs exist and are used by API.
- Endpoints for create/read location config are live and documented in Scalar.
- UI wizard can create and display persisted config.
- Automated tests cover builder validation and API persistence path.
- Documentation references `location_id` consistently.

---

## Common pitfalls to avoid

- Mixing domain entities and API DTOs directly.
- Letting builder validation happen only in API layer.
- Using `greenhouse_id` in any new schema or endpoint.
- Treating migration generation as optional manual SQL.
- Returning partially saved data on transactional failure.

---

## Handoff to next phases

- Phase 5 (Adapter) can start consuming persisted location/zone context.
- Phase 6 (Strategy) should evaluate automation per location id using zone thresholds.
- Later overview and alert flows should preserve `location_id` as the top-level scope key.

→ [Phase 5 — Adapter (requirements)](../phase-05/requirements.md) · [guided check](../phase-05/guided-check.md)

