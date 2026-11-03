# Phase 2 — Factory Method questions

**Pattern / focus:** Factory Method.

**Read first:** [Guide 02](../../materials/guides/02-factory-method.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example courier notifiers) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to sensors, creators, the `devices` table, and the sensors API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Factory Method in plain language. What problem appears when callers scatter `new` / constructors (or a growing `if type == ...`) across the application?

2. Name the main participants of Factory Method (**product**, **concrete product**, **creator**, **concrete creator**, **client**). For each, give one sentence: what it is responsible for.

3. How do you add a **new product variant** when creators are polymorphic (new class + registry entry) versus when creation lives in one shared `if/elif` function? Why does that difference matter for extension?

## B. This phase of the application

4. In this lab, what is the **product** and what are the **concrete creators**? Why must the API handler (or sensor service) go through a creator/registry instead of constructing `MoistureSensor` / `LightSensor` itself?

5. `POST /api/sensors` accepts a short `type` key such as `"moisture"` or `"light"`, while the stored/returned field is `device_type` (for example `moisture_sensor`). Why are those two fields different? Who decides the stored `device_type` and `default_config`?

6. Why is there a single `devices` table with `role="sensor"` instead of a dedicated `sensors` table? What later phase does that choice prepare for?

7. What should happen when the client posts an **unknown** `type`? Where should that rejection be decided (registry/service vs router constructing a concrete class anyway)?

## C. Compare, contrast, and scenarios

8. Contrast Factory Method with a **simple factory** (one function full of `if type == ...`). When is the simple factory “good enough,” and why does this phase still want polymorphic creators?

9. Contrast Factory Method with **Abstract Factory** (Phase 3). Factory Method answers which question? Abstract Factory answers which different question? Why is Factory Method enough for Phase 2 sensors?

10. A classmate puts SQLAlchemy session commits (or FastAPI request parsing) **inside** a concrete creator. Why is that a trap? Where should persistence and HTTP stay instead?
