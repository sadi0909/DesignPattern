from dataclasses import dataclass, field
from uuid import UUID


@dataclass(slots=True)
class Sensor:
    id: UUID | None
    device_type: str
    display_name: str
    default_config: dict[str, object] = field(default_factory=dict)
