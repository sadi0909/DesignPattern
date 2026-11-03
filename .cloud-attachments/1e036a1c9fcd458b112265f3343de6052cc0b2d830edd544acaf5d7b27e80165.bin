# Phase 8 — State (Guided check)

Complete the [requirements](requirements.md) first. Use this document if you are stuck or to check signatures and JSON. Snippets are **not** a complete solution.

## Pattern

**State** — guarded transitions per actuator.

---

## Target layout

```text
domain/actuators/
  state.py              # ActuatorState, transition table or state objects
  context.py            # ActuatorContext
infrastructure/persistence/
  models.py             # ActuatorStateRow
  actuator_state_repository.py
application/devices/dto.py   # + state, allowed_commands
```

---

## Step 1 — Database

```text
actuator_states(
  device_id PK FK → devices,
  state VARCHAR,          # off | idle | running | error | maintenance
  updated_at
)
```

Seed: `INSERT` idle for existing `role='actuator'` (in migration `upgrade()` or a follow-up). Document which.

```powershell
alembic revision --autogenerate -m "actuator_states"
alembic upgrade head
```

**Check:** every actuator row can resolve a state.

---

## Step 2 — Domain transitions

```python
ALLOWED: dict[str, set[str]] = {
    "idle": {"running", "maintenance", "error", "off"},
    "running": {"idle", "error"},
    ...
}

class ActuatorContext:
    def transition(self, target: str) -> None:
        ...  # raise IllegalTransitionError if target not allowed

    def allowed_commands(self) -> list[str]:
        ...  # e.g. idle → ["start_pump"]; running → ["stop_pump"]
```

Prefer state objects if you want a fuller State pattern; a table is acceptable if each state still encapsulates allowed commands. Write legal edges in `docs/patterns/state.md`.

**Check:** illegal transition raises a domain error; unit tests cover legal and illegal edges.

---

## Step 3 — Persistence and API

Load/save state on transition (not only in-process memory). Device list/detail DTO gains:

```json
{
  "id": "<uuid>",
  "role": "actuator",
  "state": "idle",
  "allowed_commands": ["start_pump"]
}
```

Optional demo: `POST /api/devices/{id}/transition` `{ "target": "running" }` → 409/400 if illegal; 404 missing actuator. Phase 10 will go through Command.

**Check:** Scalar shows the new fields; restart backend — states still correct.

---

## Step 4 — Frontend

Badge colors: idle = slate, running = emerald, error = red, maintenance = amber. Tooltip lists allowed commands. Full control buttons can wait until Phase 10.

**Check:** overview or devices section shows updated state after a successful transition.

---

## Step 5 — Tests and docs

- `test_idle_to_running_allowed`
- `test_running_to_maintenance_rejected` (if that is illegal in your table)
- `test_illegal_transition_does_not_update_row`
- `docs/patterns/state.md`

```powershell
$env:PYTHONPATH = "src"
pytest tests -q
```

---

## Phase 8 completion checklist

- [ ] `actuator_states` populated
- [ ] Domain guards transitions
- [ ] API exposes `state` + `allowed_commands`
- [ ] UI badges work
- [ ] Tests + pattern doc

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| State lost on restart | Persist `actuator_states`; do not keep it only in FastAPI memory |
| Illegal edge succeeds | Encode the table; raise before save |
| Transition logic in React | Domain owns guards; UI only displays `allowed_commands` |

---

## Next

→ [Phase 9 — Decorator (requirements)](../phase-09/requirements.md) · [guided check](../phase-09/guided-check.md)
