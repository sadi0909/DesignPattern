# Phase 7 — Facade questions

**Pattern / focus:** Facade.

**Read first:** the supplied Phase 7 guide and requirements

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a video publish pipeline) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to the location overview, the facade, and the dashboard Overview page from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Facade in plain language. What problem appears when every HTTP handler (or every UI screen) repeats the same multi-step dance across repositories and services?

**Answer:** Facade gives a caller one higher-level operation for a task that requires several collaborators. Instead of knowing how to gather locations, devices, readings, and automation information, a caller asks for a location overview and receives a result shaped for that use case.

When every handler or screen repeats that orchestration, each copy can call steps in a different order or apply different error handling. A change to the subsystem then requires updating every copy, and one forgotten caller may produce inconsistent results. Centralizing the coordination makes the sequence easier to test and change without forcing all callers to know the details.

2. A facade **orchestrates** collaborators. What should it **not** become (a god object that owns all domain logic)? Where should irrigation policy, sensor translation, and persistence stay instead?

**Answer:** A facade should not become a god object that owns every rule and implements every operation in the application. Its responsibility is to coordinate the collaborators needed for one use case and assemble their results, not replace those collaborators.

In this app the overview facade calls the automation service, which delegates irrigation decisions to the selected Strategy. Sensor adapters translate raw sensor data into normalized readings; repositories and the database handle persistence and queries. Keeping those responsibilities separate means the overview can change without copying or rewriting the policy, adapter, or database implementation.

3. When should you use Facade, and when should you skip it (a single repository call is enough; or you actually need to **translate** a mismatched interface)?

**Answer:** Use a facade when a use case regularly requires coordinating several subsystem operations and clients benefit from a stable, simpler entry point. The location overview is a good example: it combines location information, device and reading summaries, and a strategy recommendation.

Skip the extra layer when a caller only needs a simple repository operation and there is no meaningful coordination to hide. If the problem is that a vendor component exposes an incompatible data shape or protocol, use an Adapter to translate it; a Facade is not a substitute for that translation. The two can work together, because a facade can coordinate a subsystem that itself uses adapters.

## B. This phase of the application

4. What does `GET /api/locations/{location_id}/overview` return? Name the main pieces of the overview DTO (location, device counts, latest readings, strategy key, last recommendation). Why is overview scoped by `location_id`?

**Answer:** It returns a location object with its ID and name, counts of sensors and actuators, the latest reading per sensor with its device ID, value, unit and timestamp, the active strategy key, and a recommendation with action and reason. The recommendation is computed on each request by the existing automation service; despite the field name `last_recommendation`, it is not a saved historical result. A missing location returns 404.

The path uses `location_id` because location configuration, zones, and the saved strategy belong to a particular location. There is an important current limitation: devices have no location association, so the displayed device counts and latest readings are global, and the automation service uses the latest global moisture reading. The dashboard and API schema label this rather than pretending those fields are location-specific. A future association is needed for true location isolation.

5. Why does this phase **not** require a new business table? What already exists from Phases 2–6 that the facade only **composes**?

**Answer:** The overview is a read model, not a new business entity that needs its own durable record. The existing database already contains devices from the factory phases, locations and zones from Builder, sensor reading history from Adapter, and per-location automation rules from Strategy.

The facade obtains those existing facts through repositories and asks the automation service for a recommendation. It combines the answers into a DTO for the dashboard without copying the data to a new business table. No view or schema migration was needed; the current recommendation is calculated on demand instead of stored.

6. The overview HTTP handler should call **only** the facade, not reading/strategy/device repositories directly. Why? How does that help tests and later changes to the query shape?

**Answer:** The handler is an HTTP boundary: it accepts a location ID, delegates to one facade, and translates a missing-location error into 404. It does not need to know which repositories to call, how many queries are used, or how the automation service evaluates a recommendation.

A handler test can replace one facade with a fake and check the response and error mapping. The facade and repository can then be tested separately. If the reading query later changes to a join or devices become associated with locations, that work can remain behind the same facade and response contract rather than being repeated in every handler.

7. The Overview page should make **one** fetch and render cards from the DTO. Why must the React page not stitch five API calls together to build the same snapshot? How does a new reading or a saved strategy show up on overview without extra frontend glue?

**Answer:** One overview request keeps subsystem choreography on the server. If React made separate calls for the location, devices, readings, rule and recommendation, each screen would have to coordinate loading, failures, and result mapping itself. Separate requests could also observe different moments in time, although a single overview request alone does not guarantee a transactionally consistent database snapshot either.

On each overview GET, the facade queries the current data and asks the automation service to evaluate the saved strategy. The page displays the returned DTO without calculating the policy itself. A new reading or saved strategy appears on the next load or when the operator presses **Load / refresh**; the page does not currently refresh automatically when another panel changes data.

## C. Compare, contrast, and scenarios

8. Contrast Facade with **Adapter**. One makes an existing interface usable; the other makes a subsystem simpler to call. Which is which, and how do both appear in this greenhouse app (Phase 5 vs Phase 7)?

**Answer:** Adapter translates an existing incompatible interface into a contract the application can use. In Phase 5, simulation and vendor sensor adapters turn differently shaped raw data into normalized readings expected by the sensor port, so application services need not understand vendor fields.

Facade instead offers a simpler entry point to a group of collaborators. In Phase 7, the overview facade coordinates repositories and the automation service and returns one DTO to the handler. It does not translate a vendor protocol itself; it can use data that has already passed through an adapter.

9. This phase mentions **N+1** queries. What is an N+1 problem in an overview that lists latest readings for many devices, and what can the facade (or its repository) do about it without putting SQL in the router?

**Answer:** An N+1 problem would occur if the server first queried N sensors and then ran one additional latest-reading query for each sensor. As the sensor count grows, the number of database round trips grows with it, slowing the overview even though the client made only one HTTP request.

Here the reading repository uses a SQL window function, partitioned by device and ordered by timestamp and ID, to select the latest reading for each sensor in one query. The device repository obtains role counts with a grouped query. The facade coordinates those operations while SQL stays in the repository, not the router; an integration test checks that the total number of SELECTs remains bounded for several sensors.

10. A classmate hides every error behind a generic “overview failed,” so a missing location, a DB outage, and a strategy error look the same. Why is that a trap for a facade?

**Answer:** These errors mean different things and need different responses. A missing location is a client-visible 404, while a database outage is a server-side failure that may require operational attention; an invalid stored strategy indicates an application or configuration problem. Calling all of them “overview failed” makes diagnosis and appropriate client behavior harder and may mislead the operator.

The facade should preserve meaningful failures rather than silently returning an empty overview. This handler catches the specific missing-location error and maps it to 404; other unexpected errors propagate as server errors rather than being misreported as a missing location. Production logging and safe, more specific error responses could improve diagnostics without exposing sensitive internal details.
