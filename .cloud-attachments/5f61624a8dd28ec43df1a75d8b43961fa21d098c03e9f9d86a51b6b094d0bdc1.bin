# Phase 3 — Abstract Factory (Guided check)

Complete the [requirements](requirements.md) first. Use this document if you are stuck or to check signatures, layout, and JSON. Snippets are **not** a complete solution.

**Time estimate:** 4–6 hours.

## Pattern

**Abstract Factory** — `DeviceFamilyFactory.create_device_set()`; `SimulationDeviceFactory` and `EdgeHardwareFactory` each return a compatible kit.

Layering:

```text
DeviceRow (ORM)  ↔  Device (domain)  ↔  DeviceDto (API)
```

---

## Target repository layout (end state)

```text
backend/src/
├── domain/devices/
│   ├── entity.py              # Device
│   └── family_factory.py      # Abstract Factory
├── application/devices/
│   ├── dto.py
│   ├── mappers.py
│   └── family_service.py
├── infrastructure/persistence/
│   ├── models.py              # + device_family
│   └── device_repository.py
└── interfaces/api/devices.py
frontend/src/components/devices/
├── DeviceFamilySwitcher.tsx
└── DeviceList.tsx
```

Keep Phase 2 `domain/sensors/creators.py`.

---

## Step 0 — Phase 2 baseline

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
alembic current
```

Note head revision id — Phase 3 autogenerate must use it as `down_revision`. Confirm sensors still load.

---

## Step 1–2 — ORM + migration

Add on `DeviceRow`:

```python
device_family: Mapped[str]  # String(32), nullable=False, server_default="simulation"
# Index ix_devices_family
```

```powershell
alembic revision --autogenerate -m "device_family"
```

**Check:** `upgrade()` adds `device_family` (and index). If existing rows need backfill:

```python
op.execute("UPDATE devices SET device_family = 'simulation' WHERE device_family IS NULL")
```

```powershell
alembic upgrade head
```

`\d devices` shows `device_family`.

---

## Step 3 — Domain `Device`

```python
@dataclass(frozen=True)
class Device:
    id: UUID | None
    device_type: str
    role: str          # "sensor" | "actuator"
    device_family: str
    display_name: str
    default_config: dict
```

Keep `Sensor` for Phase 2 compatibility or map in the repository.

---

## Step 4 — Abstract Factory (signatures)

```python
class DeviceFamilyFactory(ABC):
    @property
    @abstractmethod
    def family_key(self) -> str: ...

    @abstractmethod
    def create_device_set(self) -> list[Device]: ...

class SimulationDeviceFactory(DeviceFamilyFactory):
    def create_device_set(self) -> list[Device]:
        ...  # 2 sensors via Moisture/Light creators + pump + grow light; family_key "simulation"

class EdgeHardwareFactory(DeviceFamilyFactory):
    def create_device_set(self) -> list[Device]:
        ...  # same shape, different labels/protocol (e.g. gpio-stub vs sim)

def get_family_factory(family: str) -> DeviceFamilyFactory:
    ...  # "simulation" | "edge"
```

**Check:** four devices; both roles; simulation `protocol` ≠ edge `protocol`. Do not paste a full factory — compose Phase 2 creators, then convert sensor → `Device` with `role="sensor"`.

---

## Step 5 — Repository, service, DTOs

```python
class DeviceRepository:
    def save_device(self, device: Device) -> Device: ...
    def save_devices(self, devices: list[Device]) -> list[Device]: ...
    def list_devices(self, *, device_family: str | None = None, role: str | None = None) -> list[Device]: ...

class DeviceFamilyService:
    def provision_family(self, family: str) -> list[Device]:
        factory = get_family_factory(family)
        return self._repo.save_devices(factory.create_device_set())

    def list_devices(self, **filters) -> list[Device]: ...
```

DTO fields: `id`, `device_type`, `role`, `device_family`, `display_name`, `default_config`.

```python
def device_to_dto(device: Device) -> DeviceDto:
    ...  # reject unpersisted id is None

def devices_to_dtos(devices: list[Device]) -> list[DeviceDto]:
    ...
```

**Rules:** factory/repo never import `DeviceDto`. Router maps once per handler.

---

## Step 6 — REST

Prefix `/api/devices`, tags `["devices"]`.

| Method | Path | Notes |
|--------|------|--------|
| GET | `/api/devices` | Query: `family`, `role` |
| POST | `/api/devices/provision` | Query: `family` required; 201 |

Response item:

```json
{
  "id": "<uuid>",
  "device_type": "water_pump",
  "role": "actuator",
  "device_family": "simulation",
  "display_name": "Sim irrigation pump",
  "default_config": { "protocol": "sim" }
}
```

Unknown family → 400. `include_router` in `main.py`.

```powershell
curl -X POST "http://localhost:8000/api/devices/provision?family=simulation"
curl "http://localhost:8000/api/devices?family=simulation"
```

**Check:** 4 rows per provision; Scalar **devices** schema matches TypeScript.

---

## Step 7 — Frontend

`api.ts`: `DeviceDto`, `DeviceFamily = "simulation" | "edge"`, `fetchDevices({ family, role })`, `provisionDeviceFamily(family)`.

Switcher: two buttons, selected family in local state. List: role badge (sensor vs actuator) + family badge. Provision reloads. Mount `#devices` (keep `#sensors`).

**Check:** simulation kit vs edge kit; refresh persists.

---

## Step 8 — Tests (names)

- `test_simulation_factory_returns_four_devices`
- `test_edge_factory_differs_from_simulation`
- Optional: POST provision 201 length 4

```powershell
$env:PYTHONPATH = "src"
pytest tests -q
```

---

## Step 9 — Pattern doc

`docs/patterns/abstract-factory.md`: problem, solution, vs Factory Method, DTO note, third-family exercise.

---

## Phase 3 completion checklist

- [ ] `device_family` column applied
- [ ] Provision simulation and edge each create 4 devices
- [ ] GET `?family=` filters
- [ ] DTO + mappers used by router
- [ ] Scalar + TS types aligned
- [ ] Dashboard family switcher works
- [ ] Factory tests pass
- [ ] Pattern doc written

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Empty autogenerate | Import models in `env.py` |
| Sensors missing family | Backfill / server default |
| Validation error on `role` | Only `"sensor"` / `"actuator"` |
| UI mixes families | Pass `family` on every list fetch |

---

## Non-goals

Real GPIO drivers (Phase 5), location Builder (Phase 4), running actuators (Phases 8–10).

---

## Next

→ [Phase 4 — Builder (requirements)](../phase-04/requirements.md) · [guided check](../phase-04/guided-check.md)
