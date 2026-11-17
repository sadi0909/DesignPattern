# Phase 10 — Command questions

**Pattern / focus:** Command.

**Read first:** the supplied Phase 10 guide and requirements

## How to answer

- Use your own wording. Do not paste teaching-example types (for example editor undo commands) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to command objects, the invoker, `command_log`, and the controls UI from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Command in plain language. What does it mean to **objectify a request**, and what can you do with that object that you cannot do with a bare `actuator.start()` call (queue, audit, undo, history)?

**Answer:** Command is basically used to turn an action into an object instead of directly calling a method.

For example, instead of directly calling `actuator.start()`, we create a `StartPumpCommand` which contains the command type, device and payload.

This makes it easier to execute, save in history, retry or even undo if possible. In this project we don't implement undo because physical actions like starting a pump don't always have a safe way to reverse them.

2. Name the participants (**command**, **receiver**, **invoker**, **client**). Who creates the command, who triggers `execute()`, and who actually changes actuator/hardware state?

**Answer:** The main parts are:

- **Command:** `StartPumpCommand`, `StopPumpCommand` and `SetLightLevelCommand`.
- **Receiver:** The decorated `ActuatorPort` and `ActuatorContext`.
- **Invoker:** `CommandService.submit()`, which handles the execution.
- **Client:** The API handler and dashboard controls.

The API receives the request and `create_command()` creates the correct command object. Then the invoker calls `execute()`, which sends the request through the decorated port. The adapter handles the actuator operation and the invoker updates the saved state.

3. If a command supports undo, when must it capture the data needed to reverse the action? Why is “capture **before** mutate” critical?

**Answer:** It must capture the old value before changing anything.

For example, if we are changing a light level, we need to remember its previous level first. Otherwise after changing it we might not know what the old value was.

So capturing before mutation is important because undo needs the original data to restore it.

## B. This phase of the application

4. Which command types did you implement (for example `start_pump`, `stop_pump`, `set_light_level`)? Why does the HTTP handler create a command and pass it to an **invoker** (or application service) instead of calling the actuator adapter from the router?

**Answer:** I implemented `start_pump`, `stop_pump` and `set_light_level`.

The HTTP handler just receives the request and passes it to `CommandService`. It doesn't decide which adapter method to call directly.

This is because the invoker handles the State checks, Decorator policies, state updates and command logging. If every router called the adapter directly, we would have to repeat all those things in different places.

5. Walk through the execute path: (1) consult State / `allowed_commands`, (2) if illegal → **rejected**, (3) if legal → decorated `apply`, update `actuator_states`, log **success** or **failed**. Why must a rejected command **not** change actuator state and **not** reach inner `apply`?

**Answer:** First `create_command()` creates the command object. Then the service checks the actuator and its current state.

It checks whether the requested command is allowed using `allowed_commands`.

If it is not allowed, the command is marked as `rejected` and the API returns 409. Nothing is executed and the actuator state stays the same.

If it is allowed, the command goes through the decorated `ActuatorPort`. After successful execution, the actuator state is updated and the command is saved as `success`. If something goes wrong during execution, it is saved as `failed`.

A rejected command should never reach the adapter because the action was not allowed in the first place. Otherwise it could execute something that State already rejected.

6. Distinguish **`rejected`** vs **`failed`** vs **`success`** in `command_log`. Give one greenhouse example of each. Why is “illegal in this state” not the same as “policy or adapter error after the command was accepted”?

**Answer:** 
- **Success:** The command was allowed and executed successfully. For example starting a pump when it is idle.
- **Rejected:** The command was not allowed in the current state. For example trying to start a pump that is already running.
- **Failed:** The command was allowed but something went wrong during execution. For example max run-time blocks it or the adapter gives an error.

Rejected and failed are not the same thing. Rejected means the command was never accepted, while failed means it was accepted but couldn't finish successfully.

7. Why is `command_log` a **different** table from Phase 9 `actuator_execution_log`? What concern does each log record (operator intent vs policy/adapter attempt)?

**Answer:** `command_log` records what the operator requested and what happened to that command. It stores things like command type, device, payload and status.

`actuator_execution_log` records what happened inside the decorated actuator port, including which policies were applied and whether the execution worked.

For example, a rejected command will have a record in `command_log` but no execution attempt in `actuator_execution_log`.

So one records the operator's request and the other records the actual execution attempt.

## C. Compare, contrast, and scenarios

8. Contrast Command with **Strategy**. Strategy is an interchangeable **algorithm** (decide / quote). Command is a **side-effectful request** with history. How do they cooperate in this app (Phase 6 recommends; Phase 10 executes)?

**Answer:** Strategy is about choosing an algorithm and deciding what should happen. For example in Phase 6, conservative or aggressive strategy decides whether irrigation is needed.

Command is about actually performing a specific action, like starting a pump, and recording that request.

So Strategy recommends what should happen and Command handles the actual action. They work together but they have different responsibilities.

9. Contrast Command with **State**. Who **triggers** the action, and who **decides whether it is legal**? Why must commands not bypass state guards?

**Answer:** The client creates the command and the invoker executes it. But State decides whether that command is allowed in the current situation.

For example, `StartPumpCommand` requests to start the pump, but the idle state decides whether `start_pump` is allowed and moves it to running.

Commands should not bypass State because the actuator might already be running or in maintenance. The State pattern makes sure only legal transitions happen.

10. The controls UI should disable actions that are not in `allowed_commands`. Why must the **backend** still reject illegal commands even if the UI is correct? What happens if a classmate’s command calls the raw adapter and skips State and Decorator?

**Answer:** The UI can be outdated or someone can call the API directly without using the dashboard. So disabling buttons is not enough. The backend must check `allowed_commands` again before executing anything.

If a command calls the raw adapter directly, it skips the State checks and Decorator policies. Then the actuator could be changed without updating its saved state or recording the execution properly.

We would also lose the logging and max run-time protection from Phase 9.

So commands should always go through the invoker and the decorated port.