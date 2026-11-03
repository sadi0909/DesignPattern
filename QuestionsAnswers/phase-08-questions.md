# Phase 8 — State questions

**Pattern / focus:** State.

**Read first:** the supplied Phase 8 guide and requirements

## How to answer

- Use your own wording. Do not paste teaching-example types (for example support-ticket states) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to actuator lifecycle, persisted state, and `allowed_commands` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of the State pattern in plain language. What problem appears when lifecycle is modelled as boolean flags and scattered `if` guards?

**Answer:** State lets an object change its behavior when its internal mode changes, so that the object appears to change class. Instead of every method starting with the same conditional checks, each mode becomes an object that knows which operations make sense and which modes are reachable next. The context delegates to the mode object that is currently active.

Boolean flags hide the mode instead of naming it. Three flags such as `is_running`, `is_fault`, and `is_maintenance` can represent eight combinations, but only a few are meaningful; nothing prevents `is_running` and `is_maintenance` from both being true. Guards are repeated at the start of every method, and a new code path that forgets one lets an illegal move through. Adding a new mode means editing every method rather than one place, and the UI cannot ask "what can this device do now?" without re-implementing the rules.

This application had exactly that gap before Phase 8. A device row stored `default_config.default_state` as text such as `"off"`, but nothing recorded the actuator's actual mode and nothing updated that hint. Any caller could claim any state, and the dashboard had no trustworthy value to display. The fix was to make the lifecycle explicit in the domain (`OffState`, `IdleState`, `RunningState`, `ErrorState`, `MaintenanceState`), delegate transitions to those objects, and persist the resulting state name in `actuator_states`.

2. Name the participants (**context**, **state interface**, **concrete states**, **client**). How does a successful command lead to a **transition**, and where do **guards** live?

**Answer:** The context is `ActuatorContext`. It holds the device ID and the current `ActuatorState`, and exposes `transition(target)` plus `allowed_commands()`. The state interface is `ActuatorState`, which declares the state name, its `allowed_targets`, its command vocabulary, and the guard method `require_transition()`. The concrete states are `OffState`, `IdleState`, `RunningState`, `ErrorState`, and `MaintenanceState`, each with its own target set and commands. The client is the API handler for `POST /api/devices/{id}/transition` and the dashboard that renders the result; Phase 10's Command objects will become another client.

A successful transition works like this. `ActuatorStateService` loads the device and its persisted state, builds `ActuatorContext.from_name(device_id, state_name)`, and calls `context.transition(target)`. The context resolves the target through `state_for(target)`, which raises `UnknownActuatorStateError` for a name outside the lifecycle. It then asks the current state `require_transition(target)`. That method checks `allowed_targets` and raises `IllegalTransitionError` when the edge is not listed. If the guard passes, the context replaces its state object with the target state, and only then does the service call `save_state()` to persist the new name.

The guards therefore live in the domain state objects, not in the FastAPI router, the application service, or React. The service is responsible only for loading, delegating, and saving; the router only translates domain errors into HTTP status codes. This matters because the same guard will be used by Phase 10 when commands, rather than a direct target, drive the actuator.

3. What is `allowed_commands` (or equivalent) for? Why is exposing “what can I do **now**?” better than letting the UI guess from a raw state string?

**Answer:** `allowed_commands` is the current state's list of command names that make sense right now. In this application `idle` advertises `start_pump`, `enter_maintenance`, and `shutdown`; `running` advertises `stop_pump`; `error` advertises `reset`. The list is produced by the active state object, so it changes automatically when the state changes.

A raw state string is only a label. To decide which buttons to enable, the UI would need its own lookup table from `"idle"` to commands, which duplicates domain knowledge in React. That copy drifts as soon as the lifecycle changes: add a new edge in the backend and the UI still shows the old set, or add a state and the UI has no entry at all. Exposing the list makes the API the single source of truth, so the dashboard can render legal actions without hard-coding transition rules.

The field is also the handoff to Phase 10. Command objects will consult the same set before executing, which keeps the visible buttons and the server-side behavior aligned. It is important to treat `allowed_commands` as an advertisement rather than the only enforcement: a client can still send any target, so the domain transition table remains the authoritative guard. The list tells the client what is possible; the guard ensures only legal moves are persisted.

## B. This phase of the application

4. Which actuator states did you implement (for example idle, running, error)? Sketch the **legal** transitions (which command or event moves idle → running, running → idle, into error, and out of error).

**Answer:** I implemented the five states from the lab: `off`, `idle`, `running`, `error`, and `maintenance`. The transition table is written in `backend/src/domain/actuators/state.py` and repeated in `docs/patterns/state.md`:

| From | Allowed targets | `allowed_commands` |
|------|-----------------|--------------------|
| `off` | `idle`, `error` | `enable` |
| `idle` | `running`, `maintenance`, `off`, `error` | `start_pump`, `enter_maintenance`, `shutdown` |
| `running` | `idle`, `error` | `stop_pump` |
| `error` | `idle`, `off` | `reset` |
| `maintenance` | `idle`, `off`, `error` | `exit_maintenance`, `shutdown` |

Read as events: `idle → running` when the pump is started (`start_pump`); `running → idle` when it is stopped (`stop_pump`); `idle → maintenance` when an operator takes it out of service (`enter_maintenance`), and back with `exit_maintenance`. A fault can move `off`, `idle`, `running`, or `maintenance` into `error`, and `reset` moves `error` back to `idle`. `off → idle` is `enable`, while `shutdown` moves `idle`, `maintenance`, or `error` to `off`. `running` cannot jump straight to `maintenance` or `off`; it must stop to `idle` first, which keeps the rule set small and predictable.

A self-transition is never allowed. `idle → idle` is not in the table, so repeating `start_pump` while already running is rejected rather than silently accepted. The demo endpoint in this phase accepts a target state rather than a command name; Phase 10 will map commands such as `start_pump` to these targets and check the state guard before executing.

5. Why is actuator state stored in `actuator_states` (or equivalent) rather than only in process memory? What must still be true after you restart the backend?

**Answer:** The state is persisted in the `actuator_states` table, one row per actuator, keyed by `device_id` with a foreign key to `devices` and `ON DELETE CASCADE`. Keeping it only in a Python dictionary would make the lifecycle a property of one process. A restart would reset every pump to whatever the default was, two Uvicorn workers could disagree about the same device, and a second instance would have a different view entirely. The dashboard and Phase 10 commands both need one shared answer, and PostgreSQL is that shared source of truth.

After a restart, the same actuator must still resolve to the same state and the same `allowed_commands`. The migration `5e4b7df306db_actuator_states.py` seeds every existing `role='actuator'` row to `idle`, and `DeviceRepository.save_devices()` inserts an `idle` row for newly provisioned actuators in the same transaction as the device row. Reads join that table, so `GET /api/devices` and `GET /api/devices/{id}` return the stored value rather than a default computed in memory. The `updated_at` timestamp records when the last saved transition happened.

The database test exercises this path: it provisions an actuator through the real repository, sees `idle`, transitions it to `running` through the API, and then re-reads the `actuator_states` row in a fresh session to confirm the value survived outside the request. A restart is the same situation at a larger scale: the row is already committed, so the next process finds `running`.

6. An **illegal** transition must raise a domain error and **must not** update the database. Why? Which HTTP status is reasonable for that case (400 or 409), and why should the rule live in the domain rather than in React?

**Answer:** If the row were written before the guard ran, the database would claim the actuator is in a mode it never entered. That corrupts everything that reads the mode: `allowed_commands` would advertise the wrong actions, later commands would be accepted or rejected from a false premise, and an operator could see `running` for a pump that never started. The domain also needs the chance to reject the move before any adapter or actuator port is invoked, because a rejected command must not cause a physical side effect either. In this implementation the in-memory context is the only thing mutated by `transition()`, and `save_state()` is called explicitly after the guard passes, so a rejected edge leaves the row untouched.

HTTP 409 Conflict is the better fit for a known target that cannot be reached from the current state. The request is syntactically valid and the target exists, but it conflicts with the current resource state; the client can refresh, observe the state, and choose a legal action. HTTP 400 is reserved here for a malformed request or an unknown target such as `"banana"`, which is not part of the lifecycle at all. A missing device or a sensor passed to the actuator endpoint is 404. The API maps the three domain outcomes separately instead of collapsing them into one generic error, which keeps diagnosis and client behavior meaningful.

The rule must live in the domain because the API is not the only caller. Phase 10 will execute commands, and a scheduler or test may drive transitions later; every path needs the same table. React can hide a button, but a client can bypass the UI and call the endpoint directly, so a React-only rule is a convenience, not a guard. Keeping the table in pure Python also makes the legal and illegal edges cheap to unit test without a database or HTTP request.

7. Device JSON gains `state` and `allowed_commands`. How does the dashboard use those fields (badges, disable illegal buttons)? How does this prepare **Phase 10 Command**?

**Answer:** The `DeviceDto` now includes `state` and `allowed_commands`. In `DeviceList.tsx`, every actuator renders a badge whose color follows the state: slate for `off` and `idle`, emerald for `running`, red for `error`, and amber for `maintenance`. The badge's tooltip lists the allowed commands, and a line under the device type spells out the same list so the rule is visible without hovering. The current UI does not yet show full control buttons, so there is nothing to disable; when Phase 10 adds them, the same array will decide which buttons are enabled instead of React guessing from the state string.

The device list is one query with a left join to `actuator_states`, so adding the state did not introduce a query per device. Sensors return `state: null` and an empty command list because the lifecycle belongs to actuators. A successful transition response returns the updated device DTO, which means a client that performs a transition can update its badge from the response without a second lookup.

For Phase 10, `allowed_commands` is the command catalog for the current mode. Command objects can check that the requested command is in the list before executing, and the domain transition guard rejects anything that slips through. That gives two layers: the UI only offers legal commands, and the server still enforces the rule if the UI is stale or the request is forged. It also means the set of legal commands is defined once in the state objects rather than being repeated in each command class.

## C. Compare, contrast, and scenarios

8. Contrast State with **Strategy**. Both look like “context delegates to an object.” Who typically **changes** the active object, and is the variation a **lifecycle** or a **selectable policy**? Give a greenhouse example of each (this phase vs Phase 6).

**Answer:** Both patterns put behavior behind an interface and let a context delegate to an implementation, which is why they look similar in class diagrams. The difference is who changes the delegate and why. In State, the object's own lifecycle changes the active state: a successful command moves the context from one mode to the next, and the state objects know those edges. In Strategy, a client or configuration selects one algorithm from a family, and the context runs it without switching itself; the choice is a policy preference rather than a mode the object entered.

In this application, Phase 6 is Strategy. `AutomationService` loads the saved key for a location, resolves either `ConservativeMoistureStrategy` or `AggressiveMoistureStrategy`, and calls `decide(context)`. The operator chooses the policy through the automation panel, and the strategy itself does not decide to become the other strategy. Phase 8 is State. A pump in `idle` moves to `running` when started, then back to `idle` when stopped; the lifecycle, not an operator preference, determines that `running` is the next mode. The `ActuatorContext` changes its own state as those commands succeed.

The code reflects the distinction. Strategy classes expose `decide()` and contain thresholds and recommendation logic. State classes expose `allowed_targets` and `allowed_commands()` and contain no irrigation policy at all. A useful question is: "Did the object enter this mode as part of its lifecycle, or did someone choose this algorithm for it?" If the answer is the former, State fits; if it is the latter, Strategy fits.

9. Contrast State with a pile of booleans (`is_running`, `is_fault`, `is_maintenance`). Why do illegal combinations of flags appear, and how do explicit state objects (or a transition table) prevent that?

**Answer:** Each boolean is independent, so three flags describe eight combinations even when only four are meaningful. Nothing in the type system stops a caller from setting `is_running = True` and `is_maintenance = True`, and each setter typically knows only its own flag. The illegal combination appears because the mode is implicit: the flags are supposed to encode one mode, but they are written separately and no single place validates the result. Guards then have to check several flags in the right order in every method, and a new method that checks only one of them lets a bad combination through.

Explicit states collapse the representation to one value. `actuator_states.state` is a single `VARCHAR`, and `state_for()` accepts only the five registered names. The database row cannot simultaneously say `running` and `maintenance`; the schema and the domain both make that combination unrepresentable. Legal edges exist in exactly one table, and `require_transition()` consults it before any write. Adding a state is one class plus the edges that lead to it, not an audit of every method.

The practical benefit is not just fewer bugs but better communication. The dashboard can print the state and its allowed commands, tests can iterate over the table, and a new developer can read the five classes to understand the lifecycle. A pile of booleans requires reconstructing the intended state machine from scattered conditions.

10. A classmate puts HTTP status mapping or SQLAlchemy commits **inside** a concrete state class. Another state mutates a flag directly and skips `transition` / `set_state`. Explain why each is a trap.

**Answer:** Putting HTTP status mapping or database commits inside a state class couples the domain to FastAPI and SQLAlchemy. The state objects are meant to answer one question: is this move legal, and what is the next mode? If `RunningState` raises an `HTTPException` or calls `session.commit()`, it can no longer be used by a CLI, a scheduled job, or Phase 10 without dragging the web framework and a transaction along. Unit tests then need a request context or a database, transaction boundaries become unclear, and a failure after a partial commit can leave the device in a state the domain never approved. The correct split is the one used here: the state raises `IllegalTransitionError`, the application service saves, and the router maps the error to 409.

Mutating a flag directly and skipping `transition()` or `set_state()` bypasses the guard and the persisted record. The in-memory mode changes while the `actuator_states` row still says something else, so the next read, the next `allowed_commands` response, and Phase 10 all operate on stale information. It also reintroduces the exact problem State was chosen to remove: a second path that can produce an illegal mode. In this code the only assignment to `ActuatorContext.state` is inside `transition()` after the guard passes, and the only persistence call is in `ActuatorStateService.transition()` after that. Keeping a single writer is what makes the lifecycle auditable and testable.
