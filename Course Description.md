Introduction
Welcome to a hands-on design patterns course where you learn Gang of Four (GoF) design patterns by building a real application: a smart greenhouse control system with sensors, actuators, location-based zones, automation policies, and an operator dashboard.

Modern applications change constantly: new sensor types, new vendors, new automation rules, new UI panels. Without deliberate structure, every change edits the same hotspots—if chains, duplicated constructors, and business logic tangled with HTTP and SQL.

This course teaches a shared design vocabulary and applies it incrementally in a modular monolith: one Python backend, PostgreSQL, and a React + TypeScript dashboard. You do not study patterns in isolation; each phase introduces one pattern or engineering topic and wires it into the greenhouse project with migrations, API routes, and UI updates.

Work proceeds in fourteen numbered phases, grouped into two tracks:

Track	Phases	Outcome
Required	1–12	Runnable full-stack app: skeleton, all ten course patterns, production REST API, WebSocket fan-out, schema hardening
Optional enrichment	13–14	Operator-grade dashboard polish; tests, pattern documentation, and demo narrative


What you are building
Operators manage locations (greenhouse bays, rooms, or sites) and their zones. Each zone has devices—sensors and actuators—that produce readings, follow automation strategies, transition through states, execute commands with logging, and raise alerts through an event bus. The dashboard shows health, overview data, controls, and a live feed.

In code and APIs you will often use location and location_id instead of “greenhouse”—same domain, clearer naming for tables and routes.



Technology stack
Layer	Technologies
Backend	Python, FastAPI, SQLAlchemy, Alembic
Database	PostgreSQL (typically via Docker Compose)
API documentation	Scalar at /scalar + OpenAPI JSON
Frontend	React, TypeScript, Vite, Tailwind CSS v4
Overall course goals
By the end of the required track (Phases 1–12), you should be able to:

Recognize recurring design problems in code (rigid constructors, flag soup, orchestration leakage, tight coupling to vendors) and name the pattern family that addresses them.
Explain the intent of each pattern covered in the course—in your own words, not textbook paste—and describe when not to use it.
Implement patterns as real seams in the greenhouse codebase: interfaces, collaborators, and extension points that stay testable as requirements grow.
Build and evolve a full-stack application incrementally: Alembic migrations per phase, persisted data in PostgreSQL, React UI that grows with each lab.
Design stable API contracts with DTOs, document them with Scalar, and push domain events over WebSocket without duplicating business logic.
Justify trade-offs between sibling patterns (Factory Method vs Abstract Factory, Strategy vs State, Adapter vs Facade, Command vs a plain method call).
Read and extend a layered codebase: know where domain rules, use cases, persistence, and HTTP wiring belong.


Learning goals by required phase
Phase	Focus	Primary learning outcomes
1	Skeleton	Layered project layout; health check; Alembic baseline; Scalar; React + Tailwind shell
2	Factory Method	Sensor creation via creators; avoid scattered constructors
3	Abstract Factory	Coherent device families (simulation vs edge); DTOs at API boundary
4	Builder	Stepwise location/zone configuration with build() validation
5	Adapter	Sensor/actuator ports; vendor or simulation adapters; sensor_readings persistence
6	Strategy	Interchangeable automation policies per zone/location
7	Facade	Single overview operation aggregating existing subsystems
8	State	Actuator lifecycle with guarded transitions and allowedCommands
9	Decorator	Logging, max runtime, and policies wrapped around actuator execution
10	Command	Encapsulated actuator actions; command history and integration with State
11	Observer	In-process event bus; alert persistence; polled event feed
12	API / WS / hardening	Production /api routes; WebSocket subscriber on EventBus; indexes, FKs, seeds


Optional enrichment goals (Phases 13–14)
Phase	Focus	Primary learning outcomes
13	Dashboard polish	Explicit loading/empty/error states; charts from historical readings; UX cohesion
14	Tests & demo	Test pyramid on pattern seams; integration tests; migration smoke; demo narrative and docs/patterns/
Course structure
Course includes lectures which are split into theory and practical parts. During the theory part, the instructor will cover the daily topic and after that we move to the practical part where students begin to work on the corresponding assignment (phase) related to the weekly topic.

This course doesn't have mandatory lecture attendance requirement, but by attending lectures and completing assignments, students can receive points that will be counted on top of the exam score.
The points earned from lecture attendance will be counted on top of the exam score
e.g. if max points from the exam would be 100 and the points that student can earn from lectures are 10 -> student can earn 110/100 from the exam.
To receive attendance for lectures student must present their work during practical parts.
How to receive points -> attend lectures, complete required tasks during practical sessions and submit the assignment on time.


Weekly workflow
During lectures the parts 1-2 are done along with the teacher.

Instructor assisted (lectures) / theory part

Read the learning guide — start with the Theory section.
Follow along (Part 2) — run stdlib Python demos in pattern guides when provided.


Self-study / practical part

Implement from the phase requirements document.
Verify against the guided check if you are stuck or want to compare signatures.
Answer the phase questions in your own words (Phases 1–11).
Prerequisites and expectations


Assumed background
Comfortable programming in Python or similar languages (classes, typing, basic async awareness for FastAPI).
Basic SQL and relational data modeling.
Familiarity with HTTP APIs and JSON.
Introductory JavaScript/TypeScript and React (components, hooks, fetch).
Using a terminal, Git, and Docker Compose at a beginner-to-intermediate level.


What we expect from you
Implement phases in order—later phases assume earlier schema and seams.
Run migrations forward; do not hand-edit production databases or rewrite old migration files.
Write answers and reflections in your own words.
Treat patterns as responses to real design pressure, not badges to collect.
Evaluation & Grading
Course evaluation will be based on the final exam. The assignments (phases 1-12) are mandatory, but they are not graded by points.






