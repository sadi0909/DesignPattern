from domain.sensors.creators import (
    LightSensorCreator,
    MoistureSensorCreator,
    get_creator,
)


def test_moisture_creator_defaults():
    sensor = MoistureSensorCreator().create_sensor()
    assert sensor.device_type == "moisture_sensor"
    assert sensor.default_config["moisture_threshold_percent"] == 30
    assert sensor.default_config["unit"] == "percent"


def test_light_creator_defaults():
    sensor = LightSensorCreator().create_sensor()
    assert sensor.device_type == "light_sensor"
    assert sensor.default_config["unit"] == "lux"
    assert sensor.default_config != MoistureSensorCreator().create_sensor().default_config


def test_registry_rejects_unknown_type():
    assert get_creator("moisture").create_sensor().device_type == "moisture_sensor"
    try:
        get_creator("temperature")
    except ValueError as exc:
        assert "Unsupported sensor type" in str(exc)
    else:
        raise AssertionError("unknown sensor type should be rejected")
