# Factory Method — Phase 2

## Problem

Sensor creation varies by type. If API handlers or application services construct every concrete sensor and repeat its defaults, adding a sensor type creates scattered conditionals and duplicated configuration.

## Solution

The domain defines a `SensorCreator` abstraction with `create_sensor()`. `MoistureSensorCreator` and `LightSensorCreator` implement that factory method and own the defaults for their product. The registry in `domain/sensors/creators.py` maps the short API key (`moisture` or `light`) to a creator.

The application service asks the registry for a creator, creates the domain sensor, and passes it to the repository. The router only parses HTTP input and maps errors to HTTP responses; it does not construct concrete sensor products.

## Code paths

- Product: `backend/src/domain/sensors/entity.py` (`Sensor`)
- Creator hierarchy and registry: `backend/src/domain/sensors/creators.py`
- Client/use case: `backend/src/application/sensors/service.py`
- Persistence boundary: `backend/src/infrastructure/persistence/device_repository.py`
- HTTP boundary: `backend/src/interfaces/api/sensors.py`

## Why this is useful

Adding a new sensor variant means adding a creator with its defaults and registering its key. The service's creation workflow remains unchanged. Domain code remains independent of FastAPI and SQLAlchemy.

## Exercise

Add a temperature sensor creator with a `temperature_sensor` device type, a suitable unit, and a sampling interval. Register it under `temperature`, add a creator test, and extend the API request typing only if needed. Do not put SQLAlchemy or FastAPI code in the creator.
