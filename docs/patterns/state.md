# State — Phase 8

## Problem

An actuator is not a bag of booleans. Before this phase the only hint about an actuator's mode was `default_config.default_state` (`"off"`), which nothing enforced or updated. A real lifecycle needs to answer three questions for every device: what mode is it in, which modes may it move to next, and which commands make sense right now?

Modelling that with flags (`is_running`, `is_fault`, `is_maintenance`) lets impossible combinations exist, duplicates the guard in every caller, and gives the UI nothing reliable to disable buttons with. The smell is **implicit mode with scattered guards**.

## Solution

State makes each mode an object that owns its legal exits and its command vocabulary. The context holds the current state and delegates to it; the application service persists the resulting state name.

| Role | In Phase 8 |
|------|------------|
| **Context** | `ActuatorContext` — holds the current `ActuatorState`, exposes `transition(target)` and `allowed_commands()` |
| **State interface** | `ActuatorState` — `name`, `allowed_targets`, `commands`, `allows()`, `require_transition()`, `allowed_commands()` |
| **Concrete states** | `OffState`, `IdleState`, `RunningState`, `ErrorState`, `MaintenanceState` |
| **Client** | `POST /api/devices/{id}/transition`, the dashboard badges, and the Phase 10 Command invoker |

`state_for(name)` resolves a persisted string to its singleton state object and raises `UnknownActuatorStateError` for anything outside the lifecycle. `ActuatorContext.transition()` resolves the target first, then asks the current state for permission, so an unknown target is a 400 and a known but illegal edge is a 409.

## Legal transitions

| From | Allowed targets | `allowed_commands` |
|------|-----------------|--------------------|
| `off` | `idle`, `error` | `enable` |
| `idle` | `running`, `maintenance`, `off`, `error` | `start_pump`, `set_light_level`, `enter_maintenance`, `shutdown` |
| `running` | `idle`, `error` | `stop_pump` |
| `error` | `idle`, `off` | `reset` |
| `maintenance` | `idle`, `off`, `error` | `exit_maintenance`, `shutdown` |

Self-transitions are rejected: `idle → idle` is not an edge. The command names are the vocabulary Phase 10 reuses; the transition table remains the authoritative lifecycle guard, and Phase 10 checks `allowed_commands` before sending a command to the decorated actuator port. `set_light_level` is in the idle vocabulary because a light can be adjusted while idle; the command layer additionally limits it to `grow_light` devices.

## Where it lives in code

- Domain (pure, no SQLAlchemy or FastAPI): `backend/src/domain/actuators/state.py`, `context.py`, `errors.py`
- Application: `backend/src/application/devices/actuator_state_service.py`
- Persistence: `ActuatorStateRow` in `backend/src/infrastructure/persistence/models.py`, `actuator_state_repository.py`, migration `5e4b7df306db_actuator_states.py`
- API: `backend/src/interfaces/api/devices.py` — `GET /api/devices/{id}` and `POST /api/devices/{id}/transition`
- UI: `frontend/src/components/devices/DeviceList.tsx` — state badge with a tooltip listing legal commands
- Tests: `backend/tests/test_actuator_state.py`

## Design decisions

- **Persistence:** a dedicated `actuator_states` table keyed by `device_id` (PK, FK → `devices`, `ON DELETE CASCADE`). One row per actuator; `updated_at` is refreshed on every saved transition.
- **Seeding:** the migration inserts `idle` for every existing `role='actuator'` row. `DeviceRepository.save_devices()` inserts `idle` for newly provisioned actuators in the same transaction, so the invariant holds for both old and new data.
- **Reads:** `DeviceRepository.list_devices()` and `get_device()` left-join `actuator_states`, so one query returns devices with their state instead of issuing a query per device. Sensors return `state: null` and `allowed_commands: []`.
- **Guarding before saving:** `ActuatorContext` mutates only in-memory state. `ActuatorStateService` calls `save_state()` only after the guard passes, so a rejected transition leaves the row untouched.
- **HTTP mapping:** 404 for a missing device or a sensor passed to the transition endpoint, 400 for an unknown target state, 409 for an illegal edge.
- **UI:** React renders `state` and `allowed_commands` from the API. It does not contain a transition table or infer legality from the state string.

## Known limitations

- `allowed_commands` is a shared lifecycle vocabulary, so it includes pump and light command names for every actuator. Phase 10 commands check device type separately: `start_pump`/`stop_pump` require a `water_pump`, and `set_light_level` requires a `grow_light`.
- There is no optimistic concurrency check: two simultaneous transitions can both read `idle` and the last write wins. A production system would compare `updated_at` or lock the row; the assignment does not require it.
- The demo transition endpoint remains for Phase 8 compatibility. Phase 10 routes normal actuator actions through Command; the command path checks `allowed_commands` and saves the resulting state.

## Add-a-state exercise

To add `calibrating`, for example:

1. Add `CalibratingState` in `domain/actuators/state.py` with its allowed targets and commands, and register it in `_STATES`.
2. Add the edges other states need in their `allowed_targets`.
3. No repository, API, or React change is needed: `state_for`, the DTO mapper, and the badge read the domain set. The database column accepts the new string without a migration.
4. Add the new edges to the table above and to the domain tests.
