# Phase 7 — Facade (Requirements)

This is the **assignment**. Implement from these requirements. If you get stuck or want to check your design, use the [guided check](guided-check.md) (signatures and partial snippets — not a complete solution).

After you implement, answer the [questions](./questions.md).

## Purpose

Provide a **single read API** for the dashboard that aggregates existing tables through repositories. **No new business schema** — compose what Phases 2–6 already persist.

## Scope and naming rules

- Facade is the only collaborator the overview HTTP handler should call (not five repositories in the router).
- Overview is scoped by **`location_id`**.
- Optional SQL view is allowed; not required.

## Outcome required at end of phase

- `GET` overview for a location returns one DTO: latest readings, device counts, active strategy, last recommendation (computed or cached).
- Dashboard **Overview** page does one fetch and renders cards from that DTO.
- Scalar documents the overview schema.
- Pattern note at `docs/patterns/facade.md`.

---

## Prerequisites

- Phase 6: automation rules + readings in DB.
- Devices, locations, zones exist.

---

## Required architecture for this phase

- **Domain / application:** facade class `get_overview(location_id)` assembling a read model. It may call existing repositories/services; it must not duplicate Strategy/Adapter logic.
- **Infrastructure:** queries/joins in repository layer; watch N+1 (prefer a small number of queries).
- **API:** one overview route; handler calls **only** the facade.
- **Frontend:** Overview page/section from that one response.

---

## Suggested file locations

Paths are relative to **`yourpath\project\`**.

```text
yourpath\project\
├── backend/src/
│   ├── application/overview/dto.py       # LocationOverviewDto
│   ├── application/overview/facade.py    # LocationOverviewFacade
│   └── interfaces/api/overview.py
└── frontend/src/.../OverviewPage.tsx     # or #overview section
```

No new table required.

## Type hints

`LocationOverviewDto` (read model):

| Field | Hint |
|-------|------|
| `location` | `{ id: UUID, name: str }` |
| `device_counts` | `{ sensor: int, actuator: int }` (extend with family counts if useful) |
| `latest_readings` | `list` of `{ device_id: UUID, value: float, unit: str, recorded_at: datetime }` |
| `strategy_key` | `str \| None` |
| `last_recommendation` | `{ action: str, reason: str } \| None` |

Path param: `location_id: UUID`.

---

## Step-by-step implementation requirements

## Step 1 — Overview DTO contract

Define a read DTO that includes at least:

- Location id and name.
- Device counts (by role and/or family).
- Latest readings summary (sensor id, value, unit, recorded_at).
- Active `strategy_key`.
- Last recommendation (call Strategy evaluate internally or store last result — document which).

Acceptance criteria:

- JSON field names are stable and documented in Scalar.
- Missing location → 404.

## Step 2 — Facade implementation

Implement a facade that coordinates existing subsystems.

Requirements:

- Router does not import reading/strategy/device repositories directly.
- Facade stays in application (or domain) — not a “god” ORM model.

Acceptance criteria:

- After a new reading or strategy change, overview reflects DB state without extra React glue.

## Step 3 — Database

**No migration required.** Optional view `greenhouse_overview_v1` (or `location_overview_v1`) if you want to teach views — name it with location terminology.

Acceptance criteria:

- Phase 6 schema unchanged unless you add an optional view migration.

## Step 4 — API and frontend

- `GET /api/locations/{location_id}/overview`.
- Replace `#overview` placeholder with cards bound to the DTO.
- One fetch on load (and optional refresh button).

Acceptance criteria:

- Overview works end-to-end; Scalar shows the schema.

## Step 5 — Tests and docs

- Integration test against seeded DB: overview contains expected keys.
- `docs/patterns/facade.md`: why one entry point, what it hides, N+1 note.

---

## Definition of done

- Single overview endpoint + UI.
- Handler uses only the facade.
- Tests and pattern doc complete.
- No required new tables.

---

## Common pitfalls to avoid

- Re-implementing strategy inside the facade instead of calling the strategy service.
- Five queries per nested loop (N+1) without comment or fix.
- Overview scoped by something other than `location_id`.

---

## Handoff to next phases

- Phase 8 (State) will add actuator lifecycle fields that overview can later include.

→ [Phase 8 — State (requirements)](../phase-08/requirements.md) · [guided check](../phase-08/guided-check.md)
