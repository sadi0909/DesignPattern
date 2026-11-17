import { useEffect, useState, type FormEvent } from "react";
import {
  applyActuatorCommand,
  fetchActuatorExecutions,
  fetchDevices,
  type ActuatorExecutionDto,
  type DeviceDto,
} from "../../services/api";

function formatTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "medium",
  });
}

export function ExecutionLog() {
  const [executions, setExecutions] = useState<ActuatorExecutionDto[]>([]);
  const [actuators, setActuators] = useState<DeviceDto[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [command, setCommand] = useState("start_pump");
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const [rows, devices] = await Promise.all([
        fetchActuatorExecutions(20),
        fetchDevices({ role: "actuator" }),
      ]);
      setExecutions(rows);
      setActuators(devices);
      setDeviceId((current) => current || devices[0]?.id || "");
    } catch {
      setError("Unable to load actuator executions. Check that the API is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleApply(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!deviceId || !command.trim()) return;
    setApplying(true);
    setNotice(null);
    setError(null);
    try {
      await applyActuatorCommand(deviceId, command.trim());
      setNotice("Command applied. The attempt is recorded below.");
      setExecutions(await fetchActuatorExecutions(20));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The apply attempt failed.");
      // A blocked attempt is still a recorded row, so refresh best-effort.
      try {
        setExecutions(await fetchActuatorExecutions(20));
      } catch {
        // Keep the policy error visible instead of replacing it with a fetch error.
      }
    } finally {
      setApplying(false);
    }
  }

  const deviceNames = new Map(actuators.map((device) => [device.id, device.display_name]));

  return (
    <div className="mt-4 rounded-lg bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-800">Recent executions</h3>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="rounded-md border border-slate-300 bg-white px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      <form onSubmit={(event) => void handleApply(event)} className="mt-3 flex flex-wrap items-end gap-2">
        <label className="text-xs font-medium text-slate-600">
          Actuator
          <select
            value={deviceId}
            onChange={(event) => setDeviceId(event.target.value)}
            disabled={applying || actuators.length === 0}
            className="mt-1 block rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800"
          >
            {actuators.length === 0 && <option value="">No actuators</option>}
            {actuators.map((device) => (
              <option key={device.id} value={device.id}>
                {device.display_name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-medium text-slate-600">
          Command
          <input
            value={command}
            onChange={(event) => setCommand(event.target.value)}
            disabled={applying}
            className="mt-1 block w-40 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800"
          />
        </label>
        <button
          type="submit"
          disabled={applying || !deviceId || !command.trim()}
          className="rounded-md bg-emerald-600 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {applying ? "Applying…" : "Apply demo command"}
        </button>
      </form>

      {notice && (
        <p className="mt-3 text-sm text-emerald-700" role="status" aria-live="polite">
          {notice}
        </p>
      )}
      {error && (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading executions…</p>
      ) : executions.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No actuator executions yet. Apply a demo command to create the first log row.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-xs">
            <thead className="border-b border-slate-200 text-slate-500">
              <tr>
                <th className="px-2 py-2 font-medium">Time</th>
                <th className="px-2 py-2 font-medium">Device</th>
                <th className="px-2 py-2 font-medium">Result</th>
                <th className="px-2 py-2 font-medium">Policies</th>
                <th className="px-2 py-2 font-medium">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {executions.map((execution) => (
                <tr key={execution.id}>
                  <td className="whitespace-nowrap px-2 py-2 text-slate-600">
                    {formatTime(execution.created_at)}
                  </td>
                  <td className="px-2 py-2 text-slate-700">
                    {deviceNames.get(execution.device_id) ?? execution.device_id.slice(0, 8)}
                  </td>
                  <td className="px-2 py-2">
                    <span
                      className={`rounded-full px-2 py-1 font-medium ${
                        execution.success
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {execution.success ? "success" : "failed"}
                    </span>
                  </td>
                  <td className="px-2 py-2 text-slate-600">
                    {execution.policy_applied.join(", ") || "—"}
                  </td>
                  <td className="px-2 py-2 text-slate-600">{execution.message ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
