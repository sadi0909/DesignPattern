import { useEffect, useState } from "react";
import {
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const [rows, devices] = await Promise.all([
        fetchActuatorExecutions(20),
        fetchDevices({ role: "actuator" }),
      ]);
      setExecutions(rows);
      setActuators(devices);
    } catch {
      setError("Unable to load actuator executions. Check that the API is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

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

      {error && (
        <p className="mt-3 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}

      {loading ? (
        <p className="mt-4 text-sm text-slate-500">Loading executions…</p>
      ) : executions.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No actuator executions yet. Run a command from Controls to create the first entry.
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
