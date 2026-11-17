# Decorator — Phase 9

## Problem

Phase 5 gave the greenhouse an `ActuatorPort` and one simulation adapter. Phase 8 added a lifecycle, but applying a command still had no cross-cutting behavior: no durable record of attempts, and nothing stopped a command from reaching a pump that had been `running` far past its safe limit.

Putting those concerns into the adapter would mix driver translation with policy. Putting them in the router would scatter `if` checks and make a second caller (Phase 10 Command) repeat them. Creating combined subclasses such as `LoggingMaxRuntimeSimulationActuatorAdapter` would only get worse as soon as a third policy appeared. The smell is **cross-cutting behavior with no stable wrapper seam**.

## Solution

Decorator wraps the actuator port with objects that expose the same `ActuatorPort.apply(device_id, command, payload)` interface, each adding one responsibility and delegating inward.

| Role | In Phase 9 |
|------|------------|
| **Component** | `ActuatorPort` — the interface callers use |
| **Concrete component** | `SimulationActuatorAdapter` — the real (simulated) driver |
| **Decorator base** | `ActuatorDecorator` — holds an inner `ActuatorPort`, delegates `apply()`, and exposes the stack's policy names |
| **Concrete decorators** | `LoggingActuatorDecorator`, `MaxRunTimeActuatorDecorator` |
| **Composition root** | `build_actuator_port()` in `infrastructure/adapters/actuators/composition.py` |

```text
LoggingActuatorDecorator
  └── MaxRunTimeActuatorDecorator
        └── SimulationActuatorAdapter
```

The order is deliberate:

- **Logging is outermost.** It sees the whole logical attempt, including a policy failure raised before the adapter is reached, and writes exactly one `actuator_execution_log` row.
- **Max run time sits immediately inside logging.** It can short-circuit the call; the adapter is not touched when the policy blocks.
- **The adapter is innermost.** It performs the actual apply and knows nothing about policies or persistence.

`LoggingActuatorDecorator` walks the wrapper chain with `policy_names()`, so a new inner policy automatically appears in `policy_applied`; the logging class does not hard-code the stack. The stored order is inner-to-outer, for example `["maxRunTime", "logging"]`.

## Max run time policy

The decorator reads Phase 8's `actuator_states` row, not a separate timer. If the persisted state is `running` and `updated_at` is older than the configured limit, it raises `MaxRunTimeExceededError` before delegating. The limit is `actuator_max_runtime_seconds` (default `30`, overridable through `ACTUATOR_MAX_RUNTIME_SECONDS` in `backend/.env`).

Using the State timestamp keeps one lifecycle as the source of truth. A second "running since" field would drift the moment a transition failed or an actuator was reset. The clock is injectable for tests; production uses UTC now.

## Execution log

`actuator_execution_log` stores one row per apply attempt:

| Column | Meaning |
|--------|---------|
| `id` | UUID primary key |
| `device_id` | FK to `devices`, `ON DELETE CASCADE` |
| `success` | `true` only when the adapter completed |
| `policy_applied` | JSONB list such as `["maxRunTime", "logging"]` |
| `message` | failure text, or `null` on success |
| `created_at` | timestamp with time zone |

`ExecutionLogRepository.record()` commits immediately, so a failed attempt survives the exception that logging re-raises. `GET /api/actuators/executions?limit=20` returns newest first. Phase 10's command invoker calls this same decorated port; the legacy `POST /api/actuators/{device_id}/apply` route remains only as a Phase 9 demo entry point and is no longer used by the dashboard.

The dashboard panel shows time, device, a success/failed badge, the policies, and the failure message. A blocked attempt is therefore visible after refresh as `success=false` with `maxRunTime` in `policy_applied` and the limit in `message`.

## Where it lives in code

- Port and decorator base: `backend/src/domain/actuators/ports.py`
- Execution read model: `backend/src/domain/actuators/execution.py`
- Decorators: `backend/src/infrastructure/adapters/actuators/logging_decorator.py`, `max_runtime_decorator.py`
- Composition: `backend/src/infrastructure/adapters/actuators/composition.py`
- Persistence: `ActuatorExecutionLogRow` in `backend/src/infrastructure/persistence/models.py`, `execution_log_repository.py`, migration `e76077ba625e_actuator_execution_log.py`
- Application: `backend/src/application/actuators/execution_service.py`, `dto.py`, `mappers.py`
- API: `backend/src/interfaces/api/actuators.py`
- UI: `frontend/src/components/devices/ExecutionLog.tsx`
- Tests: `backend/tests/test_actuator_decorators.py`

## Design decisions

- **One wrapper per concern.** Logging and max runtime are independent classes; either can be removed or reordered by editing one composition function.
- **Same method signature.** Every wrapper implements `ActuatorPort.apply`; callers see one interface regardless of stack depth.
- **Failures are still attempts.** Logging catches, records `success=false`, then re-raises so the API can return 409. The write is committed before the re-raise.
- **Policy names are discovered, not configured twice.** `ActuatorDecorator.policy_names()` walks the chain, avoiding a second list that could drift from the actual stack.
- **The service validates the actuator, not the decorator.** `ActuatorExecutionService` rejects unknown devices and sensors with 404 before any attempt row is written; an apply on a missing device is not a real attempt.
- **No retry decorator yet.** Retrying a physical actuator command needs idempotency keys, which Phase 10's Command layer can supply.

## Known limitations

- Max run time blocks every command while over the limit, including a stop command. A production policy would likely let stop/shutdown through; the phase requirement only asks for a blocked attempt.
- The legacy demo apply endpoint does not change the actuator's Phase 8 state. Phase 10's command path maps commands to transitions and executes through this same decorated port; only the legacy route skips the lifecycle.
- `SimulationActuatorAdapter` keeps its applied-command history in memory per request, so that history is not durable. The durable record is `actuator_execution_log`.
- Policy failures return HTTP 409; adapter/driver failures bubble up as 500. Both are still recorded in the execution log.
