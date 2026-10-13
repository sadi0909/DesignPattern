# Strategy — Phase 6

## Problem

Irrigation policy is a choice, not a fixed rule. A conservative grower waits until moisture is clearly low; an aggressive one tops up earlier. If that choice lives as `if strategy == "conservative": ... elif strategy == "aggressive": ...` inside the service or the HTTP router, every new policy edits the same hotspot, and tests must cover every branch combination. The smell is **algorithm and selection logic fused together**.

## Solution

Strategy defines a family of interchangeable algorithms behind one interface. The client picks one; the context runs it without knowing which one it is.

| Role | In Phase 6 |
|------|------------|
| **Strategy** | `AutomationStrategy.decide(context) -> Recommendation` |
| **Concrete strategies** | `ConservativeMoistureStrategy` (`"conservative"`), `AggressiveMoistureStrategy` (`"aggressive"`) |
| **Context (plain input)** | `LocationAutomationContext`: `location_id`, `zone_name`, `moisture`, `moisture_low`, `moisture_high` (all 0–1 fractions) |
| **Context user / client** | `AutomationService.evaluate()`, which loads the persisted key and builds one context per zone |

Choosing a strategy (`get_strategy(key)`) is separate from running it (`decide`). An unknown key raises `UnknownStrategyError` before any `decide()` call or database write.

### The difference the two strategies make

Both strategies see the same moisture and the same zone band. They differ in the band between the thresholds:

| Zone band | Moisture | Conservative | Aggressive |
|-----------|----------|--------------|------------|
| 0.25–0.45 | 0.40 | **wait** (within the band) | **irrigate** (below the high threshold) |
| 0.25–0.45 | 0.20 | irrigate (below low) | irrigate (below high) |
| 0.25–0.45 | 0.50 | wait (above high) | wait (above high) |

## Where it lives in code

- Domain (pure, no SQLAlchemy/FastAPI): `backend/src/domain/automation/strategy.py` (interface, both strategies, `get_strategy`), `context.py`, `rule.py`, `errors.py`
- Application: `backend/src/application/automation/service.py` (load key → build contexts from zones and the latest moisture reading → `decide`) and `dto.py`
- Persistence: `AutomationRuleRow` in `backend/src/infrastructure/persistence/models.py` (table `automation_rules`, one row per `location_id`, unique FK → `locations`), `automation_repository.py`, migration `a1c3e9f07b2d_automation_rules.py`
- API: `backend/src/interfaces/api/automation.py` — `GET` and `PUT /api/locations/{location_id}/automation`, `POST .../automation/evaluate`
- UI: `frontend/src/features/automation/StrategyPanel.tsx` (mounted in `#automation`)
- Tests: `backend/tests/test_automation.py`

## Design decisions

- **Persistence:** a dedicated `automation_rules` table (not columns on `locations`). `location_id` is unique, so each location has exactly one active strategy. Saving an existing location updates its row in place.
- **Thresholds come from `zones`**, never from constants in a strategy class.
- **Evaluation uses the saved key.** The client cannot override it per request. A location with no saved rule uses `conservative` and the response says `is_default`.
- **Units:** sensors report moisture in percent (0–100); thresholds are fractions (0–1). The service converts once, when it builds the context, so strategies only ever see fractions.
- **Multiple zones:** each zone gets its own decision. The location irrigates if any zone asks for water; the reason names that zone.
- **Recommend, don't act:** `decide` returns `irrigate` or `wait`. It never drives a pump. Carrying out the action is Command (Phase 10) on top of actuators.

## Known limitation

Devices are not yet bound to a location (no `location_id` on `devices`), so the "latest moisture" is the newest reading across all moisture sensors. Binding sensors to locations is the natural next step, and the service method that loads the reading is the only place that would change.

## Add-a-third-strategy exercise

Add `FrugalMoistureStrategy` that irrigates only when moisture is below the low threshold **and** the reading is at least 30 minutes old (to avoid watering right after a manual top-up). Steps:

1. Write the class in `domain/automation/strategy.py` with `key = "frugal"` and a `decide` method. Extend `LocationAutomationContext` only if it needs the reading time.
2. Add it to the `_STRATEGIES` tuple. It appears in `available_strategies` and the dropdown with no other changes.
3. Add a unit test next to the others showing it differs from the two existing strategies.

If the router or the service needs an `if key == "frugal"` branch, the design has leaked: move that logic into the strategy.
