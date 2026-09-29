from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Device:
    id: UUID | None
    device_type: str
    role: str
    device_family: str
    display_name: str
    default_config: dict[str, object] = field(default_factory=dict)
