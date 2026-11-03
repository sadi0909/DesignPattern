# Phase 6 — Strategy (Guided check)

Complete the [requirements](requirements.md) first. Use this document if you are stuck or to check signatures and JSON. Snippets are **not** a complete solution.

## Pattern

**Strategy** — pluggable `decide(context)` algorithms.

---

## Target layout

```text
domain/automation/
  strategy.py          # AutomationStrategy + Conservative / Aggressive
  context.py           # LocationAutomationContext
application/automation/
  dto.py
  service.py
infrastructure/persistence/
  models.py            # AutomationRuleRow OR extra columns on LocationRow
  automation_repository.py
interfaces/api/automation.py
frontend/.../StrategyPanel.tsx
```

---

## Step 1 — Persistence of strategy choice

Preferred table:

```text
automation_rules(
  id,
  location_id UNIQUE FK → locations,
  strategy_key,          # conservative | aggressive
  parameters JSONB,
  updated_at
)
```

Alternatively: `strategy_key` + `parameters` on `locations`. Document your choice. No `greenhouse_id`.

```powershell
alembic revision --autogenerate -m "automation_rules"
alembic upgrade head
```

**Check:** upserting a key updates persisted data; one active strategy per `location_id`.

---

## Step 2 — Strategy domain

```python
class AutomationStrategy(ABC):
    key: str
    def decide(self, context: LocationAutomationContext) -> Recommendation:
        ...

class ConservativeMoistureStrategy(AutomationStrategy): ...
class AggressiveMoistureStrategy(AutomationStrategy): ...

def get_strategy(key: str) -> AutomationStrategy:
    ...  # unknown key → error before decide()
```

`LocationAutomationContext`: `location_id`, latest moisture (and optional light), zone `low`/`high`.

`Recommendation`: `action` (e.g. `irrigate` | `wait`), `reason`, optional `score`.

**Check:** same context, different keys → observably different recommendations (encode that in tests).

---

## Step 3 — Application orchestration

```python
class AutomationService:
    def set_strategy(self, location_id: UUID, strategy_key: str) -> None: ...
    def evaluate(self, location_id: UUID) -> RecommendationDto:
        # 1. load location / 404
        # 2. load persisted strategy_key
        # 3. latest moisture from sensor_readings (not ORM rows into decide)
        # 4. zone thresholds for location_id
        # 5. context = LocationAutomationContext(...)
        # 6. get_strategy(key).decide(context)
        ...
```

Do **not** pass `DeviceRow` / `ZoneRow` into strategy classes. Thresholds come from `zones`, not hardcoded constants.

**Check:** strategies import no SQLAlchemy; missing location → not-found style error.

---

## Step 4 — API

| Method | Path |
|--------|------|
| PUT | `/api/locations/{location_id}/automation` body `{ "strategy_key": "conservative" }` |
| POST | `/api/locations/{location_id}/automation/evaluate` |

Evaluate uses the **persisted** key (query override is optional extra). 400 unknown key; 404 missing location.

Evaluate response:

```json
{
  "location_id": "<uuid>",
  "strategy_key": "conservative",
  "action": "wait",
  "reason": "Moisture 0.40 is within 0.25–0.45"
}
```

**Check:** Scalar shows schemas; evaluate after PUT uses the saved key.

---

## Step 5 — Frontend

`#automation`: `<select>` of keys, Save, Evaluate, result card (action + reason). Tailwind; error/success states.

**Check:** change strategy → next evaluate differs for the same moisture (take a read or seed first).

---

## Step 6 — Tests and docs

- `test_conservative_waits_when_within_band`
- `test_aggressive_differs_on_same_context`
- Optional integration with seeded readings + zones
- `docs/patterns/strategy.md`: problem, interface, where in code, add-a-third-strategy exercise

```powershell
$env:PYTHONPATH = "src"
pytest tests -q
```

---

## Phase 6 completion checklist

- [ ] Strategy key persisted per location
- [ ] Two algorithms behind one interface
- [ ] Evaluate uses DB readings + zone thresholds
- [ ] UI save + evaluate works
- [ ] Tests + pattern doc

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Same recommendation for both keys | Document a moisture band where aggressive acts sooner |
| `if strategy ==` in the router | Lookup `get_strategy(key)` / polymorphism |
| Thresholds ignored | Load `zones` for `location_id`, not constants |
| Evaluate ignores dropdown | Persist key first; evaluate reads DB |

---

## Next

→ [Phase 7 — Facade (requirements)](../phase-07/requirements.md) · [guided check](../phase-07/guided-check.md)
