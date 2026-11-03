# Phase 4 — Builder (Guided check)

Complete the [requirements](requirements.md) first. Use this document if you are stuck or to check signatures, layout, and JSON. Snippets are **not** a complete solution.

**Time estimate:** 4–6 hours.

## Pattern

**Builder** — construct a complex `LocationConfig` incrementally; `build()` validates and returns an immutable result (or raises `ConfigurationError`).

**Naming:** `locations` / `location_id` — not `greenhouses` / `greenhouse_id`.

```text
LocationConfigBuilder → LocationConfig (domain)
       ↓ build()
LocationRepository → LocationRow + ZoneRow (ORM)
       ↓
LocationConfigDto (API)
```

---

## Target repository layout (end state)

```text
backend/src/
├── domain/locations/
│   ├── entity.py               # Location, Zone, LocationConfig
│   ├── config_builder.py
│   └── errors.py               # ConfigurationError
├── application/locations/
│   ├── dto.py
│   ├── mappers.py
│   └── config_service.py
├── infrastructure/persistence/
│   ├── models.py               # LocationRow, ZoneRow
│   └── location_repository.py
└── interfaces/api/locations.py
frontend/src/components/config/LocationConfigWizard.tsx
```

---

## Step 0 — Phase 3 baseline

```powershell
docker compose up -d
cd backend
.\.venv\Scripts\Activate.ps1
alembic current
```

Confirm `/api/devices` and dashboard families still work.

---

## Step 1–2 — ORM + migration

**`LocationRow`:** `id` (UUID), `name`, `created_at`; relationship to zones.

**`ZoneRow`:** `id`, **`location_id`** FK → `locations.id` (`ondelete="CASCADE"`), `name`, `moisture_threshold_low/high` (numeric), `schedule` (JSONB). Index `ix_zones_location_id`.

Optional: nullable `devices.location_id` FK.

```powershell
alembic revision --autogenerate -m "locations_and_zones"
alembic upgrade head
```

**Check:** `\d zones` shows **`location_id`**, not `greenhouse_id`.

---

## Step 3 — Domain + Builder (signatures)

```python
class ConfigurationError(ValueError): ...

class LocationConfigBuilder:
    def with_location_name(self, name: str) -> "LocationConfigBuilder": ...
    def add_zone(
        self,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict | None = None,
    ) -> "LocationConfigBuilder": ...
    def build(self) -> LocationConfig:
        ...  # reject empty name, zero zones, low >= high, thresholds outside 0–1
```

**Check:** invalid configs never reach the repository.

---

## Step 4 — DTOs

Request: `location_name` + `zones[]` with `name`, `moisture_threshold_low/high`, `schedule`.

Response: `location: { id, name }` + `zones[]` each including **`location_id`**.

Domain entities stay separate from Pydantic models.

---

## Step 5 — Repository + service

```python
class LocationRepository:
    def save_config(self, config: LocationConfig) -> tuple[LocationRow, list[ZoneRow]]:
        ...  # flush location id, insert zones, one commit

    def get_config(self, location_id) -> tuple[LocationRow, list[ZoneRow]] | None:
        ...

class LocationConfigService:
    def build_and_save(self, request: BuildLocationConfigRequestDto) -> LocationConfigDto:
        builder = LocationConfigBuilder().with_location_name(request.location_name)
        for z in request.zones:
            builder.add_zone(...)
        config = builder.build()
        loc_row, zone_rows = self._repo.save_config(config)
        return location_config_to_dto(...)
```

**Check:** failed save does not leave a location without zones.

---

## Step 6 — REST

Prefix `/api/locations`, tags `["locations"]`.

| Method | Path | Status |
|--------|------|--------|
| POST | `/config` | 201 |
| GET | `/{location_id}/config` | 200 / 404 |

Validation errors → 400.

Example create body:

```json
{
  "location_name": "Lab Site A",
  "zones": [
    {
      "name": "Bench 1",
      "moisture_threshold_low": 0.2,
      "moisture_threshold_high": 0.45,
      "schedule": { "watering": "08:00" }
    }
  ]
}
```

**Check:** Scalar **locations** tag; every zone in the response has `location_id`.

---

## Step 7 — Frontend wizard

Mount in `#config`. Collect location name + dynamic zone list; POST create; show returned id and zones. Inline validation + API error banner. Tailwind cards from earlier phases.

Types in `api.ts` must match JSON keys (`location_id`, not `greenhouse_id`).

---

## Step 8 — Tests (names)

- `test_build_success`
- `test_build_requires_name` / `test_build_requires_zones`
- `test_build_rejects_invalid_thresholds`
- Optional API: POST 201 + GET structure with `location_id`

```powershell
$env:PYTHONPATH = "src"
pytest tests -q
```

---

## Step 9 — Pattern doc

`docs/patterns/builder.md`: problem, fluent `build()`, vs Factory Method / Abstract Factory, `location_id` naming, extension idea.

---

## Phase 4 completion checklist

- [ ] `locations` + `zones`; FK `zones.location_id`
- [ ] Builder validates before persist
- [ ] POST/GET location config live in Scalar
- [ ] Wizard creates and displays config
- [ ] Builder tests pass
- [ ] Pattern doc written

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Autogenerate empty | Import new models in `env.py` |
| `greenhouse_id` in migration | Rename models; regenerate |
| 400 on POST | Read `detail` — thresholds or empty zones |
| Zones missing on GET | Load relationship after commit |

---

## Non-goals

Assigning every device to a location; strategy execution (Phase 6); edit/delete UI (stretch).

---

## Next

→ [Phase 5 — Adapter (requirements)](../phase-05/requirements.md) · [guided check](../phase-05/guided-check.md)
