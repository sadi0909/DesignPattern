# Testing

The suite is a pyramid built on the pattern seams, not on framework details. Most
tests are fast unit tests with hand-written fakes; API tests replace only the
service dependency; a smaller set runs against PostgreSQL; and one smoke test
runs the migration chain on a throwaway database.

## Layers

| Layer | What it exercises | Database | Typical files |
|-------|-------------------|----------|---------------|
| Unit | Domain rules, pattern seams, in-memory fakes | No | `test_creators.py`, `test_location_builder.py`, `test_actuator_state.py`, `test_automation.py`, `test_events.py` |
| API contract | FastAPI routes, DTOs, status codes, OpenAPI, `dependency_overrides` | No | `test_devices_api.py`, `test_locations_api.py`, `test_overview.py`, `test_health.py` |
| Integration | Real repositories, transactions, cross-subsystem flows | Yes | Gated tests inside most modules and `test_demo_flow.py` |
| Migration smoke | Alembic graph and a clean upgrade/downgrade cycle | Yes (scratch DB) | `test_migrations.py` |

## Pattern seams and the tests that prove them

| Phase | Pattern | Seam in production code | Proving tests |
|-------|---------|-------------------------|---------------|
| 2 | Factory Method | `domain/sensors/creators.py` | `test_creators.py` |
| 3 | Abstract Factory | `domain/devices/family_factory.py` | `test_device_family_factory.py`, `test_devices_api.py` |
| 4 | Builder | `domain/locations/config_builder.py` | `test_location_builder.py`, `test_locations_api.py` |
| 5 | Adapter | `domain/sensors/ports.py`, `infrastructure/adapters/sensors/` | `test_readings.py` |
| 6 | Strategy | `domain/automation/strategy.py` | `test_automation.py` |
| 7 | Facade | `application/overview/facade.py` | `test_overview.py` |
| 8 | State | `domain/actuators/state.py` | `test_actuator_state.py` |
| 9 | Decorator | `infrastructure/adapters/actuators/logging_decorator.py`, `max_runtime_decorator.py` | `test_actuator_decorators.py` |
| 10 | Command | `domain/commands/`, `application/commands/service.py` | `test_commands.py` |
| 11 | Observer | `domain/events/bus.py`, `application/alerts/subscribers.py` | `test_events.py` |
| 12 | Observer transport | `application/realtime/` | `test_realtime.py` |

The point of each test is the seam, not the class: a new sensor creator, device
family, strategy, command, or subscriber should be provable by adding a case to
the matching test file without touching the route layer.

## Commands

```bash
cd backend

# Default suite: unit + API contract; PostgreSQL tests are skipped.
.venv/Scripts/python.exe -m pytest tests -q

# Full suite against PostgreSQL.
RUN_DB_INTEGRATION=1 .venv/Scripts/python.exe -m pytest tests -q

# One seam while iterating.
.venv/Scripts/python.exe -m pytest tests/test_actuator_state.py -q

# Lint everything, including migrations.
.venv/Scripts/ruff.exe check src tests alembic
```

PowerShell uses `$env:RUN_DB_INTEGRATION = "1"` instead of the inline prefix.

The frontend has no automated renderer tests in this build; `npm run build`
type-checks and bundles it, and the manual walkthrough in
[`docs/demo.md`](demo.md) covers the visible behavior.

## The end-to-end demo test

`tests/test_demo_flow.py` is the demo story written as one PostgreSQL test:

1. Build a location with an intentionally dry zone.
2. Provision a simulation device family and assign a moisture sensor and pump.
3. Read the sensor while a WebSocket client is connected.
4. Assert `reading.created` and `alert.created` arrive (in either order, because
   the threshold subscriber publishes its alert inside the reading publish).
5. Start the pump and assert `actuator.state_changed` (`idle` → `running`).
6. Verify the same facts through the history, range, overview, alerts, commands,
   and device APIs.
7. Open a fresh `TestClient` to prove the alert is database-backed, not socket
   state.

It creates real rows and deletes them in a `finally` block, so it is safe to run
against the development database.

## Migration smoke

`tests/test_migrations.py` has two checks:

- **Offline:** parse `revision` and `down_revision` from every file in
  `alembic/versions/`, then assert exactly one root, exactly one head, no merge
  tuples, and no dangling `down_revision`. The local `backend/alembic` package
  shadows the installed `alembic` library when pytest runs from `backend`, so the
  graph is read from source rather than imported.
- **PostgreSQL:** create a scratch database, run `alembic upgrade head` twice
  (the second run proves idempotence), confirm every core table and the head
  revision, run `downgrade base`, confirm the tables are gone, and drop the
  scratch database. The scratch URL is rendered with the password intact because
  SQLAlchemy's default string form masks it.

## What is not covered

- No browser automation, accessibility audit, or load test.
- No frontend unit tests; hooks and SVG chart math are verified by build and
  manual review.
- The WebSocket reconnect/backoff path is verified manually; the server-side
  envelope mapping and fan-out are unit tested.
- Long-running behaviour (retention, outbox, alert resolution) is documented as
  a known limitation rather than tested.
