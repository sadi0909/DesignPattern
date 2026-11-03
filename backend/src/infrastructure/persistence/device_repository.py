from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from domain.devices.entity import Device
from domain.sensors.entity import Sensor

from .models import ActuatorStateRow, DeviceRow


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_sensor(self, sensor: Sensor) -> Sensor:
        device = Device(
            id=None,
            device_type=sensor.device_type,
            role="sensor",
            device_family="simulation",
            display_name=sensor.display_name,
            default_config=dict(sensor.default_config),
        )
        return self._to_sensor(self.save_device(device))

    def save_device(self, device: Device) -> Device:
        return self.save_devices([device])[0]

    def save_devices(self, devices: list[Device]) -> list[Device]:
        if not devices:
            return []

        rows = [
            DeviceRow(
                device_type=device.device_type,
                role=device.role,
                device_family=device.device_family,
                display_name=device.display_name,
                default_config=dict(device.default_config),
            )
            for device in devices
        ]
        self._session.add_all(rows)
        self._session.flush()
        self._session.add_all(
            ActuatorStateRow(device_id=row.id, state="idle")
            for row in rows
            if row.role == "actuator"
        )
        self._session.commit()
        for row in rows:
            self._session.refresh(row)
        return [
            self._to_device(row, "idle" if row.role == "actuator" else None) for row in rows
        ]

    def get_device(self, device_id: UUID) -> Device | None:
        row = self._session.execute(
            select(DeviceRow, ActuatorStateRow.state)
            .outerjoin(ActuatorStateRow, ActuatorStateRow.device_id == DeviceRow.id)
            .where(DeviceRow.id == device_id)
        ).one_or_none()
        return None if row is None else self._to_device(*row)

    def list_devices(
        self,
        *,
        device_family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        query = select(DeviceRow, ActuatorStateRow.state).outerjoin(
            ActuatorStateRow, ActuatorStateRow.device_id == DeviceRow.id
        )
        if device_family is not None:
            query = query.where(DeviceRow.device_family == device_family)
        if role is not None:
            query = query.where(DeviceRow.role == role)
        rows = self._session.execute(query.order_by(DeviceRow.created_at.desc())).all()
        return [self._to_device(row, state) for row, state in rows]

    def count_by_role(self) -> dict[str, int]:
        """Count globally: the current device schema has no location association."""
        rows = self._session.execute(
            select(DeviceRow.role, func.count()).group_by(DeviceRow.role)
        ).all()
        return {role: count for role, count in rows}

    def list_sensors(self) -> list[Sensor]:
        devices = self.list_devices(role="sensor")
        return [self._to_sensor(device) for device in devices]

    @staticmethod
    def _to_device(row: DeviceRow, state: str | None = None) -> Device:
        return Device(
            id=row.id,
            device_type=row.device_type,
            role=row.role,
            device_family=row.device_family,
            display_name=row.display_name or row.device_type,
            default_config=dict(row.default_config),
            state=state if row.role == "actuator" else None,
        )

    @staticmethod
    def _to_sensor(device: Device) -> Sensor:
        return Sensor(
            id=device.id,
            device_type=device.device_type,
            display_name=device.display_name,
            default_config=dict(device.default_config),
        )
