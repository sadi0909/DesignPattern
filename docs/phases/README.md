# Phases

This project grows a smart greenhouse control system one phase at a time. Each phase introduces one topic and wires it into the codebase with migrations, API routes, and UI updates.

## Required track (Phases 1–12)

| Phase | Topic | Status |
|-------|-------|--------|
| 1 | Skeleton — layered layout, health check, Alembic baseline, Scalar, React + Tailwind shell | ✅ Done |
| 2 | Factory Method — sensor creators, `devices` table, `/api/sensors` | ✅ Done |
| 3 | Abstract Factory — coherent device families (simulation vs edge) | ✅ Done |
| 4 | Builder — stepwise location/zone configuration | ✅ Done |
| 5 | Adapter — sensor/actuator ports, adapters, `sensor_readings` | ✅ Done |
| 6 | Strategy — interchangeable automation policies | ✅ Done |
| 7 | Facade — single location-scoped overview operation | ✅ Done — optional Phase 4 device location link activated |
| 8 | State — actuator lifecycle with guarded transitions | ✅ Done |
| 9 | Decorator — logging/policies wrapped around actuator execution | ✅ Done |
| 10 | Command — encapsulated actuator actions, command history | ✅ Done |
| 11 | Observer — in-process event bus, alerts, event feed | ✅ Done |
| 12 | API / WS / hardening — production `/api`, WebSocket fan-out, indexes, seeds | ✅ Done |

## Optional enrichment (Phases 13–14)

| Phase | Topic | Status |
|-------|-------|--------|
| 13 | Dashboard polish — loading/empty/error states, charts from historical readings | ✅ Done (optional) |
| 14 | Tests & demo — test pyramid on pattern seams, integration tests, `docs/patterns/` reflections | ✅ Done (optional) |

## Phase 13 notes (optional)

Implemented: a historical moisture chart fed by
`GET /api/sensors/{id}/readings?from=&to=`, 12-reading sparklines on sensor
cards, an active/all alert filter with severity sorting, loading skeletons,
a route-level error boundary, and exponential WebSocket backoff capped at
15 seconds.

Deferred: editing an existing location configuration (the wizard still creates
only), and resolving alerts from the UI (no `PATCH /api/alerts/{id}` route in
this build). The chart needs no new index; the existing
`sensor_readings (device_id, recorded_at DESC)` index supports the range scan.

## Phase 14 notes (optional)

Implemented without production-code changes:

- `backend/tests/test_demo_flow.py` — the demo narrative as one PostgreSQL test:
  dry location, device family, sensor read, unordered WebSocket pair
  (`reading.created` + `alert.created`), pump start (`actuator.state_changed`),
  then history, range, overview, alert, and command checks plus a fresh client.
- `backend/tests/test_migrations.py` — one linear revision graph (parsed from
  `alembic/versions/`, because `backend/alembic` shadows the installed package),
  then `upgrade head` twice and `downgrade base` on a scratch database.
- [`docs/testing.md`](../testing.md) — test pyramid, seam-to-test map, commands,
  and uncovered areas.
- [`docs/demo.md`](../demo.md) — five-minute walkthrough and talk track.
- [`docs/patterns/README.md`](../patterns/README.md) — index of the ten pattern
  notes with their seams and proving tests.

The suite runs with or without PostgreSQL; database tests are gated by
`RUN_DB_INTEGRATION=1`. The frontend has no automated renderer tests; it is
verified by `npm run build` and the manual demo.

## Where things live

- Phase answers: [`QuestionsAnswers/`](../../QuestionsAnswers/)
- Pattern reflections (Phase 2 onward): `docs/patterns/`
- Schema, FK policies, and realtime notes: [`docs/schema.md`](../schema.md)
- Course materials: per-phase guide, requirements, and guided check documents.
