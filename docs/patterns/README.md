# Pattern notes

One note per pattern, written after the phase landed. Each follows the same
shape: the problem in this codebase, the seam that solves it, trade-offs, known
limitations, and where the code lives.

| Phase | Pattern | Note | Production seam | Proving tests |
|-------|---------|------|-----------------|---------------|
| 2 | Factory Method | [factory-method.md](factory-method.md) | `domain/sensors/creators.py` | `tests/test_creators.py` |
| 3 | Abstract Factory | [abstract-factory.md](abstract-factory.md) | `domain/devices/family_factory.py` | `tests/test_device_family_factory.py` |
| 4 | Builder | [builder.md](builder.md) | `domain/locations/config_builder.py` | `tests/test_location_builder.py` |
| 5 | Adapter | [adapter.md](adapter.md) | `domain/sensors/ports.py`, `infrastructure/adapters/sensors/` | `tests/test_readings.py` |
| 6 | Strategy | [strategy.md](strategy.md) | `domain/automation/strategy.py` | `tests/test_automation.py` |
| 7 | Facade | [facade.md](facade.md) | `application/overview/facade.py` | `tests/test_overview.py` |
| 8 | State | [state.md](state.md) | `domain/actuators/state.py` | `tests/test_actuator_state.py` |
| 9 | Decorator | [decorator.md](decorator.md) | `infrastructure/adapters/actuators/logging_decorator.py`, `max_runtime_decorator.py` | `tests/test_actuator_decorators.py` |
| 10 | Command | [command.md](command.md) | `domain/commands/`, `application/commands/service.py` | `tests/test_commands.py` |
| 11 | Observer | [observer.md](observer.md) | `domain/events/bus.py`, `application/alerts/subscribers.py` | `tests/test_events.py` |

Phase 12 has no new pattern note: it adds a transport subscriber on the Phase 11
bus. The seam and its tests are described in
[`docs/testing.md`](../testing.md#pattern-seams-and-the-tests-that-prove-them).

## Reading order

For the exam, the useful thread is the sibling comparisons:

- Factory Method vs Abstract Factory — one product vs a coherent kit.
- Strategy vs State — a chosen algorithm vs a lifecycle with legal transitions.
- Adapter vs Facade — translate one interface vs simplify many.
- Command vs calling the port — audit, queue, and undo pressure.
- Observer vs direct calls — the producer stops naming its consumers.

Each note ends with the trade-offs and the cases where the pattern is not worth
its indirection.
