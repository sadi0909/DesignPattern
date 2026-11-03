# Phase 8 — State questions

**Pattern / focus:** State.

**Read first:** [Guide 08](../../materials/guides/08-state.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example support-ticket states) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to actuator lifecycle, persisted state, and `allowed_commands` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of the State pattern in plain language. What problem appears when lifecycle is modelled as boolean flags and scattered `if` guards?

2. Name the participants (**context**, **state interface**, **concrete states**, **client**). How does a successful command lead to a **transition**, and where do **guards** live?

3. What is `allowed_commands` (or equivalent) for? Why is exposing “what can I do **now**?” better than letting the UI guess from a raw state string?

## B. This phase of the application

4. Which actuator states did you implement (for example idle, running, error)? Sketch the **legal** transitions (which command or event moves idle → running, running → idle, into error, and out of error).

5. Why is actuator state stored in `actuator_states` (or equivalent) rather than only in process memory? What must still be true after you restart the backend?

6. An **illegal** transition must raise a domain error and **must not** update the database. Why? Which HTTP status is reasonable for that case (400 or 409), and why should the rule live in the domain rather than in React?

7. Device JSON gains `state` and `allowed_commands`. How does the dashboard use those fields (badges, disable illegal buttons)? How does this prepare **Phase 10 Command**?

## C. Compare, contrast, and scenarios

8. Contrast State with **Strategy**. Both look like “context delegates to an object.” Who typically **changes** the active object, and is the variation a **lifecycle** or a **selectable policy**? Give a greenhouse example of each (this phase vs Phase 6).

9. Contrast State with a pile of booleans (`is_running`, `is_fault`, `is_maintenance`). Why do illegal combinations of flags appear, and how do explicit state objects (or a transition table) prevent that?

10. A classmate puts HTTP status mapping or SQLAlchemy commits **inside** a concrete state class. Another state mutates a flag directly and skips `transition` / `set_state`. Explain why each is a trap.
