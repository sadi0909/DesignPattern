# Observer — Phase 11

## Problem

The greenhouse already had two interesting things happen at runtime: a sensor reading was persisted, and an operator command was executed. Nothing else could react to either without editing the service that produced it.

Adding the first alert naively would look like this:

```python
# Smell: the reading pipeline knows every consumer
persisted = self._readings.insert(reading)
self._alerts.record(...)       # new dependency
self._metrics.increment(...)   # next sprint
self._websocket.broadcast(...) # Phase 12
```

Every new reaction would edit `ReadingService`, make its tests construct more collaborators, and couple a domain use case to alert persistence and transport. The smell is **the producer knows all consumers by name**.

Observer removes that list from the producer: services publish a domain event, and subscribers opt in.

## Solution

`EventBus` is the subject. It keeps a list of handlers per event class and notifies them when something is published. Publishers only know `EventBus`.

| Role | In Phase 11 |
|------|-------------|
| **Subject / event bus** | `EventBus` in `domain/events/bus.py` |
| **Observer / subscriber** | `MoistureThresholdSubscriber`, `AlertPersistenceSubscriber` |
| **Event** | `ReadingTaken`, `ThresholdCrossed`, `CommandExecuted`, `ActuatorStateChanged` |
| **Publisher** | `ReadingService` and `CommandService` |
| **Concrete transport (later)** | WebSocket subscriber in Phase 12; polling in this phase |

`EventBus.subscribe(event_type, handler)` registers a handler and returns an unsubscribe callable. `publish(event)` walks the event class MRO so a handler registered for `DomainEvent` sees every event. Handlers run synchronously and in registration order.

### Failure isolation

A subscriber that raises must not stop the fan-out. `publish()` wraps each handler in `try/except`, logs the exception with its traceback, and continues to the next subscriber. This matters as soon as there is more than one consumer: a broken alert writer must not prevent metrics or the Phase 12 WebSocket bridge from receiving the same event.

## Event catalog

| Event | Published by | When | Main fields |
|-------|--------------|------|-------------|
| `ReadingTaken` | `ReadingService` | After the reading row is committed | `device_id`, `location_id`, `sensor_type`, `value`, `unit` |
| `ThresholdCrossed` | `MoistureThresholdSubscriber` | A moisture reading is outside a zone's thresholds | `zone_name`, `moisture`, `threshold`, `direction`, `severity` |
| `CommandExecuted` | `CommandService` | A command succeeds, fails in the decorated port, or is rejected | `command_type`, `status`, `error_message` |
| `ActuatorStateChanged` | `CommandService` | A guarded lifecycle transition was saved | `from_state`, `to_state` |

`ThresholdCrossed.moisture` and `.threshold` are 0–1 fractions, matching `zones.moisture_threshold_low/high`. Sensor readings use percent, so the subscriber divides the reading by 100 before comparing. Alert messages format both values back as percentages.

## Read path

```text
POST /api/sensors/{id}/read
  └── ReadingService.take_reading
        1. resolve device and adapter
        2. persist sensor_readings row
        3. publish ReadingTaken
              └── EventBus
                    └── MoistureThresholdSubscriber
                          - ignore non-moisture readings and unassigned devices
                          - load the location's zones
                          - compare moisture with low/high thresholds
                          - publish ThresholdCrossed(direction, threshold, zone)
                                └── EventBus
                                      └── AlertPersistenceSubscriber
                                            - skip while an active alert exists
                                              for this device + threshold.crossed
                                            - insert alerts row
  └── return the reading DTO
```

The reading request does not import `AlertRepository`, and the alert subscriber does not know the reading endpoint exists. Adding a metrics subscriber means subscribing another handler in the composition root.

A reading published before its row is committed would let a subscriber fail to see it; the publish is therefore after `ReadingRepository.insert()` returns.

## Command path

`CommandService` already had three outcomes: success, rejected by State, and failed inside the decorated port. It publishes `CommandExecuted` for all three and `ActuatorStateChanged` after a successful lifecycle transition.

`AlertPersistenceSubscriber` only writes an alert for `status="failed"` (event type `command.failed`, severity `critical`). A rejected command is a valid guard decision, not a hardware incident, and is already visible in command history. The alert carries the command type and the failure message so the feed is readable without opening the command table.

## `alerts` table

| Column | Meaning |
|--------|---------|
| `id` | UUID primary key |
| `location_id` | FK to `locations`, nullable, `ON DELETE SET NULL` |
| `device_id` | FK to `devices`, nullable, `ON DELETE SET NULL` |
| `severity` | `info`, `warning`, or `critical` |
| `message` | Human-readable alert text |
| `event_type` | `threshold.crossed` or `command.failed` |
| `status` | `active` or `resolved` |
| `created_at` | Timestamptz, server default `now()` |
| `acknowledged_at` | Nullable; reserved for acknowledgement |

Check constraints keep `severity` and `status` inside their allowed values. Both foreign keys are `SET NULL` because alerts are history: deleting a device should not erase the fact that it once alarmed.

Threshold alerts are de-duplicated while an alert for the same `device_id` + `threshold.crossed` is still `active`. Repeated dry readings therefore do not flood the feed. Command failures are recorded per attempt because each failed operator action is a separate incident.

## API

`GET /api/alerts` returns newest first.

| Query parameter | Meaning |
|-----------------|---------|
| `status` | `active` or `resolved`; omitted returns both |
| `location_id` | Only alerts for one site scope |
| `since` | Only alerts created at or after an ISO-8601 timestamp |
| `limit` | 1–200, default 50 |

Response items contain `id`, `location_id`, `device_id`, `severity`, `message`, `event_type`, `status`, `created_at`, and `acknowledged_at`.

The alerts router is included before the Scalar UI is served, so Scalar lists the endpoint under the `alerts` tag. The response model is `AlertDto`, which also drives the OpenAPI schema.

## UI

`#events` uses `EventFeed`. It calls `GET /api/alerts?status=active&limit=50` immediately and then every **5 seconds** (`POLL_INTERVAL_MS = 5000`). The interval is visible in the panel (“Polling every 5 seconds”) and in the component source.

The feed shows a severity badge (`info` blue, `warning` amber, `critical` red), the message, the event type, the short device ID, and the timestamp. It has loading, error, and empty states, and a manual Refresh button. Because the feed reads PostgreSQL, a page refresh still shows the same alerts.

## Phase boundary with WebSocket

This phase deliberately does **not** open a socket. `frontend/src/services/realtime.ts` exports `RealtimeEvent = { type: string; payload: unknown }` and `subscribeRealtime(handler)`, which currently returns a no-op unsubscribe. Its docstring says Phase 12 replaces the module with a WebSocket client.

On the backend, the bus is process-wide (`get_event_bus()`), not per request. That is the seam Phase 12 needs: one WebSocket subscriber registered on the same bus receives every future reading/command event, and the transport is not rebuilt inside socket handlers. Polling is the honest Phase 11 transport; it proves the event-to-alert flow without implementing Phase 12 early.

## Where it lives in code

- Event types: `backend/src/domain/events/events.py`
- Bus: `backend/src/domain/events/bus.py`
- Alert entity: `backend/src/domain/alerts/entity.py`
- Subscribers: `backend/src/application/alerts/subscribers.py`
- Alert DTO: `backend/src/application/alerts/dto.py`
- Persistence: `AlertRow` in `backend/src/infrastructure/persistence/models.py`, `alert_repository.py`, migration `0f8f495c39ee_alerts.py`
- Composition root: `backend/src/infrastructure/events/composition.py`
- API: `backend/src/interfaces/api/alerts.py`
- Publishers wired in: `backend/src/application/readings/service.py`, `backend/src/application/commands/service.py`
- UI: `frontend/src/components/events/EventFeed.tsx`, `frontend/src/services/realtime.ts`
- Tests: `backend/tests/test_events.py`

## Design decisions

- **One event for “reading stored”, another for “threshold crossed.”** The reading pipeline should not contain the alerting rule, and the threshold rule should not depend on how the reading was persisted. The threshold subscriber is the only place that knows zone configuration.
- **Rule in the subscriber.** The guidance is explicit: keep alert rules out of the producer. A change from “below low” to “below low for three readings” edits one subscriber, not the reading service.
- **A process-wide bus with per-event sessions.** Phase 12 needs one subscription point. A bus-owned singleton cannot hold a request-scoped SQLAlchemy session, so each infrastructure handler opens a short session, delegates to a repository-injected subscriber, and commits. Unit tests construct the same subscribers directly with fakes.
- **Persist, don’t cache.** Alerts are rows, not React state. That is what survives refresh and what later phases can query by location or time.
- **Isolate subscriber failures.** Alert persistence failing should not turn a successful sensor read into a 500. The bus logs the failure; the reading still succeeds.
- **Deduplicate threshold alerts.** Without it, a dry zone produces one alert per poll/read. Deduplication is scoped to active alerts, so future resolution work can re-alert naturally.

## Known limitations

- There is no acknowledgement or resolution endpoint yet; `status` stays `active` and `acknowledged_at` stays `null`. The table is ready for it.
- De-duplication is per device + event type, not per zone. A device that is low in two zones gets one alert.
- Alert persistence is a separate commit from the reading/command write, so a crash between them can lose an alert. A production system would use an outbox.
- Publishing is synchronous: slow subscribers delay the HTTP response. Heavy work belongs in a queue, as the guide notes.
- A subscriber failure is logged but not retried, and the API response cannot report that an alert was lost.
- Only moisture threshold crossings and failed commands produce alerts; other event types are published for future subscribers but have no alert rule.
- There is no retention policy for `alerts`; the table grows without bound.

## Add-a-subscriber exercise

To add a metrics counter:

1. Create `MetricsSubscriber` in `application/alerts/` with a `handle(event)` method (or one method per event type).
2. Subscribe it in `build_event_bus()`; no publisher changes.
3. Prove isolation with a failing subscriber test: the metrics handler still receives events after another handler raises.
