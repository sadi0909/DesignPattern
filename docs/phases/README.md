# Phases

This project grows a smart greenhouse control system one phase at a time. Each phase introduces one topic and wires it into the codebase with migrations, API routes, and UI updates.

## Required track (Phases 1–12)

| Phase | Topic | Status |
|-------|-------|--------|
| 1 | Skeleton — layered layout, health check, Alembic baseline, Scalar, React + Tailwind shell | ✅ Done |
| 2 | Factory Method — sensor creators, `devices` table, `/api/sensors` | ⬜ Next |
| 3 | Abstract Factory — coherent device families (simulation vs edge) | ⬜ |
| 4 | Builder — stepwise location/zone configuration | ⬜ |
| 5 | Adapter — sensor/actuator ports, adapters, `sensor_readings` | ⬜ |
| 6 | Strategy — interchangeable automation policies | ⬜ |
| 7 | Facade — single overview operation | ⬜ |
| 8 | State — actuator lifecycle with guarded transitions | ⬜ |
| 9 | Decorator — logging/policies wrapped around actuator execution | ⬜ |
| 10 | Command — encapsulated actuator actions, command history | ⬜ |
| 11 | Observer — in-process event bus, alerts, event feed | ⬜ |
| 12 | API / WS / hardening — production `/api`, WebSocket fan-out, indexes, seeds | ⬜ |

## Optional enrichment (Phases 13–14)

| Phase | Topic |
|-------|-------|
| 13 | Dashboard polish — loading/empty/error states, charts from historical readings |
| 14 | Tests & demo — test pyramid on pattern seams, integration tests, `docs/patterns/` reflections |

## Where things live

- Phase answers: [`QuestionsAnswers/`](../../QuestionsAnswers/)
- Pattern reflections (Phase 2 onward): `docs/patterns/`
- Course materials: per-phase guide, requirements, and guided check documents.
