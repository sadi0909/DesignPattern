# Phase 2 study guide — Factory Method

This is a study aid, not a completed answer sheet. Write the final answers in your own words in the assignment question file.

## How to study the questions

1. Read the question and identify whether it asks about the general pattern, this project's code, or a comparison.
2. Open the referenced file paths below and trace the request from the API to persistence.
3. Explain the idea aloud without copying the wording here.

## Code map

- Product/entity: `backend/src/domain/sensors/entity.py`
- Abstract and concrete creators: `backend/src/domain/sensors/creators.py`
- Application client: `backend/src/application/sensors/service.py`
- ORM and repository: `backend/src/infrastructure/persistence/`
- HTTP boundary: `backend/src/interfaces/api/sensors.py`
- Frontend client/UI: `frontend/src/services/api.ts` and `frontend/src/features/sensors/SensorList.tsx`

## Question prompts and hints

1. Focus on moving type-specific construction decisions away from callers and toward specialized creators. Mention the maintenance problem caused by scattered constructors or conditionals.
2. Identify the five roles: the common returned object, each concrete product variant, the abstraction declaring the factory method, each specialized implementation, and the code that requests a product.
3. Compare extension by adding a creator/registry entry with editing a central conditional. Explain why the first keeps the workflow stable.
4. Trace `POST /api/sensors` through the router, service, registry, creator, and repository. Explain why the router should not know the concrete construction details.
5. Distinguish an external request key from the canonical persisted device type. Find where each value is selected.
6. Look at the `role` column and connect the shared device table to future actuator/device-family work.
7. Follow the `get_creator` error path and identify the HTTP status produced by the router.
8. A simple factory centralizes branching in one function; Factory Method gives each variant a polymorphic creator. Decide when the simpler approach would be sufficient.
9. Factory Method creates one product variant; Abstract Factory coordinates a compatible family of products. Explain why Phase 2 only needs one sensor at a time.
10. Keep HTTP parsing in the API layer and database/session work in infrastructure. Ask what would happen to domain tests if creators required a web framework or live database.

## Self-quiz

- Can you point to the exact factory method?
- What changes would be needed to add a temperature sensor?
- What files would not need to change?
- Why does the repository filter by `role="sensor"`?
- What proves that moisture and light defaults are different?
