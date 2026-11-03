# Phase 2 — Factory Method (Guided check)

Complete the [requirements](requirements.md) first. Use this document if you are stuck or to check signatures, layout, and JSON. Snippets are **not** a complete solution.

**Time estimate:** 3–5 hours.

## Pattern

**Factory Method** — creator interface (`create_sensor`); concrete creators choose type and defaults. Callers depend on the abstract creator, not `MoistureSensor(...)` in HTTP handlers.

---

## Target repository layout (end state)

Paths are relative to **`yourpath\project\`** (replace with your clone path).

```text
yourpath\project\
├── backend/
│   ├── alembic/versions/
│   │   ├── 001_baseline.py
│   │   └── <rev>_devices.py        # NEW — autogenerate
│   └── src/
│       ├── domain/sensors/
│       │   ├── entity.py
│       │   └── creators.py
│       ├── application/sensors/service.py
│       ├── infrastructure/persistence/
│       │   ├── base.py
│       │   ├── models.py
│       │   └── device_repository.py
│       └── interfaces/api/sensors.py
└── frontend/src/
    ├── services/api.ts
    └── features/sensors/SensorList.tsx
```

---

## Step 0 — Working Phase 1 stack

```powershell
cd "yourpath\project\"
docker compose up -d
```

Backend: venv → `cd src` → `uvicorn main:app --reload --port 8000`. Frontend: `npm run dev`. Confirm dashboard and Scalar before changing code.

---

## Step 1 — Persistence layer (before migration)

**`base.py`**

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

**`DeviceRow`** — columns to include (write the mapped types yourself):

| Column | Notes |
|--------|--------|
| `id` | UUID PK, `gen_random_uuid()` server default |
| `device_type` | String(64), not null |
| `role` | String(32), default `"sensor"` |
| `display_name` | String(128), nullable |
| `default_config` | JSONB, default `{}` |
| `created_at` | timestamptz, `now()` |
| Index | `ix_devices_role` on `role` |

**Alembic `env.py`** — replace `target_metadata = None` with `Base.metadata`, and import `models` so autogenerate is not empty.

**`get_db`** — yield a `SessionLocal()` and close it in `finally`.

---

## Step 2 — Autogenerate

From `yourpath\project\backend\` with venv active (not `src/`):

```powershell
alembic revision --autogenerate -m "devices"
```

Review: `down_revision` is Phase 1 id; `upgrade()` contains `op.create_table("devices", ...)`. If `upgrade()` is `pass` only, metadata is not wired — delete the file and regenerate.

```powershell
alembic upgrade head
docker exec -it greenhouse-postgres psql -U greenhouse -d greenhouse -c "\d devices"
```

Discipline for later phases: change models → autogenerate → review → upgrade. Never edit applied revisions.

---

## Step 3 — Domain + Factory Method

**`Sensor`** fields: `id: UUID | None`, `device_type`, `display_name`, `default_config`.

Creator surface you should have:

```python
class SensorCreator(ABC):
    @abstractmethod
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        ...

class MoistureSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        ...  # device_type="moisture_sensor"; config includes unit/threshold/interval

class LightSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        ...  # device_type="light_sensor"; different unit/interval

def get_creator(sensor_type: str) -> SensorCreator:
    ...  # registry: "moisture" | "light"; unknown → ValueError
```

**Check:** moisture vs light defaults are not the same dict.

---

## Step 4 — Repository + service

```python
class DeviceRepository:
    def save_sensor(self, sensor: Sensor) -> Sensor: ...
    def list_sensors(self) -> list[Sensor]: ...  # role == "sensor"

class SensorService:
    def create_sensor(self, sensor_type: str, display_name: str | None = None) -> Sensor:
        creator = get_creator(sensor_type)
        prototype = creator.create_sensor(display_name=display_name)
        return self._repo.save_sensor(prototype)

    def list_sensors(self) -> list[Sensor]:
        ...
```

**Check:** `commit()` happens; id is populated after save.

---

## Step 5 — REST

Prefix `/api/sensors`, tags `["sensors"]`.

Request: `{ "type": "moisture" | "light", "display_name": string | null }`

Response:

```json
{
  "id": "<uuid>",
  "device_type": "moisture_sensor",
  "display_name": "Soil moisture sensor",
  "default_config": { "sampling_interval_seconds": 300, "unit": "vwc" }
}
```

`POST` → 201; unknown type → 400. `include_router` in `main.py`.

```powershell
curl http://localhost:8000/api/sensors
curl -X POST http://localhost:8000/api/sensors -H "Content-Type: application/json" -d "{\"type\":\"moisture\"}"
```

**Check:** Scalar **sensors** tag; GET still returns rows after restart.

---

## Step 6 — Frontend

`api.ts` types/functions: `SensorDto`, `fetchSensors()`, `createSensor(type, displayName?)`.

`SensorList` responsibilities: load on mount, buttons for moisture/light, error banner, empty state, list with name + type + config. Mount in `#sensors`; leave other placeholders.

**Check:** add both types, refresh, both still listed.

---

## Step 7 — Tests (names, not full files)

- `test_moisture_creator_defaults` — type `moisture_sensor`; threshold key present
- `test_light_creator_defaults` — type `light_sensor`; unit differs
- Optional API test for GET/POST

```powershell
$env:PYTHONPATH = "src"
pytest tests -q
```

---

## Step 8 — Pattern doc

`docs/patterns/factory-method.md`: problem, solution, code paths, exercise (temperature creator).

---

## Phase 2 completion checklist

- [ ] Autogenerate reviewed and applied
- [ ] `\d devices` shows expected columns
- [ ] POST moisture/light → 201 with distinct `default_config`
- [ ] GET persists across restart
- [ ] Scalar sensors tag
- [ ] Dashboard Sensors section works
- [ ] Creator tests pass
- [ ] Pattern doc written

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Empty autogenerate | Import `Base` + `models` in `env.py` |
| `relation "devices" does not exist` | `alembic upgrade head` from `backend/` |
| 404 on `/api/sensors` | `include_router` |
| Empty list after create | `commit()` in repository |
| Test import errors | `PYTHONPATH=src` |

---

## Non-goals

`device_family`, actuators, live readings, locations/zones.

---

## Next

→ [Phase 3 — Abstract Factory (requirements)](../phase-03/requirements.md) · [guided check](../phase-03/guided-check.md)
