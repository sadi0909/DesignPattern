# Abstract Factory — Phase 3

## Problem

The greenhouse needs related sensors and actuators that belong to one environment. A simulation moisture sensor paired with an edge-only actuator can have incompatible configuration and behavior. Choosing each device independently makes that mismatch easy to introduce.

## Solution

`DeviceFamilyFactory` defines a single operation that creates a complete kit. `SimulationDeviceFactory` and `EdgeHardwareFactory` each return two sensors and two actuators, with one family key, family-specific names, and protocol/configuration defaults. `get_family_factory()` resolves the requested family once, so the resulting kit stays internally consistent.

The factories compose Phase 2's `MoistureSensorCreator` and `LightSensorCreator` to retain each sensor's type-specific defaults. Actuators are created alongside those sensors with family-specific configuration. The application service persists the returned domain devices as one kit.

## Factory Method vs Abstract Factory

Factory Method answers **“Which one product?”** Phase 2 uses sensor creators to choose and configure one sensor type. Abstract Factory answers **“Which product line?”** Phase 3 chooses one device family and creates a matching group of sensor and actuator products. Abstract Factory often uses Factory Method-style creators inside each family factory; it complements rather than replaces those creators.

## Code paths

- Unified domain product: `backend/src/domain/devices/entity.py` (`Device`)
- Abstract and concrete family factories: `backend/src/domain/devices/family_factory.py`
- Composed sensor creators: `backend/src/domain/sensors/creators.py`
- Provision/list use case: `backend/src/application/devices/family_service.py`
- Persistence: `backend/src/infrastructure/persistence/device_repository.py`
- HTTP DTO and mapper: `backend/src/application/devices/dto.py`, `backend/src/application/devices/mappers.py`
- Devices API: `backend/src/interfaces/api/devices.py`
- Dashboard family selection and list: `frontend/src/components/devices/`

## Why `Device` is not a DTO

`Device` is a domain object with the fields and rules the application needs; it does not depend on Pydantic or HTTP. `DeviceDto` is an API read model shaped for JSON responses. Dedicated mapper functions convert persisted domain devices into DTOs at the application/API boundary. This keeps persistence and family creation independent from the wire format.

## Extending the families

To add another coherent family, define a `DeviceFamilyFactory` implementation with its own family key and protocol/configuration defaults, then register it in `get_family_factory()`. Reuse the existing sensor creators when their product defaults still apply, and provide matching actuator defaults. Add tests that assert the new kit's family and configuration remain distinct. The list/provision API and dashboard can continue to work through the family abstraction.
