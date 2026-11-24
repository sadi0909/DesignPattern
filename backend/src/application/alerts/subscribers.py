"""Subscribers that turn domain events into persisted alerts.

The threshold rule lives here, not in the reading pipeline: a reading event is
just "this value was stored". If the rule lived in ``ReadingService`` the
publisher would need zone configuration and alert persistence, which is the
coupling Observer is meant to remove.
"""

from domain.events.bus import EventBus
from domain.events.events import CommandExecuted, ReadingTaken, ThresholdCrossed
from infrastructure.persistence.alert_repository import AlertRepository
from infrastructure.persistence.location_repository import LocationRepository

MOISTURE_DEVICE_TYPE = "moisture_sensor"
MOISTURE_UNIT_PERCENT = "percent"
THRESHOLD_EVENT_TYPE = "threshold.crossed"
COMMAND_FAILED_EVENT_TYPE = "command.failed"


class MoistureThresholdSubscriber:
    """Evaluates persisted moisture readings against each zone's thresholds.

    It publishes :class:`ThresholdCrossed`; it does not write alerts itself, so
    metrics or a future notification subscriber can also react to a crossing.
    """

    def __init__(self, locations: LocationRepository, events: EventBus) -> None:
        self._locations = locations
        self._events = events

    def handle(self, event: ReadingTaken) -> None:
        if event.sensor_type != MOISTURE_DEVICE_TYPE or event.unit != MOISTURE_UNIT_PERCENT:
            return
        if event.location_id is None:
            return

        config = self._locations.get_config(event.location_id)
        if config is None:
            return

        moisture = event.value / 100.0
        for zone in config.location.zones:
            if moisture < zone.moisture_threshold_low:
                self._publish(event, zone.name, moisture, zone.moisture_threshold_low, "below")
            elif moisture > zone.moisture_threshold_high:
                self._publish(event, zone.name, moisture, zone.moisture_threshold_high, "above")

    def _publish(
        self,
        event: ReadingTaken,
        zone_name: str,
        moisture: float,
        threshold: float,
        direction: str,
    ) -> None:
        self._events.publish(
            ThresholdCrossed(
                device_id=event.device_id,
                location_id=event.location_id,
                zone_name=zone_name,
                moisture=moisture,
                threshold=threshold,
                direction="below" if direction == "below" else "above",
            )
        )


class AlertPersistenceSubscriber:
    """Writes alert rows for threshold crossings and failed commands.

    Threshold alerts are de-duplicated while an alert for the same device and
    event type is still ``active``; repeated dry readings therefore do not
    flood the feed. Command failures are recorded per attempt because each one
    is a separate operator-visible incident.
    """

    def __init__(self, alerts: AlertRepository) -> None:
        self._alerts = alerts

    def handle(self, event: object) -> None:
        if isinstance(event, ThresholdCrossed):
            self._on_threshold_crossed(event)
        elif isinstance(event, CommandExecuted) and event.status == "failed":
            self._on_command_failed(event)

    def _on_threshold_crossed(self, event: ThresholdCrossed) -> None:
        if self._alerts.has_active(event.device_id, THRESHOLD_EVENT_TYPE):
            return
        label = "low" if event.direction == "below" else "high"
        self._alerts.record(
            location_id=event.location_id,
            device_id=event.device_id,
            severity=event.severity,
            message=(
                f"Moisture {event.moisture:.1%} is {event.direction} the {label} "
                f"threshold {event.threshold:.1%} in zone {event.zone_name}"
            ),
            event_type=THRESHOLD_EVENT_TYPE,
        )

    def _on_command_failed(self, event: CommandExecuted) -> None:
        message = f"Command {event.command_type} failed"
        if event.error_message:
            message = f"{message}: {event.error_message}"
        self._alerts.record(
            location_id=event.location_id,
            device_id=event.device_id,
            severity="critical",
            message=message,
            event_type=COMMAND_FAILED_EVENT_TYPE,
        )
