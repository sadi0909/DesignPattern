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
| 14 | Tests & demo — test pyramid on pattern seams, integration tests, `docs/patterns/` reflections | Not started |

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

## Where things live

- Phase answers: [`QuestionsAnswers/`](../../QuestionsAnswers/)
- Pattern reflections (Phase 2 onward): `docs/patterns/`
- Schema, FK policies, and realtime notes: [`docs/schema.md`](../schema.md)
- Course materials: per-phase guide, requirements, and guided check documents.
