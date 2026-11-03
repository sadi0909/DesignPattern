# Phase 7 — Facade (Guided check)

Complete the [requirements](requirements.md) first. Use this document if you are stuck or to check signatures and JSON. Snippets are **not** a complete solution.

## Pattern

**Facade** — one entry point over subsystems.

---

## Target layout

```text
application/overview/
  dto.py                 # LocationOverviewDto
  facade.py              # LocationOverviewFacade
interfaces/api/overview.py
frontend/.../OverviewPage.tsx   # or section in DashboardPage
```

---

## Step 1 — Overview DTO contract

```python
class LocationOverviewDto(BaseModel):  # or equivalent
    location: LocationSummaryDto       # id, name
    device_counts: dict[str, int]      # e.g. sensor, actuator
    latest_readings: list[ReadingSummaryDto]
    strategy_key: str | None
    last_recommendation: RecommendationDto | None
```

JSON field names must stay stable and match Scalar.

**Check:** missing `location_id` → 404 at the API (wired in Step 4).

---

## Step 2 — Facade implementation

```python
class LocationOverviewFacade:
    def get_overview(self, location_id: UUID) -> LocationOverviewDto:
        # latest readings (join sensor_readings)
        # device counts by family/role
        # active strategy_key
        # last recommendation — delegate to automation service, do not re-implement Strategy
        ...
```

Router injects **only** the facade — not `DeviceRepository`, `ReadingRepository`, and `AutomationService` together.

Watch N+1: a small number of queries (devices, latest readings, rules) — not a query per device in a Python loop without comment.

**Check:** after a new reading or strategy change, overview reflects DB state without extra React glue.

---

## Step 3 — Database

**No migration required.** Optional view `location_overview_v1` (prefer location terminology). If you skip the view, document that existing tables are enough.

**Check:** Phase 6 schema unchanged unless you added an optional view revision.

---

## Step 4 — API and frontend

`GET /api/locations/{location_id}/overview`

Example response:

```json
{
  "location": { "id": "<uuid>", "name": "Lab Site A" },
  "device_counts": { "sensor": 2, "actuator": 2 },
  "latest_readings": [
    { "device_id": "<uuid>", "value": 0.31, "unit": "vwc", "recorded_at": "..." }
  ],
  "strategy_key": "conservative",
  "last_recommendation": { "action": "wait", "reason": "..." }
}
```

`#overview`: one `fetchOverview(locationId)`; cards for counts, readings, strategy, recommendation. Optional refresh button.

**Check:** Scalar shows the schema; one fetch on load.

---

## Step 5 — Tests and docs

- `test_overview_returns_strategy_and_readings`
- `docs/patterns/facade.md`: why one entry point, what it hides, N+1 note

---

## Phase 7 completion checklist

- [ ] Single overview endpoint + UI
- [ ] Handler uses only the facade
- [ ] No required new tables
- [ ] Tests + pattern doc

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Router lists five Depends(...) | Inject the facade only |
| Overview stale after a read | Facade must query DB (or evaluate) each GET |
| Many queries per device | Join / window for latest readings |
| Scoped by greenhouse id | Use `location_id` |

---

## Next

→ [Phase 8 — State (requirements)](../phase-08/requirements.md) · [guided check](../phase-08/guided-check.md)
