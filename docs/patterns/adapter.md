# Adapter — Phase 5

## Problem

Sensor drivers speak foreign dialects. The simulation driver invents plausible values, while the mocked vendor SDK returns a raw payload with nested objects, odd field names (`reading_tenths`, `uom_code`, `captured_epoch_ms`), scaled integers, vendor unit codes (`PCT`, `KLX`), and epoch milliseconds. If business code speaks those dialects directly, every caller re-implements parsing, scaling, and unit conversion, and swapping a vendor means rewriting services. The smell is **business code speaking a foreign protocol**.

## Solution

Adapter converts the interface of a class into another interface clients expect. This phase splits each integration into a **port** (the application-facing interface) and thin **adapters** (the translators):

| Role | In Phase 5 |
|------|------------|
| **Target (port)** | `SensorPort.read(device) -> Reading`, `ActuatorPort.apply(device_id, command, payload)` |
| **Adaptee** | Simulation driver logic, mocked vendor SDK payload |
| **Adapter** | `SimulationSensorAdapter`, `VendorStubSensorAdapter`, `SimulationActuatorAdapter` |
| **Client** | `ReadingService`, the sensors router, the dashboard card |

Every adapter returns the same normalized `Reading` value object (`device_id`, `value`, `unit`, `source`, `recorded_at`). The vendor adapter **translates** only: field names, integer scaling (deci-percent → percent, tenths of kilolux → lux), unit codes, and epoch milliseconds → timezone-aware datetime. Its `translate(device, raw)` is a pure function so unit tests can pass raw payloads without HTTP. It does **not** decide irrigation policy — that stays in domain/Strategy (Phase 6). Each reading carries `source` (`"simulation"` or `"vendor"`) so history records which adapter produced it.

The API router and application service depend on `SensorPort` only; vendor-shaped types never cross the adapter boundary. The one allowed seam to concrete classes is the selector:

- **Selection rule:** an explicit `default_config["protocol"]` wins (`sim` → simulation adapter, `gpio-stub` → vendor-stub adapter); otherwise fall back to `device_family` (`simulation` → simulation adapter, `edge` → vendor-stub adapter). Unknown protocols raise `SensorReadError` (HTTP 400).

`POST /api/sensors/{id}/read` runs: load device (missing → 404) → select adapter → `port.read()` → append to `sensor_readings` → map to `ReadingDto`. Readings are **appended** (`sensor_readings`, indexed on `(device_id, recorded_at DESC)`), so history grows and Phase 6 Strategy can consume real persisted data.

The actuator side ships `ActuatorPort` plus `SimulationActuatorAdapter` now: `apply()` records the command intent in memory and logs it — no GPIO. Phase 9 wraps this exact class with decorators.

## Object adapter, not class adapter

These are **object adapters**: each adapter *has* (or stands in for) the adaptee and implements the port by composition. The GoF class-adapter alternative uses multiple inheritance to adapt an interface; modern code prefers composition because it is looser, works with any adaptee instance, and avoids fragile base classes.

## Code paths

- Ports: `backend/src/domain/sensors/ports.py`, `backend/src/domain/actuators/ports.py`
- Normalized value object: `backend/src/domain/sensors/reading.py`
- Sensor adapters: `backend/src/infrastructure/adapters/sensors/simulation.py`, `vendor_stub.py`
- Selection rule: `backend/src/infrastructure/adapters/sensors/selector.py`
- Actuator stub: `backend/src/infrastructure/adapters/actuators/simulation.py`
- ORM + repository: `backend/src/infrastructure/persistence/models.py` (`ReadingRow`), `reading_repository.py`
- Use case: `backend/src/application/readings/service.py` (+ `dto.py`)
- HTTP endpoints: `backend/src/interfaces/api/sensors.py`
- Sensor card "Read now": `frontend/src/features/sensors/SensorList.tsx`

## Extension exercise (third vendor)

Add a second vendor driver whose raw payload uses yet another shape (for example XML or an epoch in seconds). Write `VendorTwoSensorAdapter(SensorPort)` with its own `translate`, map its protocol key in `select_sensor_adapter`, and keep `Reading`, `sensor_readings`, `ReadingService`, the routes, and the UI untouched — only the new adapter and one selector entry change. That is Adapter's payoff: the boundary absorbs vendor churn.
