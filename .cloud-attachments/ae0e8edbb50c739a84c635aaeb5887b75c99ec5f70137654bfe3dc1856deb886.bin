# Phase 5 — Adapter (Guided check)

Complete the [requirements](requirements.md) first. Use this document if you are stuck or to check signatures and JSON. Snippets are **not** a complete solution.

## Pattern

**Adapter** — vendor/simulation APIs → unified `SensorPort`; actuator stub → `ActuatorPort`.

```text
POST /read → SensorPort.read() → Reading → sensor_readings → ReadingDto
```

---

## Target repository layout (end state)

```text
backend/src/
├── domain/sensors/
│   ├── ports.py          # SensorPort
│   └── reading.py        # normalized Reading
├── domain/actuators/
│   └── ports.py          # ActuatorPort
├── application/readings/
│   ├── dto.py
│   └── service.py
├── infrastructure/
│   ├── adapters/sensors/         # simulation.py, vendor_stub.py
│   ├── adapters/actuators/simulation.py  # SimulationActuatorAdapter
│   └── persistence/
│       ├── models.py     # ReadingRow
│       └── reading_repository.py
└── interfaces/api/sensors.py   # + read/history routes
```

---

## Step 1 — Database model

```text
sensor_readings(id, device_id FK, value, unit, source, recorded_at)
Index: (device_id, recorded_at DESC)
```

ORM lives in infrastructure (`ReadingRow`), not in domain.

**Check:** model includes FK to `devices` and an index that supports “latest reading per device.”

---

## Step 2 — Generate migration via Alembic

```powershell
alembic revision --autogenerate -m "sensor_readings"
alembic upgrade head
```

Review `upgrade()`: create table, index, FK. Do not edit applied revisions.

**Check:** `alembic current` is the new revision; `\d sensor_readings` shows the table.

---

## Step 3 — Ports and adapters

```python
class SensorPort(ABC):
    @abstractmethod
    def read(self, device: Device) -> Reading:
        ...

class SimulationSensorAdapter(SensorPort):
    def read(self, device: Device) -> Reading:
        ...  # source="simulation"

class VendorStubSensorAdapter(SensorPort):
    def read(self, device: Device) -> Reading:
        ...  # translate a different raw dict/object; source="vendor"
```

`Reading` fields: `device_id`, `value`, `unit`, `source`, `recorded_at`.

Selector example: `protocol` in `default_config`, or `device_family` (`simulation` vs `edge`). Application code depends on `SensorPort`, not on adapter classes (except a factory/selector).

**Check:** two adapters can yield different `source` values; vendor adapter **translates**, it does not decide irrigation policy.

---

## Step 3b — Actuator port (simulation stub)

Define `ActuatorPort` and a simulation adapter now so Phase 9 can wrap it with decorators. No GPIO or real hardware.

```python
class ActuatorPort(ABC):
    @abstractmethod
    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        ...

class SimulationActuatorAdapter(ActuatorPort):
    def apply(self, device_id: UUID, command: str, payload: dict) -> None:
        ...  # log or in-memory record only; no physical output
```

Selector can mirror sensors (`device_family` / `protocol`). A unit test or thin demo route that calls `apply` is enough this phase.

**Check:** `ActuatorPort` and `SimulationActuatorAdapter` exist; Phase 9 can import the innermost adapter from `infrastructure/adapters/actuators/simulation.py`.

---

## Step 4 — Persistence and application service

```python
class ReadingRepository:
    def insert(self, reading: Reading) -> Reading: ...
    def list_for_device(self, device_id: UUID, limit: int = 20) -> list[Reading]: ...

class ReadingService:
    def take_reading(self, device_id: UUID) -> ReadingDto: ...
    def list_readings(self, device_id: UUID, limit: int = 20) -> list[ReadingDto]: ...
```

Service: load device (missing → not-found) → select adapter → `port.read()` → persist → map DTO.

**Check:** each successful read **appends** a row (history exists, not overwrite-only).

---

## Step 5 — API endpoints

| Method | Path |
|--------|------|
| POST | `/api/sensors/{id}/read` |
| GET | `/api/sensors/{id}/readings?limit=1` |

Response:

```json
{
  "device_id": "<uuid>",
  "value": 0.31,
  "unit": "vwc",
  "source": "simulation",
  "recorded_at": "2026-08-28T09:00:00Z"
}
```

404 if device missing; 400 for adapter/validation failures. Scalar **sensors** tag updates automatically.

**Check:** two POSTs increase row count; Scalar shows the reading schema.

---

## Step 6 — Frontend

Sensor card: “Read now”, latest value, source badge (`simulation` vs `vendor`). Loading and error states. After refresh, show last **DB** reading (optional `GET .../readings?limit=1`). Tailwind conventions from earlier phases.

**Check:** refresh still shows the stored value, not only React state.

---

## Step 7 — Tests

- `test_vendor_adapter_normalizes_raw_payload`
- `test_read_inserts_sensor_reading`

Translation tests should not require HTTP.

```powershell
$env:PYTHONPATH = "src"
pytest tests -q
```

---

## Step 8 — Documentation

`docs/patterns/adapter.md`: problem (incompatible APIs), solution (port + adapters), where in code, extension (third vendor).

---

## Phase 5 completion checklist

- [ ] Table + index applied
- [ ] Two adapters behind `SensorPort`
- [ ] `ActuatorPort` + `SimulationActuatorAdapter` (stub apply; no GPIO)
- [ ] POST read persists a row
- [ ] UI shows value + source from DB
- [ ] Tests + pattern doc

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Autogenerate empty | Import `ReadingRow` / models in `alembic/env.py` |
| Latest reading is slow / wrong | Index `(device_id, recorded_at DESC)` |
| Router imports vendor XML/JSON types | Depend on `SensorPort` only |
| UI loses value on refresh | Persist each read; fetch last row from DB |

---

## Next

→ [Phase 6 — Strategy (requirements)](../phase-06/requirements.md) · [guided check](../phase-06/guided-check.md)
