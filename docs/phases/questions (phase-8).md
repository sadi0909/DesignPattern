# Phase 8 — State questions

**Pattern / focus:** State.

**Read first:** [Guide 08](../../materials/guides/08-state.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example support-ticket states) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to actuator lifecycle, persisted state, and `allowed_commands` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of the State pattern in plain language. What problem appears when lifecycle is modelled as boolean flags and scattered `if` guards?

**Answer:** State pattern is basically used when an object can have different states and its behaviour changes depending on the current state.

If we use multiple boolean flags like `is_running`, `is_fault` and `is_maintenance`, it can become confusing because some combinations are not even valid. We would also need to check these flags in different methods.

With State pattern, each state has its own rules and knows which transitions are allowed. This makes it easier to manage the lifecycle and avoid invalid states.

2. Name the participants (**context**, **state interface**, **concrete states**, **client**). How does a successful command lead to a **transition**, and where do **guards** live?

**Answer:** 
The main parts are:

- **Context:** `ActuatorContext`, which holds the current actuator state.
- **State interface:** `ActuatorState`, which defines the common methods and allowed transitions.
- **Concrete states:** `OffState`, `IdleState`, `RunningState`, `ErrorState` and `MaintenanceState`.
- **Client:** The API handler and dashboard which use the actuator.

When a transition is requested, the context checks the target state and then asks the current state if that transition is allowed. If everything is valid, it changes the state and the service saves the new state in database.

The guards are inside the domain state classes, not in the router or React. This means every part of the application follows the same rules.

3. What is `allowed_commands` (or equivalent) for? Why is exposing “what can I do **now**?” better than letting the UI guess from a raw state string?

**Answer:** `allowed_commands` basically tells us what actions are possible in the current state.

For example, an idle actuator can start the pump, enter maintenance or shutdown. A running actuator can stop the pump, and an error state can be reset.

Without this field, React would need its own rules to decide which buttons should be available. Then we would have the same logic in two places.

By returning `allowed_commands` from the API, the backend tells the UI what actions are available. Phase 10 can also use the same list when executing commands.

## B. This phase of the application

4. Which actuator states did you implement (for example idle, running, error)? Sketch the **legal** transitions (which command or event moves idle > running, running > idle, into error, and out of error).

**Answer:** 
There are 5 actuator states in this phase:

- `off`
- `idle`
- `running`
- `error`
- `maintenance`

The main transitions are:

- `off > idle` using enable.
- `idle > running` using `start_pump`.
- `running > idle` using `stop_pump`.
- `idle > maintenance` using `enter_maintenance`.
- `maintenance > idle` using `exit_maintenance`.
- Any active state can move to `error` when a fault happens.
- `error > idle` using reset.
- `idle`, `maintenance` or `error` can move to `off` using shutdown.

A running actuator cannot directly go to maintenance or off. It must first stop and return to idle.

Also, moving to the same state again is not allowed.

5. Why is actuator state stored in `actuator_states` (or equivalent) rather than only in process memory? What must still be true after you restart the backend?

**Answer:** If we only keep the state in memory, it will be lost whenever the backend restarts. Also, if we have multiple backend workers, they might show different states for the same actuator.

That is why we store it in the `actuator_states` table, with one row for each actuator.

Existing actuators are given `idle` during migration, and newly created actuators also get `idle` when they are provisioned.

After restarting the backend, the actuator should still have its previous saved state and the correct `allowed_commands`. The database is the shared source of truth.

6. An **illegal** transition must raise a domain error and **must not** update the database. Why? Which HTTP status is reasonable for that case (400 or 409), and why should the rule live in the domain rather than in React?

**Answer:** If an illegal transition is saved, then the database will show a state that the actuator was never supposed to enter. This can cause problems when other parts of the application try to use it.

For example, if a running actuator is not allowed to move directly to maintenance, that transition should be rejected before saving anything.

We can return **409 Conflict** because the target state exists but it is not allowed from the current state. An unknown target should return **400**, and a missing device should return **404**.

The rule should live in the domain because React can be bypassed by sending a direct API request. So hiding a button in the UI is not enough. The backend must check the transition itself.

7. Device JSON gains `state` and `allowed_commands`. How does the dashboard use those fields (badges, disable illegal buttons)? How does this prepare **Phase 10 Command**?

**Answer:** The dashboard uses `state` to show a badge for each actuator. Different states have different colors, like green for running, red for error and amber for maintenance.

It also shows the allowed commands so the user can see what actions are available.

Sensors have `state: null` and an empty command list because they don't have an actuator lifecycle.

In Phase 10, these commands can be used to decide which buttons should be enabled and which commands are allowed to execute. So the UI and backend can follow the same rules. 


## C. Compare, contrast, and scenarios

8. Contrast State with **Strategy**. Both look like “context delegates to an object.” Who typically **changes** the active object, and is the variation a **lifecycle** or a **selectable policy**? Give a greenhouse example of each (this phase vs Phase 6).

**Answer:** State and Strategy look similar because both use different objects to handle behaviour, but they are used for different purposes.

In Strategy, the client chooses which policy to use. For example, the operator can choose conservative or aggressive irrigation in Phase 6.

In State, the object changes its own state depending on what happens. For example, an actuator moves from idle to running when the pump starts.

So Strategy is about choosing a policy, while State is about managing the lifecycle of an object.

9. Contrast State with a pile of booleans (`is_running`, `is_fault`, `is_maintenance`). Why do illegal combinations of flags appear, and how do explicit state objects (or a transition table) prevent that?

**Answer:** With boolean flags, every flag is independent. For example, 3 flags can create 8 different combinations, even though most of them might not make sense.

We could end up with an actuator showing both running and maintenance at the same time.

With State pattern we use one state value instead of multiple flags. An actuator can only have one state at a time, and the transition rules decide which state it can move to next.

This makes it easier to prevent invalid combinations and manage the lifecycle.

10. A classmate puts HTTP status mapping or SQLAlchemy commits **inside** a concrete state class. Another state mutates a flag directly and skips `transition` / `set_state`. Explain why each is a trap.

**Answer:** State classes should only handle state rules and transitions. They should not depend on FastAPI or SQLAlchemy.

For example, if `RunningState` directly commits something to the database or raises an HTTP exception, then it becomes difficult to reuse and test without those frameworks.

The state should raise a domain error when something is not allowed. The service handles saving the new state and the router handles HTTP responses.

Also, directly changing a flag or state without using `transition()` is a problem because it skips the guards and can leave the database with an old state.

So all transitions should go through the context and service. This makes sure the same rules are followed every time.
