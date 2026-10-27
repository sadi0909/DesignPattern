# Phase 7 — Facade questions

**Pattern / focus:** Facade.

**Read first:** the supplied Phase 7 guide and requirements

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a video publish pipeline) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to the location overview, the facade, and the dashboard Overview page from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Facade in plain language. What problem appears when every HTTP handler (or every UI screen) repeats the same multi-step dance across repositories and services?

**Answer:** Facade is basically used when we need to bring multiple services together and make them easier to use.

For example, instead of the HTTP handler calling different services to get locations, devices, readings and automation info, it can just call the overview facade.

If we repeat all those steps in different places, the code becomes harder to maintain. So facade keeps the process in one place and makes it easier to change later.

2. A facade **orchestrates** collaborators. What should it **not** become (a god object that owns all domain logic)? Where should irrigation policy, sensor translation, and persistence stay instead?

**Answer:** Facade should not become one big class which handles everything. Its job is to bring different services together, not replace them.

Irrigation rules should stay in Strategy, sensor translation in Adapters and database operations in repositories.

This way each part handles its own job and facade just connects them when needed.

3. When should you use Facade, and when should you skip it (a single repository call is enough; or you actually need to **translate** a mismatched interface)?

**Answer:** We should use Facade when one task needs multiple services and we want to access them through one simple operation. The location overview is a good example.

If we only need one simple repository call, then adding a facade isn't really needed.

Also, if two interfaces don't match and we need to translate data between them, then Adapter is the better choice. Facade is more about making things easier to use together.

## B. This phase of the application

4. What does `GET /api/locations/{location_id}/overview` return? Name the main pieces of the overview DTO (location, device counts, latest readings, strategy key, last recommendation). Why is overview scoped by `location_id`?

**Answer:** It returns the location details, sensor and actuator counts, latest readings, active strategy key and a recommendation with its reason.

The recommendation is calculated when we request the overview, it is not a saved result from before. If the location doesn't exist, the API returns 404.

We use location_id because the configuration and strategy belong to a particular location. But right now devices are not connected to locations, so the device counts and readings are still global. Thats one limitation of the current setup.

5. Why does this phase **not** require a new business table? What already exists from Phases 2–6 that the facade only **composes**?

**Answer:** We already have the data from previous phases. Devices come from the factory phases, locations and zones from Builder, readings from Adapter and automation rules from Strategy.

The facade just collects this information and combines it into one DTO for the overview page.

So we don't need another table because the overview is not a new business entity. The recommendation is calculated when requested instead of being saved in database.

6. The overview HTTP handler should call **only** the facade, not reading/strategy/device repositories directly. Why? How does that help tests and later changes to the query shape?

**Answer:** The HTTP handler should just receive the request, call the facade and return the response.

If it starts calling different repositories and services directly, then it has to know too much about how the data is collected.

It also makes testing harder. If the handler only depends on the facade, we can replace it with a fake during testing. Later if the database queries change, we can handle that inside the facade without changing the router.

7. The Overview page should make **one** fetch and render cards from the DTO. Why must the React page not stitch five API calls together to build the same snapshot? How does a new reading or a saved strategy show up on overview without extra frontend glue?

**Answer:** The Overview page should make one request and get everything from the overview DTO.

If React makes separate requests for location, devices, readings and strategy, then it has to manage all those requests and errors separately. That makes the frontend more complicated than it needs to be.

With one request, the server collects everything and the page just displays the result.

When a new reading or strategy is saved, it will show up when the page is loaded again or when the user presses Load / refresh. It doesn't update automatically when something changes in another part of the application.

## C. Compare, contrast, and scenarios

8. Contrast Facade with **Adapter**. One makes an existing interface usable; the other makes a subsystem simpler to call. Which is which, and how do both appear in this greenhouse app (Phase 5 vs Phase 7)?

**Answer:** Adapter is used when an interface doesn't match what our application expects. In Phase 5, the sensor adapters convert vendor or simulation data into the normal Reading format.

Facade is used when we want to make multiple services easier to use together. In Phase 7, the overview facade collects information from different services and returns one DTO.

So Adapter translates the interface, while Facade brings different parts together behind one simple operation.

9. This phase mentions **N+1** queries. What is an N+1 problem in an overview that lists latest readings for many devices, and what can the facade (or its repository) do about it without putting SQL in the router?

**Answer:** N+1 happens when we first get a list of sensors and then make another database query for every sensor to get its latest reading.

For example, if we have 10 sensors, we could end up making 11 queries instead of getting the readings in one query. As the number of sensors increases, it becomes slower.

In this phase, the reading repository uses a SQL window function to get the latest reading for each sensor in one query. The device repository also uses a grouped query for the sensor and actuator counts.

The facade coordinates these operations, but the SQL stays inside the repositories and not in the router.

10. A classmate hides every error behind a generic “overview failed,” so a missing location, a DB outage, and a strategy error look the same. Why is that a trap for a facade?

**Answer:** Different errors mean different things. If the location doesn't exist, the API should return 404. But if the database is down, thats a server problem and needs different handling.

An invalid strategy is also a different issue, so we shouldn't treat every error like the location is missing.

The facade should keep these errors meaningful instead of returning an empty overview for everything. This makes it easier to understand what actually went wrong and fix it.
