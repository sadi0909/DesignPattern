# Phase 2 — Factory Method Study Notes

> Use these notes to understand the questions and write your own answers. Do not copy the wording directly into the assignment.

## Project code map

- `backend/src/domain/sensors/entity.py` — framework-independent `Sensor` product entity.
- `backend/src/domain/sensors/creators.py` — creator abstraction, concrete creators, and registry.
- `backend/src/application/sensors/service.py` — application client that requests a sensor from a creator and persists it.
- `backend/src/infrastructure/persistence/models.py` — SQLAlchemy `DeviceRow` database model.
- `backend/src/infrastructure/persistence/device_repository.py` — maps domain sensors to database rows and back.
- `backend/src/interfaces/api/sensors.py` — thin HTTP adapter for GET and POST sensor requests.
- `frontend/src/services/api.ts` — typed browser API functions.
- `frontend/src/features/sensors/SensorList.tsx` — dashboard list and creation buttons.

## 1. Intent of Factory Method

Factory Method is about moving the decision and details of object creation behind a common creator interface. The client asks for a product without knowing every concrete class or every default value.

When constructors or `if/elif` branches are scattered across callers, adding a type requires changing many places. Defaults can become inconsistent and callers become coupled to implementation details.

**Write in your own answer:** explain the maintenance problem, not just the phrase “creates objects.”

## 2. Participants

Use the five roles from the question:

- **Product:** the common kind of object the client receives and uses.
- **Concrete product:** one particular variation of that product.
- **Creator:** the abstraction that declares the factory method.
- **Concrete creator:** the variation-specific class that implements the factory method and owns its defaults.
- **Client:** the code that asks for a product and uses it without constructing the concrete variation itself.

**Code connection:** map these roles to the sensor entity, the moisture/light variations, the creator classes, and `SensorService`.

## 3. Adding a new product variant

With polymorphic creators, a new variant normally means a new concrete product/creator and a registry entry. The main application workflow can remain unchanged because it calls the shared creator method.

With one large conditional factory, the central function must be edited every time. That may be acceptable for a tiny stable problem, but it creates a shared change hotspot as variants grow.

**Think about:** which approach lets a new type be added near its own defaults?

## 4. Product and concrete creators in this lab

The product is the plain domain `Sensor`. The concrete creators are the moisture and light creator classes. The API and service should not construct the concrete variations directly because that would put type-specific knowledge in the caller.

Trace the actual code: the router passes the short type to the service; the service calls `get_creator`; the creator builds the sensor; the repository saves it.

**Important distinction:** the service is the client of the creator abstraction. It does not need to import concrete creator classes.

## 5. `type` versus `device_type`

The request `type` is a short selection key intended for the API client, such as `moisture` or `light`. `device_type` is the canonical stored domain/database value, such as `moisture_sensor` or `light_sensor`.

The concrete creator decides the canonical `device_type` and its `default_config`. This keeps the API request simple and keeps defaults next to the creator that owns them.

**Check the code:** compare `SensorCreateRequest.type` with the values returned by each creator.

## 6. One `devices` table

The shared table represents devices generally, while the `role` column identifies whether a row is a sensor. This avoids prematurely creating separate tables for every device kind.

Filtering by `role="sensor"` lets the repository list only sensors now. The design leaves room for later phases to add actuators and device-family information without replacing the foundation.

**Do not claim:** that the table already implements later-phase actuator behavior. It only prepares a persistence boundary for it.

## 7. Unknown sensor types

An unknown short key should be rejected before a database insert. The registry lookup is the natural place to determine whether a creator exists; the API translates that domain/application error into HTTP `400` with a useful message.

This keeps the router from guessing which concrete class to construct and prevents invalid rows from being saved.

## 8. Factory Method versus simple factory

A simple factory is one function that branches on a type and returns an object. It can be reasonable when there are very few variants, the problem is stable, and central branching is still easy to understand.

Factory Method adds polymorphic creators. Each creator owns one variation's construction details, giving the design a clearer extension point. Phase 2 uses it to practice adding sensor variants without expanding the service's creation logic.

**Your comparison should be balanced:** Factory Method is not automatically better for every small problem.

## 9. Factory Method versus Abstract Factory

Factory Method focuses on selecting and creating one product variation. Abstract Factory focuses on creating a compatible family or bundle of related products.

Phase 2 creates one sensor at a time, so a single creator method is enough. Later, Abstract Factory can coordinate related device products that must belong to the same family, while Factory Method can remain part of the individual creation process.

**Use the greenhouse example:** one moisture sensor versus a coordinated group of related devices.

## 10. SQL/HTTP inside a creator

A concrete creator should decide how to construct and configure a domain product. It should not parse HTTP requests or commit SQLAlchemy sessions.

FastAPI request parsing and HTTP status mapping belong in the API/interface layer. Sessions, ORM rows, commits, and queries belong in infrastructure/repositories. The application service coordinates the use case.

Keeping these concerns separate means creators can be unit-tested without a web server or database, and the domain remains independent of frameworks.

## Trace exercise

Starting at `POST /api/sensors`, write the collaborators in order:

1. HTTP request model
2. router function
3. application service
4. creator registry
5. concrete creator
6. domain sensor
7. repository
8. ORM row
9. PostgreSQL table

Then explain which layer owns each responsibility.

## Self-check before submitting

Try answering these without looking at the notes:

- What is the exact factory method name in this project?
- Where is the creator registry?
- Which class owns moisture defaults?
- Why does the service not import `MoistureSensorCreator` directly?
- What happens for `POST {"type": "temperature"}`?
- Why is `devices` filtered by `role`?
- Which code is allowed to call `commit()`?
- What would you add to support a temperature sensor?

If you can explain the request flow and the reason for each layer in your own words, you understand the practical part of Phase 2.
