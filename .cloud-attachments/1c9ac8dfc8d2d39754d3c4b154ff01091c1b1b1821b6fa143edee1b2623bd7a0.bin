# Phase 8 — State (Requirements)

This is the **assignment**. Implement from these requirements. If you get stuck or want to check your design, use the [guided check](guided-check.md) (signatures and partial snippets — not a complete solution).

After you implement, answer the [questions](./questions.md).

## Purpose

Persist **actuator lifecycle** per device. The API exposes current `state` and `allowed_commands` so the UI (and Phase 10 Command) can show legal actions only.

## Scope and naming rules

- State machine lives in domain (transition table or state objects). Routers must not encode `if state == "idle"` transition rules.
- Persist state in the database; do not keep it only in process memory.
- Illegal transitions are rejected and must not update the stored state.

## Outcome required at end of phase

- Each actuator has a persisted state.
- Device (or actuator) API includes `state` and `allowed_commands`.
- UI shows state badges; illegal transitions are explained (tooltip or error).
- Scalar documents the new fields / transition endpoint if you expose one.
- Pattern note at `docs/patterns/state.md`.

---

## Prerequisites

- Phase 7 overview works; actuators exist from Phase 3 (`role=actuator`).

---

## Required architecture for this phase

- **Domain:** context + states or a transition table (`idle`, `running`, `off`, `error`, `maintenance` — use this set or a documented subset). `allowed_commands` derived from current state.
- **Application:** DTOs including state fields; service that loads, transitions, saves.
- **Infrastructure:** `actuator_states` table (or equivalent) keyed by `device_id`.
- **API:** include state on device read models; optional explicit transition/dev endpoint.
- **Frontend:** badges on actuator cards.

---

## Suggested file locations

Paths are relative to **`yourpath\project\`**.

```text
yourpath\project\
├── backend/src/
│   ├── domain/actuators/state.py         # states / transition table
│   ├── domain/actuators/context.py       # ActuatorContext
│   ├── application/devices/dto.py        # + state, allowed_commands
│   ├── infrastructure/persistence/models.py              # ActuatorStateRow
│   └── infrastructure/persistence/actuator_state_repository.py
└── frontend/src/components/devices/      # badges on actuator cards
```

## Type hints

Domain:

| Name | Hint |
|------|------|
| `state` | `str` — `"off"` \| `"idle"` \| `"running"` \| `"error"` \| `"maintenance"` |
| `allowed_commands` | `list[str]` (e.g. `start_pump`, `stop_pump`) |
| `IllegalTransitionError` | domain error (subclass of `ValueError` or similar) |

ORM `actuator_states`:

| Column | SQL hint |
|--------|----------|
| `device_id` | UUID PK, FK → `devices` |
| `state` | VARCHAR |
| `updated_at` | timestamptz |

Device DTO extra JSON fields: `state: string`, `allowed_commands: string[]`. Optional transition body: `{ "target": string }`.

---

## Step-by-step implementation requirements

## Step 1 — Database

Table `actuator_states`:

| Column | Intent |
|--------|--------|
| `device_id` | PK, FK → `devices` (actuators) |
| `state` | VARCHAR: `off`, `idle`, `running`, `error`, `maintenance` |
| `updated_at` | Timestamptz |

Seed existing actuators to `idle` in the migration or a one-time service call (document which).

Acceptance criteria:

- Autogenerate + apply; every actuator row can resolve a state.

## Step 2 — Domain transitions

Implement guarded transitions. Example legal edges: `idle → running`, `running → idle`, `* → error`, `error → idle` after reset — you may refine, but **write them down** in the pattern doc.

`allowed_commands` is a list of command names Phase 10 will reuse (e.g. `start_pump`, `stop_pump`).

Acceptance criteria:

- Illegal transition raises a domain error and does not persist.
- Unit tests cover legal and illegal edges.

## Step 3 — Persistence and API

Load/save state on transition. Device list/detail DTO gains `state` and `allowed_commands`.

Optional: `POST /api/devices/{id}/transition` for demo; Phase 10 will go through Command.

404 missing actuator; 409 or 400 on illegal transition.

Acceptance criteria:

- Scalar shows the new fields.
- Restart backend; states still correct.

## Step 4 — Frontend

State badges on actuator cards; tooltip or disabled affordance for illegal actions if you already show buttons (full controls can wait until Phase 10).

Acceptance criteria:

- Overview or devices section shows updated state after a successful transition.

## Step 5 — Tests and docs

- Transition table tests.
- DB update asserted on legal transition only.
- `docs/patterns/state.md`.

---

## Definition of done

- `actuator_states` populated.
- Domain guards transitions.
- API exposes `state` + `allowed_commands`.
- UI badges work.
- Tests and pattern doc complete.

---

## Common pitfalls to avoid

- Storing state only on the FastAPI process.
- Allowing `idle → maintenance` (or any edge) without a table/rule.
- Putting transition logic in React.

---

## Handoff to next phases

- Phase 9 (Decorator) wraps actuator ports and logs attempts.
- Phase 10 (Command) must consult `allowed_commands` / state guards before execute.

→ [Phase 9 — Decorator (requirements)](../phase-09/requirements.md) · [guided check](../phase-09/guided-check.md)
