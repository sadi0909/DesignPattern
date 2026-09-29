from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from uuid import UUID


def _freeze_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_json_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json_value(item) for item in value)
    return value


def _thaw_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    return value


def schedule_to_dict(schedule: Mapping[str, object]) -> dict[str, object]:
    return {key: _thaw_json_value(value) for key, value in schedule.items()}


@dataclass(frozen=True, slots=True)
class Zone:
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: Mapping[str, object] = field(default_factory=dict)
    id: UUID | None = None
    location_id: UUID | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "schedule", _freeze_json_value(self.schedule))


@dataclass(frozen=True, slots=True)
class Location:
    name: str
    zones: tuple[Zone, ...]
    id: UUID | None = None


@dataclass(frozen=True, slots=True)
class LocationConfig:
    location: Location
