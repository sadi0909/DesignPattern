import pytest

from domain.locations.config_builder import LocationConfigBuilder
from domain.locations.entity import schedule_to_dict
from domain.locations.errors import ConfigurationError


def test_build_success():
    config = (
        LocationConfigBuilder()
        .with_location_name("  Lab Site A  ")
        .add_zone(
            "  Bench 1 ",
            0.2,
            0.45,
            {"watering": "08:00"},
        )
        .add_zone("Bench 2", 0.15, 0.5)
        .build()
    )

    assert config.location.name == "Lab Site A"
    assert len(config.location.zones) == 2
    assert config.location.zones[0].name == "Bench 1"
    assert config.location.zones[0].schedule == {"watering": "08:00"}
    assert config.location.zones[1].schedule == {}
    assert config.location.id is None
    assert all(zone.id is None and zone.location_id is None for zone in config.location.zones)


def test_build_requires_name():
    builder = LocationConfigBuilder().add_zone("Bench 1", 0.2, 0.45)

    with pytest.raises(ConfigurationError, match="Location name is required"):
        builder.build()


def test_build_requires_zones():
    builder = LocationConfigBuilder().with_location_name("Lab Site A")

    with pytest.raises(ConfigurationError, match="At least one zone is required"):
        builder.build()


def test_build_rejects_invalid_thresholds():
    for low, high in ((0.45, 0.2), (0.4, 0.4), (-0.1, 0.5), (0.2, 1.1)):
        builder = LocationConfigBuilder().with_location_name("Lab Site A")
        builder.add_zone("Bench 1", low, high)
        with pytest.raises(ConfigurationError):
            builder.build()


def test_built_zone_schedule_is_deeply_immutable():
    original_schedule = {"watering": {"time": "08:00", "days": ["Monday"]}}
    config = (
        LocationConfigBuilder()
        .with_location_name("Lab Site A")
        .add_zone("Bench 1", 0.2, 0.45, original_schedule)
        .build()
    )
    zone = config.location.zones[0]

    original_schedule["watering"]["days"].append("Tuesday")
    assert schedule_to_dict(zone.schedule) == {"watering": {"time": "08:00", "days": ["Monday"]}}

    with pytest.raises(TypeError):
        zone.schedule["watering"]["time"] = "09:00"  # type: ignore[index]
    with pytest.raises(AttributeError):
        zone.schedule["watering"]["days"].append("Tuesday")  # type: ignore[union-attr]


def test_build_rejects_blank_or_duplicate_zone_names():
    blank_builder = LocationConfigBuilder().with_location_name("Lab Site A")
    blank_builder.add_zone("   ", 0.2, 0.45)
    with pytest.raises(ConfigurationError, match="Zone name is required"):
        blank_builder.build()

    duplicate_builder = (
        LocationConfigBuilder()
        .with_location_name("Lab Site A")
        .add_zone("Bench 1", 0.2, 0.45)
        .add_zone(" bench 1 ", 0.1, 0.6)
    )
    with pytest.raises(ConfigurationError, match="Zone names must be unique"):
        duplicate_builder.build()
