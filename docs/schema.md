# Schema and realtime notes (Phases 12–13)

Phase 12 hardens the schema that grew in Phases 2–11 and documents the live
feed. No Phase 2–11 revision was edited; hardening is a new revision at the
end of the chain. Phase 13 adds no schema revision: historical chart queries
reuse the existing per-device reading index.

## Migration chain

| Revision | Purpose |
|----------|---------|
| `001_baseline` | Alembic baseline |
| `920d7a54afc3` | `devices` |
| `985f7eb19f51` | `locations`, `zones` |
| `64d5e11816a6` | `sensor_readings` |
| `7f7ae01a985c` | `devices.device_family` |
| `5e4b7df306db` | `actuator_states` |
| `e76077ba625e` | `actuator_execution_log` |
| `16c2d2e633a5` | `devices.location_id` link |
| `a1c3e9f07b2d` | `automation_rules` |
| `4b66f6de4dcc` | `command_log` |
| `0f8f495c39ee` | `alerts` |
| `b7d4c2a91f30` | **Phase 12 hardening**: composite alert indexes |

`alembic upgrade head` from an empty database applies all of them.

## Indexes that support live traffic

| Table | Index | Used by |
|-------|-------|---------|
| `sensor_readings` | `(device_id, recorded_at DESC)` | per-sensor history, chart ranges, and latest moisture |
| `alerts` | `(status, created_at DESC)` | active/resolved feed, newest first |
| `alerts` | `(location_id, created_at DESC)` | location-scoped feed |
| `alerts` | `(created_at DESC)` | unfiltered feed |
| `command_log` | `(created_at DESC)`, `(device_id)` | command history |
| `actuator_execution_log` | `(created_at DESC)`, `(device_id)` | execution log |
| `devices` | `(role)`, `(device_family)`, `(location_id)` | device filters and joins |

The Phase 12 revision replaces the old single-column `alerts(status)` and
`alerts(location_id)` indexes with composites that also order by newest
`created_at`.

Phase 13 charts call
`GET /api/sensors/{id}/readings?from=<iso>&to=<iso>`. The range filter and the
oldest-first ordering are both served by
`ix_sensor_readings_device_id_recorded_at`; Postgres can scan the index
backwards, so no chart-specific index or migration is needed.

## Foreign key delete behavior

| Child column | Parent | On delete |
|--------------|--------|-----------|
| `devices.location_id` | `locations.id` | `SET NULL` (device survives) |
| `alerts.location_id`, `alerts.device_id` | `locations.id`, `devices.id` | `SET NULL` (history survives) |
| `zones.location_id`, `automation_rules.location_id` | `locations.id` | `CASCADE` (configuration dies with its location) |
| `sensor_readings`, `actuator_states`, `actuator_execution_log`, `command_log` (`device_id`) | `devices.id` | `CASCADE` (device history dies with the device) |

All of these were created by the revisions that introduced the tables; the
hardening revision does not rewrite them.

## Idempotent demo seed

```bash
cd backend
.venv\Scripts\Activate.ps1   # or activate the venv your shell uses
python seed.py
```

`seed.py` inserts fixed-UUID demo rows (one location, one zone, a moisture
sensor, an idle water pump, a conservative automation rule, and one moisture
reading). Re-running it reports that the rows are already present and changes
nothing.

## Realtime surface

- REST stays under `/api/...`; `GET /health` remains unprefixed.
- `WS /api/ws` accepts every client in course mode and streams
  `{"type": ..., "payload": ...}` messages for `reading.created`,
  `actuator.state_changed`, and `alert.created`.
- The socket is wired in the FastAPI lifespan to the same `EventBus` used by
  the Phase 11 subscribers. The route only registers clients; alert rules and
  persistence remain in the subscribers.
- The frontend derives the URL from `VITE_API_BASE_URL` (or the current host)
  and Vite proxies `/api` including WebSockets in development.
- `EventFeed` applies pushed `alert.created` messages immediately and keeps a
  30-second `GET /api/alerts` reconciliation poll as a fallback.
