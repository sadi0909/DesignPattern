import { useEffect, useState } from "react";
import {
  fetchDevices,
  provisionDeviceFamily,
  type ActuatorState,
  type DeviceDto,
  type DeviceFamily,
} from "../../services/api";
import { DeviceFamilySwitcher } from "./DeviceFamilySwitcher";

const stateStyles: Record<ActuatorState, string> = {
  off: "bg-slate-200 text-slate-800",
  idle: "bg-slate-100 text-slate-700",
  running: "bg-emerald-100 text-emerald-800",
  error: "bg-red-100 text-red-800",
  maintenance: "bg-amber-100 text-amber-800",
};

export function DeviceList() {
  const [family, setFamily] = useState<DeviceFamily>("simulation");
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [provisioning, setProvisioning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function loadDevices(selectedFamily: DeviceFamily) {
    try {
      setError(null);
      setDevices(await fetchDevices({ family: selectedFamily }));
    } catch {
      setDevices([]);
      setError("Unable to load devices. Check that the API is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoading(true);
    void loadDevices(family);
  }, [family]);

  async function handleProvision() {
    try {
      setProvisioning(true);
      setError(null);
      await provisionDeviceFamily(family);
      await loadDevices(family);
    } catch {
      setError("Unable to provision this device family.");
    } finally {
      setProvisioning(false);
    }
  }

  return (
    <div className="mt-4 rounded-lg bg-slate-50 p-4">
      <DeviceFamilySwitcher family={family} onFamilyChange={setFamily} disabled={provisioning} />
      <button
        type="button"
        onClick={() => void handleProvision()}
        disabled={provisioning}
        className="mb-4 rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
      >
        {provisioning ? "Provisioning…" : `Provision ${family} kit`}
      </button>
      {error && <p className="mb-3 text-sm text-red-600" role="alert">{error}</p>}
      {loading ? (
        <p className="text-sm text-slate-500">Loading devices…</p>
      ) : devices.length === 0 ? (
        <p className="text-sm text-slate-500">No {family} devices yet. Provision a kit above.</p>
      ) : (
        <ul className="space-y-2">
          {devices.map((device) => (
            <li key={device.id} className="rounded-md border border-slate-200 bg-white p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-medium text-slate-800">{device.display_name}</p>
                <div className="flex gap-2 text-xs font-medium">
                  <span
                    className={`rounded-full px-2 py-1 ${
                      device.role === "sensor"
                        ? "bg-sky-100 text-sky-800"
                        : "bg-amber-100 text-amber-800"
                    }`}
                  >
                    {device.role}
                  </span>
                  <span className="rounded-full bg-violet-100 px-2 py-1 text-violet-800">
                    {device.device_family}
                  </span>
                  {device.role === "actuator" && device.state && (
                    <span
                      className={`rounded-full px-2 py-1 ${stateStyles[device.state]}`}
                      title={`Allowed commands: ${device.allowed_commands.join(", ") || "none"}`}
                    >
                      {device.state}
                    </span>
                  )}
                </div>
              </div>
              <p className="mt-1 text-xs text-slate-500">{device.device_type}</p>
              {device.role === "actuator" && (
                <p className="mt-1 text-xs text-slate-600">
                  Legal commands: {device.allowed_commands.length > 0 ? device.allowed_commands.join(", ") : "none"}
                </p>
              )}
              <pre className="mt-2 overflow-x-auto text-xs text-slate-600">
                {JSON.stringify(device.default_config, null, 2)}
              </pre>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
