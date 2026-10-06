from abc import ABC, abstractmethod

from domain.devices.entity import Device

from .reading import Reading


class SensorPort(ABC):
    """Application-facing sensor interface (the Adapter "target").

    Concrete adapters translate vendor or simulation driver output into the
    normalized Reading shape. Application code depends on this port only —
    never on a vendor SDK or a simulation driver class.
    """

    @abstractmethod
    def read(self, device: Device) -> Reading:
        """Return one normalized reading for the device."""
        raise NotImplementedError
