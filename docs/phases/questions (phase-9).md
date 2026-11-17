# Phase 9 — Decorator questions

**Pattern / focus:** Decorator.

**Read first:** the supplied Phase 9 guide and requirements

## How to answer

- Use your own wording. Do not paste teaching-example types (for example HTTP client wrappers) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to `ActuatorPort`, policy decorators, and `actuator_execution_log` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Decorator in plain language. Why is stacking wrappers a flexible alternative to a combinatorial explosion of subclasses (`LoggingRetryMaxRuntimeActuator`, …)?

**Answer:** Decorator is basically used when we want to add extra behaviour to an existing object without changing its original code.

Instead of creating separate classes for every combination of features, we can wrap one decorator around another. For example, we can add logging and max run-time checking around the actuator adapter.

If we use inheritance for everything, we will end up with too many classes like `LoggingRetryActuator` and `LoggingMaxRuntimeActuator`. With Decorator we can just combine the wrappers whenever we need them.

2. Name the participants (**component**, **concrete component**, **decorator**, **concrete decorators**). What interface does every decorator present to the caller, and why must that match the wrapped component?

**Answer:** The main parts are:

- **Component:** `ActuatorPort`, which defines the `apply()` method.
- **Concrete component:** `SimulationActuatorAdapter`.
- **Decorator:** `ActuatorDecorator`, which wraps another actuator port.
- **Concrete decorators:** `LoggingActuatorDecorator` and `MaxRunTimeActuatorDecorator`.

Every decorator should use the same `apply(device_id, command, payload)` interface as the original adapter. This way the service doesn't need to know whether it is using a normal adapter or multiple decorators wrapped around it.

3. **Order matters.** Using logging and retry (or logging and max-run-time) as an example, explain how wrapping A around B can change what you observe compared with wrapping B around A.

**Answer:** The order matters because each wrapper handles the call differently.

In this project logging is outside max run-time. So even if max run-time blocks a command, logging can catch the error and save a failed attempt in the database.

If we reverse the order, max run-time can block the command before it reaches the logging decorator. Then the failed attempt won't be recorded.

So the order decides what gets logged and when.

## B. This phase of the application

4. What is `ActuatorPort` here, and which **at least two** decorators did you stack around the real adapter (for example logging and max run-time)? Where is the chain wired (composition root / factory), and why not inside the HTTP router?

**Answer:** `ActuatorPort` is the common interface for actuators. It has one method, `apply(device_id, command, payload)`.

In this phase we use `SimulationActuatorAdapter` with two decorators: `MaxRunTimeActuatorDecorator` and `LoggingActuatorDecorator`.

They are connected inside `build_actuator_port()` in the composition file. We don't put this logic in the HTTP router because the router should only handle requests and responses.

This also makes it easier for other parts of the application, like Phase 10 Command, to use the same decorated port.

5. Max run-time can **short-circuit**: the inner adapter is never called. Why must a blocked attempt still produce a row in `actuator_execution_log` with `success=false` and the policy named in `policy_applied`?

**Answer:** Even if the command is blocked, we still need to know that someone tried to execute it.

If we don't save it, the dashboard won't show anything and we won't know why the pump didn't start.

The row should have `success=false` and `policy_applied` should show `maxRunTime`. Since logging is outside max run-time, it can catch the error, save the failed attempt and then pass the error back to the API.

6. How does max run-time know the actuator has been running too long (for example `actuator_states.updated_at` from Phase 8)? Why is that data from **State**, not something the decorator should invent as a second lifecycle?

**Answer:** `MaxRunTimeActuatorDecorator` gets the actuator state and `updated_at` from `ActuatorStateRepository`.

If the actuator is running, it checks how long it has been in that state. If it goes over the configured limit, which is 30 seconds by default, it blocks the command.

We already have this information from Phase 8, so there is no reason to create another running timer inside the decorator. Otherwise the two states could become different, especially after a backend restart.

The decorator should only check the time and block the call if needed. It should not manage the actuator lifecycle itself.

7. `GET /api/actuators/executions` feeds the dashboard execution log. Why persist attempts in the database instead of only printing to stdout? What should the UI show after a blocked attempt and a refresh?

**Answer:** Printing logs in the terminal is not enough because they can disappear after restarting the backend. Also the dashboard cannot easily access them.

By saving executions in `actuator_execution_log`, we can see the history even after restarting and check what happened to each actuator.

After a blocked attempt and page refresh, the dashboard should show a new failed row with a red badge, the applied policies and the reason why it was blocked.

So even failed attempts remain visible in the execution history.

## C. Compare, contrast, and scenarios

8. Contrast Decorator with **Adapter**. Both wrap. One **keeps** the interface and **adds** behaviour; the other **changes** the interface and **translates**. Which is which in this greenhouse (Phase 9 vs Phase 5)?

**Answer:** Adapter changes the interface so that something incompatible can work with our application.

Decorator keeps the same interface but adds extra behaviour around the object.

For example, in Phase 5 the adapters convert vendor or simulation data into the format our application expects. In Phase 9, the logging and max run-time decorators wrap `SimulationActuatorAdapter` and add extra functionality without changing its `apply()` method.

So Adapter translates, while Decorator adds behaviour.

9. Contrast Decorator with **inheritance** of combined policies. How does composition let you add or remove a policy without a new subclass for every combination?

**Answer:** With inheritance we would need to create a different class for every combination of policies. For example, logging alone, max run-time alone and logging with max run-time.

If we add more policies, the number of classes will increase a lot and it becomes difficult to maintain.

With Decorator we can simply wrap one object with another. In this project `build_actuator_port()` creates the required chain, and we can add or remove a decorator without creating another subclass.

10. A classmate’s decorator changes the method signature “a little” (extra required argument, different return type). Another ignores wrap order and cannot explain whether logging runs once per logical call or per inner attempt. Explain why each is a trap.

**Answer:** Every decorator must keep the same interface as `ActuatorPort`. If one decorator needs an extra argument or returns a different type, then it won't work properly with the other wrappers and the service.

The wrapping order is also important because it decides how many times logging happens and whether failed attempts are recorded.

For example, logging outside max run-time records the blocked attempt. But if logging is inside, it may never receive that call.

So we should keep the same interface and define the decorator order properly when building the chain.
