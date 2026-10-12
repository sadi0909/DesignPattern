# Phase 1 — Skeleton questions

**Pattern / focus:** Course intro and an empty-but-running three-tier skeleton (no GoF pattern this phase).

## A. Pattern

1. In your own words, what is a design pattern? What is it *not*

Ans: A design pattern is a type of strategy when coding or developing while thinking steps ahead so that a scalable system could be built. It is not a framework or some package. It helps build structure.

2. Name the three GoF pattern families. For each family, give one-sentence: what kind of design problem it addresses. Then place **Factory Method** and **Strategy** into the correct family.

Ans: 1. Creational - It helps create objects flexibly without hardwiring constructors into every caller.
2. Structural - composing clauses and interfaces into larger structures, fitting pieces together without rewriting callers.
3. Behavioral- It helps understand how objects collaborate and distribute responsibility.
 - Factory method in creational family. Because it helps delegate object creation to creator subclasses.
- I would put "strategy" into behavioral.

3. A teammate wants to add a pattern “because it is on the course list,” even though the feature is small and unlikely to grow. When should you **skip** a pattern? What risk do you take if you apply one too early?

Ans: I would skip a pattern when I see that a problem is not recurring, or the feature is small and unlikely to grow. Because we have to let the problem design the pattern or select the pattern design, and a small problem would unlikely suggest or fit into any that the design pattern teaches. And applying one too early causes complexity in the development process. For example, extra classes that are kind of an exaggeration. The main goal of design pattern is to face some hardship at the beginning, so that in future, when the project grows, it becomes manageable and scalable.

But when a project does not require that in the future, then applying it at the present becomes a painful management.

## B. This phase of the application

4. Why does Phase 1 ship a vertical slice that does almost no greenhouse business logic? What does “empty but running” prove that a folder of unimplemented classes would not?

Ans: Phase 1 is mainly about proving that the whole system can actually run, not about building the greenhouse business logic yet. We want to make sure that Postgres works, the Alembic migration works, the API can connect to the database, /health works, Scalar works, and the React frontend can communicate with the backend.

The reason for making it "empty but running" is that an empty folder with a lot of classes only proves that we can create classes. It does not prove that the actual system works.

For example, if there is a problem with the database connection, the ports, CORS, migrations, imports, or environment variables, we can find it now before adding business logic. This makes debugging much easier.

It is basically like building the greenhouse itself before planting anything. We first make sure the walls, electricity, water, and other infrastructure work. Then we can start adding the actual plants and functionality later. In this case, table and sensors API from phase 2.§	

5. List the four backend layer packages used in this course (`domain`, `application`, `infrastructure`, `interfaces/api`). For each, state what belongs there and give one example of something that must **not** live in `domain`.

Ans: The four backend layers are:

domain/ — This contains the actual business concepts and business rules. Things like entities, value objects, and interfaces related to the business belong here. It should stay independent from frameworks and external technologies.
application/ — This is where the use cases and orchestration live. It coordinates the domain with the infrastructure and handles things like application services and DTOs.
infrastructure/ — This contains the technical implementation details, such as database connections, repositories, configuration, and external service adapters.
interfaces/api/ — This is the HTTP/API layer. It contains things like FastAPI routes, request and response handling, CORS, and Scalar setup.

In Phase 1, the domain and application packages are basically empty because we do not have business functionality yet. The infrastructure already has settings.py and db.py, while the API has main.py and health.py.

Something that should not be inside domain is something like a FastAPI route or a SQLAlchemy model. Those are implementation details, not business rules.



6. What does `GET /health` return, and why does it check the database instead of only reporting that the HTTP process is up? Why is API documentation served at `/scalar`, and why is `/docs` disabled?


Ans: The /health endpoint returns:

{ "status": "ok", "db": "ok" }

when the database is working, and:

{ "status": "degraded", "db": "fail" }

when the database is not responding.

The reason we check the database is because an API being alive does not necessarily mean that the system is actually working. The backend could still be running while the database is completely down.

So checking the database gives us more useful information. It tells us not only that the API process is alive, but also that the main thing the application depends on is reachable.

For documentation, we use Scalar at /scalar because that is the documentation tool for this project. It uses the live OpenAPI schema, so the documentation matches the running API.

/docs is disabled because Swagger is not needed here. Having both Scalar and Swagger would just create two different documentation surfaces, which could eventually become inconsistent.



7. Phase 1 requires Alembic (or equivalent) with a **baseline** migration and **no** business tables such as `devices`. Why introduce the migration toolchain before any product schema? What would go wrong if you created tables by hand in Postgres and only added migrations later?


Ans: The main reason is to make sure the migration system is working before we start depending on it.

The baseline migration does not create any business tables, but it proves that Alembic is connected to the correct database and that migrations can actually be applied. After that, Phase 2 can add the real devices migration on top of a known starting point.

I think this is important because if we create tables manually first and only introduce migrations later, the database history and the actual database can become different.

For example, one developer might have created a table manually while another developer does not have it. Then when the migration is added, Alembic does not really know what happened before it.

It also makes it harder to recreate the database from scratch, and rollback becomes unreliable because there is no proper migration history.

So having Alembic from the beginning means that the schema has a proper history and every change can be reproduced and reviewed.



## C. Compare, contrast, and scenarios

8. Explain **dependency direction** in this skeleton: which layers may import which? Why must domain code not import FastAPI, SQLAlchemy, or Pydantic models used as HTTP schemas?


Ans: The dependency direction is basically from the outside toward the inside:

Browser
   ↓
interfaces/api
   ↓
application
   ↓
domain

infrastructure → domain

The API layer can call the application layer. The application layer can use the domain and infrastructure. Infrastructure can implement things defined by the domain.

But the domain should not depend on these outer layers.

For example, the domain should not import FastAPI, SQLAlchemy, or Pydantic HTTP models because those are technologies used to implement the system, not part of the business rules.

The main goal is to keep the business logic independent.

That way, we can change FastAPI, change the ORM, or change the database implementation without having to rewrite the actual business rules.

It also makes testing easier because we can test domain logic without starting a web server or connecting to a real database.

So the idea is basically that the business rules should not know how the outside world implements them.



9. The frontend cannot show a healthy badge. A classmate blames “the patterns.” What should you check first (stack, CORS/proxy, health JSON), and why is that a Phase 1 concern rather than a later pattern concern?


Ans: I would not blame the patterns first because the patterns are not even involved in this part of the system yet.

I would first check whether the backend is actually running by calling:

GET /health

and checking whether it returns something like:

{ "status": "ok", "db": "ok" }

Then I would check whether Postgres is healthy in Docker.

After that, I would check CORS and the Vite proxy, because the frontend and backend are running on different ports. If the browser cannot reach the backend, the badge cannot work even if the backend itself is fine.

Then I would check whether the frontend is expecting the correct JSON structure and whether VITE_API_BASE_URL is pointing to the correct API.

Finally, I would check the browser console for React or runtime errors.

This is a Phase 1 concern because all of these things are part of the basic system pipeline. Phase 1 exists to prove that the frontend, backend, database, configuration, and communication between them actually work.

The GoF patterns come later, so blaming them for a health badge that cannot load would basically be blaming the wrong part of the system.



10. Course completion is at **Phase 12**, not Phase 1. What is still missing after a successful skeleton, and how do later phases add behaviour without rewriting the foundations you laid here?

Ans: After Phase 1, we basically have the foundation of the application, but we do not really have the greenhouse product yet.

We already have things like Postgres, the health check, Scalar, the Alembic baseline, the React dashboard shell, and the layered backend structure.

What is still missing is most of the actual functionality: the devices table, sensor and actuator models, the GoF patterns, automation logic, events and alerts, WebSockets, the real API routes, authentication, and the rest of the database schema.

The important part is that later phases should add to the foundation instead of rebuilding it.

For example, Phase 2 can add the devices migration and domain classes without changing the overall folder structure. Later phases can keep adding services, repositories, routes, and pattern implementations into the places that already exist.

This is basically the same idea as the reason for Phase 1 being "empty but running". We are setting up the structure early so that when the system grows, we do not have to move everything around.

So later phases should be filling the rooms, not moving the walls.
