# Phase 6 — Strategy questions

**Pattern / focus:** Strategy.

**Read first:** [Guide 06](../../materials/guides/06-strategy.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example shipping quotes) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to irrigation (or lighting) policies, location context, and the automation API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Strategy in plain language. How does the **context** use a strategy, and why must “choose which algorithm” stay separate from “run the algorithm”?

Ans:

Strategy is basically used when we have different ways of doing the same thing and we want to switch between them without changing the main code.

In this lab, AutomationService gets the saved strategy using get_strategy(key) and calls decide(context) to get the recommendation. Keeping these separate means we can add a new strategy without changing the service or router.

2. Name the participants (**strategy**, **concrete strategies**, **context**, **client**). What goes wrong when all policies live as `if/elif` inside the context (or inside an HTTP router)?

Ans:

The main parts are AutomationStrategy (interface), ConservativeMoistureStrategy and AggressiveMoistureStrategy (concrete strategies), AutomationService (context) and the client which selects the strategy through the API.

If everything is inside if/elif, adding a new policy means changing the same code again. It also makes testing harder and mixes business logic with the HTTP router. Keeping each strategy separate makes it easier to manage.

3. When should you use Strategy, and when should you skip it (one algorithm only; or the variation is a **lifecycle mode** rather than a chosen policy)?

Ans:

We should use Strategy when we have different algorithms doing the same job, like conservative and aggressive irrigation.

If there is only one algorithm, a simple function is enough. Also, if an object changes between states during its lifecycle, like an actuator going from closed to open, State pattern makes more sense.

## B. This phase of the application

4. In this lab, what does a strategy’s `decide(context)` return (action + reason)? Give a concrete difference you implemented (or were required to implement) between **conservative** and **aggressive** on the **same** moisture reading and zone thresholds.

Ans:

decide(context) returns a Recommendation with an action and reason. The action can be irrigate or wait, and the reason explains why.

For example, if moisture is 0.40 and the thresholds are 0.25-0.45, conservative will return wait, while aggressive will return irrigate. Below 0.25 both irrigate, and at or above 0.45 both wait.

5. Where do the numbers in `LocationAutomationContext` (or your equivalent) come from? Why must strategies receive a plain context object, not SQLAlchemy rows or FastAPI types? Why are thresholds read from **zones**, not hardcoded in the strategy class?

Ans:

The moisture value comes from the latest sensor_readings row and is converted from percentage (0-100) to a fraction (0-1). The thresholds come from the location's zones in the database.

We use a plain frozen dataclass so the strategy doesn't depend on SQLAlchemy or FastAPI. It also makes testing easier. Thresholds come from zones because each zone can have different settings, instead of hardcoding the same values for all.

One limitation is that the latest reading currently comes from all moisture sensors because devices are not yet linked to a specific location.

6. The active `strategy_key` is **persisted** per `location_id` (for example in `automation_rules`). Why must `POST .../automation/evaluate` use the **saved** key rather than a key the client sends only in that request? What happens on the next evaluate after the operator changes strategy but moisture stays the same?

Ans:

The selected strategy is saved in automation_rules for each location. If the client could send any strategy during evaluation, the result might not match the saved configuration.

For example, with moisture 0.40 and thresholds 0.25-0.45, conservative returns wait, but aggressive returns irrigate. So even if moisture stays the same, changing the strategy changes the result.

7. Strategy **recommends** (irrigate / wait). It should not itself start a pump. Why keep **decide** separate from **execute**? Which later pattern is meant to carry out the action?

Ans:

Strategy should only decide what to do, not execute it. This makes testing easier and gives the operator a chance to check or block the action before any water is used.

Command pattern in Phase 10 will handle the actual action. The flow is recommendation → command → actuator.

## C. Compare, contrast, and scenarios

8. Contrast Strategy with **State** (Phase 8). Both delegate to an object with the same shape. Who typically **changes** the active object, and is the variation a **policy** or a **lifecycle**?

Ans:

In Strategy, the client chooses the policy, like conservative or aggressive irrigation. It answers how the system should make a decision.

In State, the object changes its own state when events happen, like an actuator moving from closed to open or faulted. So Strategy is about choosing a policy, while State is about an object's lifecycle.

9. Contrast Strategy with **Adapter** (Phase 5) and with **Builder** (Phase 4). Which one translates a foreign API, which one assembles a valid aggregate, and which one swaps an algorithm?

Adapter translates a foreign interface into the format our application expects, like converting vendor sensor data into a normal Reading.

Builder assembles an object step by step and checks if it is valid, like LocationConfigBuilder in Phase 4.

Strategy lets us switch between different algorithms, like conservative and aggressive irrigation. Basically Adapter translates, Builder assembles and Strategy swaps the algorithm.

10. A classmate writes one “mega-strategy” that still contains `if conservative` / `if aggressive` inside a single class. Another strategy class calls the actuator adapter to water immediately. Explain why each is a trap.

Ans:

A mega-strategy puts all the policies in one class using if/elif. Adding more policies will make it harder to manage and test. Keeping each policy in its own class makes things simpler.

A strategy that calls the actuator directly is also wrong because it mixes decision making with execution. It could start watering without giving anyone a chance to check the recommendation first.

The strategy should return a recommendation, and a Command object should handle the actual action.