# Command — Phase 10

## Problem

Before this phase the dashboard had a temporary `POST /api/actuators/{id}/apply` route that sent a string straight to the decorated actuator port. That is useful for exercising policies, but it is not an operator action: it does not check the Phase 8 lifecycle, it can change hardware without changing `actuator_states`, and it has no durable record of *why* the operator asked for the action.

Changing a pump from the UI should mean “start this pump”, not “run this adapter method”. The request needs to survive as a value — with its device, command type and payload — so it can be checked, queued, logged and audited. Calling `adapter.apply()` directly throws that information away. The smell is **an ephemeral request with no auditable intent**.

## Solution

Command turns each actuator request into an object with an `execute()` method. A registry maps the wire `command_type` to a command class, so the HTTP layer and invoker do not grow a `if command_type == ...` ladder for every device action.

| Role | In Phase 10 |
|------|-------------|
| **Command** | `Command` in `domain/commands/base.py`; `StartPumpCommand`, `StopPumpCommand`, `SetLightLevelCommand` |
| **Receiver** | The decorated `ActuatorPort` changes the hardware/simulation; `ActuatorContext` owns the lifecycle transition |
| **Invoker** | `CommandService.submit()` — resolves the command object, guards it, calls the port, advances state, and writes the audit row |
| **Client** | `POST /api/commands` (or the `/api/devices/{id}/commands` alias) and the dashboard controls |

The concrete command classes are small because the payload and command name are the important state. `StartPumpCommand` maps to `running`, `StopPumpCommand` maps to `idle`, and `SetLightLevelCommand` has no lifecycle target; it changes the light level while the light remains in its current lifecycle state. `SetLightLevelCommand` validates that `payload.level` is a number from 0 to 100.

The device-type guard is deliberately separate from the lifecycle guard. A pump is allowed to start only on a `water_pump`, and a light level is accepted only on a `grow_light`. The state machine is shared, but it should not make a pump pretend it has a lamp.

## Execute path

```text
POST /api/commands
  └── CommandService.submit(device_id, command_type, payload)
        1. create the command through the registry
        2. load an actuator and its persisted state
        3. reject if the command does not support this device type
        4. reject if command_type is not in allowed_commands
        5. reject if the mapped target transition is illegal
        6. command.execute(port, device_id)
             └── LoggingActuatorDecorator
                   └── MaxRunTimeActuatorDecorator
                         └── SimulationActuatorAdapter
        7. on success, transition the context and save actuator_states
        8. insert command_log: success or failed
```

A rejected request stops at step 4 or 5. It writes `command_log` with `status=rejected` and then returns HTTP 409. It does **not** call the decorated port and does **not** save `actuator_states`. This is why a rejected start cannot leave a pump running while the database still says idle.

The invoker intentionally contains no device-specific action logic. `create_command()` is the single type-to-class map; adding a future `stop_all` command means adding a class and one registry entry, not editing the API handler.

## `command_log`

`command_log` is the operator-intent audit, not a copy of the Phase 9 execution log.

| Column | Meaning |
|--------|---------|
| `id` | UUID primary key |
| `command_type` | `start_pump`, `stop_pump` or `set_light_level` |
| `device_id` | FK to `devices`, `ON DELETE CASCADE` |
| `payload` | JSONB, for example `{"level": 65}` |
| `status` | `success`, `failed` or `rejected` |
| `error_message` | guard/policy/adapter reason, or `null` |
| `created_at` | timestamp with time zone |

`CommandLogRepository.record()` commits immediately. That is important for `rejected` and `failed`: the row must survive the exception raised to the API, otherwise the history would hide exactly the attempts operators need to investigate.

### Status meanings

| Status | Written when | Port reached? | State changed? |
|--------|--------------|---------------|----------------|
| `success` | The guard passed, the decorated port completed, and the transition (if any) was saved | Yes | For start/stop |
| `rejected` | The device type or `allowed_commands` guard refused the command | No | No |
| `failed` | The command was accepted, but a decorator or adapter raised | Yes, up to the failure point | No; state is saved only after a successful apply |

A rejected command is not a failed command. “This pump is already running” is a valid lifecycle refusal before execution. “The max-run-time policy blocked this accepted command” is an execution failure after the request entered the port stack. Both belong in `command_log`, but only the latter should also appear as `success=false` in `actuator_execution_log`.

## State and Decorator integration

Phase 8 remains the authority for lifecycle. The command object supplies a target state, while `ActuatorContext` checks whether the current state allows that target. Phase 10 adds `set_light_level` to the idle state’s command vocabulary, but keeps `start_pump` and `stop_pump` as the lifecycle-changing commands.

Phase 9 remains the execution stack. The invoker calls `ActuatorPort`, never `SimulationActuatorAdapter` directly, so logging and max-run-time policy are not bypassed. A decorator failure is caught by `CommandService`, recorded as `failed`, and re-raised. The logging decorator has already recorded the same attempt in `actuator_execution_log`.

`command_log` and `actuator_execution_log` therefore answer different questions:

- `command_log`: what did the operator ask for, and was it accepted?
- `actuator_execution_log`: what actually happened inside the decorated apply, and which policies ran?

A rejected command has a command-log row but no execution-log row. A successful command normally has one row in each. A policy failure has one row in each, with different wording and different status fields.

## HTTP choices

- `POST /api/commands` with `{ "command_type": "...", "device_id": "...", "payload": {} }` executes synchronously and returns the persisted command log.
- `POST /api/devices/{device_id}/commands` is an alias that accepts `{ "command_type": "...", "payload": {} }`; it is convenient for the guided check and uses the same invoker.
- `GET /api/commands?limit=50` returns newest first.
- Unknown command type or invalid light payload → 400.
- Missing device or a sensor passed as an actuator → 404.
- State/device-type rejection or a policy block → 409. This choice is documented here and tested consistently.

## UI

The `#controls` section now uses `CommandPanel`. It fetches actuators and their `allowed_commands`, disables Start pump, Stop pump and Set light level when the current state does not allow them, and also distinguishes pumps from grow lights. After a command it refreshes both the device list and the `command_log` table, so a rejected row is visible without a page reload. `#commands` contains the command-history table with time, device, command, payload, status and error message.

The Phase 9 execution-log panel is now read-only. It remains useful for seeing decorator policy behaviour, but it is no longer an alternate way to trigger actuator actions from the dashboard.

## Where it lives in code

- Command abstraction and errors: `backend/src/domain/commands/base.py`, `errors.py`
- Concrete commands: `backend/src/domain/commands/pump.py`, `light.py`
- Type registry: `backend/src/domain/commands/registry.py`
- Command read model: `backend/src/domain/commands/log.py`
- Invoker/service: `backend/src/application/commands/service.py`
- Request/response DTOs and mapper: `backend/src/application/commands/dto.py`, `mappers.py`
- Persistence: `CommandLogRow` in `backend/src/infrastructure/persistence/models.py`, `command_log_repository.py`, migration `4b66f6de4dcc_command_log.py`
- API: `backend/src/interfaces/api/commands.py`
- UI: `frontend/src/components/commands/CommandPanel.tsx`
- Tests: `backend/tests/test_commands.py`

## Design decisions

- **Objects, not strings, at the domain seam.** The API parses the wire request once; the invoker works with a typed command object that knows its target state and device compatibility.
- **Registry instead of a router ladder.** `create_command()` is the only place that maps `command_type` to a class. The API handler delegates to the invoker.
- **Guard before port.** Lifecycle and device-type checks happen before `apply`, so rejected requests are cheap and cannot touch the adapter.
- **State after successful apply.** The current state is saved only after the decorated port completes. If the port fails, the persisted state stays where it was.
- **Separate audit tables.** The command log records operator intent; the execution log records policy/adapter attempts. Combining them would make a rejected request look like a failed hardware call.
- **No undo yet.** Undo is optional in the pattern. A physical pump start can be compensated with a stop command, but a general inverse is not safe for every actuator, so this phase stores the intent and result rather than pretending to reverse hardware.

## Known limitations

- There is no durable queue or worker: `POST /api/commands` executes synchronously. A real deployment would use a job queue and idempotency keys.
- State saving and the two audit writes are separate commits. A crash between the port call and the state save can leave hardware and database out of sync; a production system needs an outbox or a single unit of work around the hardware boundary.
- The max-run-time decorator still blocks every command while a pump is over its limit, including `stop_pump`. That is a Phase 9 policy limitation, documented there; the command layer only reports it as `failed`.
- The legacy `POST /api/actuators/{id}/apply` demo route remains for Phase 9 compatibility and tests. It is not used by the dashboard, and it is not the command path.
- There is no optimistic concurrency check: two commands can read the same state before either saves. A production implementation would lock the actuator row or compare `updated_at`.
- `set_light_level` is exposed in the generic idle `allowed_commands`; the command layer’s grow-light check is what prevents a pump from accepting it.

## Add-a-command exercise

To add `set_fan_speed`:

1. Add `SetFanSpeedCommand` in `domain/commands/`, validate its payload, and give it a `supported_device_types` entry for the fan device type.
2. Register it in `domain/commands/registry.py`.
3. If it changes lifecycle, give it a `target_state`; if it only changes a setting, leave `target_state` as `None`.
4. Add the command name to the appropriate state’s `commands` tuple, then add a UI button whose `disabled` expression reads `allowed_commands`.
5. Add a service test for success and a state-guard rejection test; the invoker, audit table and API route need no changes.
