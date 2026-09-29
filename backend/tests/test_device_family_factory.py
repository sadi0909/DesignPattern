from domain.devices.family_factory import (
    EdgeHardwareFactory,
    SimulationDeviceFactory,
    UnsupportedDeviceFamilyError,
    get_family_factory,
)


def test_simulation_factory_returns_four_devices():
    devices = SimulationDeviceFactory().create_device_set()

    assert len(devices) == 4
    assert {device.device_family for device in devices} == {"simulation"}
    assert {device.role for device in devices} == {"sensor", "actuator"}
    assert sum(device.role == "sensor" for device in devices) == 2
    assert sum(device.role == "actuator" for device in devices) == 2
    assert {device.device_type for device in devices} == {
        "moisture_sensor",
        "light_sensor",
        "water_pump",
        "grow_light",
    }


def test_edge_factory_differs_from_simulation():
    simulation_devices = SimulationDeviceFactory().create_device_set()
    edge_devices = EdgeHardwareFactory().create_device_set()

    assert {device.device_family for device in edge_devices} == {"edge"}
    assert {device.default_config["protocol"] for device in simulation_devices} == {"sim"}
    assert {device.default_config["protocol"] for device in edge_devices} == {"gpio-stub"}
    assert {device.device_type for device in edge_devices} == {
        device.device_type for device in simulation_devices
    }
    assert {
        device.display_name for device in edge_devices
    } != {device.display_name for device in simulation_devices}


def test_factory_lookup_normalizes_family_and_rejects_unknown_keys():
    assert get_family_factory(" EDGE ").family_key == "edge"
    try:
        get_family_factory("cloud")
    except UnsupportedDeviceFamilyError as exc:
        assert "Unsupported device family" in str(exc)
    else:
        raise AssertionError("unknown device families should be rejected")
