# Demo walkthrough

A five-minute narrative for showing the greenhouse to a reviewer, plus the
commands behind each screen. It follows the same story as
`backend/tests/test_demo_flow.py`.

## Before the demo

Follow [First-time Setup](../README.md#first-time-setup), then start the three
processes from [Daily Start](../README.md#daily-start-three-terminals). Seed the
demo rows once:

```bash
cd backend
.venv/Scripts/alembic.exe upgrade head
.venv/Scripts/python.exe seed.py
```

The seed is idempotent: re-running it inserts nothing and prints that the demo
rows are already present.

## The script

### 1. Health and transport

Open <http://localhost:5173/dashboard>. The header shows `API: ok`, `DB: ok`, and
`WS: connected`. Stop the backend briefly to show `down` and the reconnect
backoff, then restart it and show `connected` again.

### 2. Overview and seeded history

The **Overview** card shows `Demo Greenhouse`, one sensor and one actuator, the
latest seeded moisture reading, the `conservative` strategy, and a computed
recommendation.

The **Moisture trend** card reads the same value from PostgreSQL through
`GET /api/sensors/{id}/readings?from=&to=` and plots it oldest-first. The sensor
card carries a 12-reading sparkline. Change the range to prove the chart is a
query, not a canned line.

### 3. A live reading

In **Sensors**, press **Read now**. The reading is persisted by the Adapter,
published by the Observer bus, and pushed over `WS /api/ws`; the **Events** feed
shows `reading.created` without a page refresh. The 30-second poll is only a
fallback.

### 4. A deterministic alert

The seeded zone (35%–65%) may or may not alert on a random reading. To make it
certain:

1. **Configuration** → build `Demo dry bay` with one zone and thresholds
   `0.85` / `0.95`.
2. **Sensors** → create a moisture sensor.
3. **Devices** → assign that sensor to `Demo dry bay`.
4. **Sensors** → **Read now**.

Every simulated moisture value is 20–80%, so the reading is always below 85%.
The threshold subscriber publishes `ThresholdCrossed`, the alert subscriber
persists it, and the feed shows `alert.created` with `threshold.crossed` and
`warning` severity. Press **Refresh** or reload the page: the alert is still
there because it is a row, not React state.

The API equivalent is `POST /api/locations/config`, `POST /api/sensors`,
`PATCH /api/devices/{id}/location`, and `POST /api/sensors/{id}/read`.

### 5. A guarded command

In **Controls**, choose the seeded pump and press **Start pump**; confirm the
dialog. The Command object passes the State guard, the Decorator chain logs the
attempt and enforces max runtime, and the adapter applies it. The device badge
becomes `running`, **allowed commands** narrows to `stop_pump`, the **Execution
log** gains a successful row, and the command history records the attempt.

Press **Start pump** again: the State guard rejects it with `409` and the history
shows `rejected`, while the execution log stays unchanged because the request
never reached the decorated port. Then **Stop pump** to leave the pump idle.

### 6. Alerts and events

The **Events** card has an Active/All filter and sorts by severity. Active is the
default; switch to All to show resolved-capable history. Resolution is deferred
in this build: there is no `PATCH /api/alerts/{id}`.

### 7. Proof in one request

```bash
curl "http://localhost:8000/api/locations/<location-id>/overview"
```

The response is assembled by the Facade from locations, devices, readings, and
the strategy service. `GET /api/alerts?location_id=<id>` and
`GET /api/commands?limit=10` show the same facts the dashboard just displayed.

### 8. Tests

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests -q
RUN_DB_INTEGRATION=1 .venv/Scripts/python.exe -m pytest tests -q
```

The default run proves the pattern seams without a database; the second run adds
repositories, the WebSocket flow, and the migration smoke. See
[`docs/testing.md`](testing.md) for the seam-to-test map.

## Talk track

| What the viewer saw | One sentence to say |
|---------------------|---------------------|
| Sensor cards and creators | Factory Method keeps device construction in one seam. |
| Provisioned simulation kit | Abstract Factory keeps a family coherent. |
| Location wizard | Builder validates a stepwise configuration before `build()`. |
| Readings and trend | Adapter normalizes vendor/simulation data behind a port. |
| Strategy card | Strategy swaps the automation policy without editing the service. |
| Overview card | Facade gives the UI one location-scoped read. |
| Pump state badge | State guards every lifecycle transition. |
| Execution log | Decorator adds logging and runtime policy around the port. |
| Command history | Command turns an operator intent into an auditable object. |
| Live events | Observer publishes domain events; WebSocket is just one subscriber. |

## Reset

The demo data is fixed and idempotent. Test rows created by the integration suite
are removed in `finally` blocks; if an interrupted run left rows behind, the
`Phase 14 demo greenhouse` location and its devices can be deleted through the
API or by recreating the Docker volume (see the README setup section).
