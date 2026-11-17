import { useEffect, useState } from "react";
import {
  executeCommand,
  fetchCommands,
  fetchDevices,
  type CommandLogDto,
  type CommandStatus,
  type DeviceDto,
} from "../../services/api";

const statusStyles: Record<CommandStatus, string> = {
  success: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
  rejected: "bg-amber-100 text-amber-800",
};

function formatTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "medium",
  });
}

export function CommandPanel() {
  const [actuators, setActuators] = useState<DeviceDto[]>([]);
  const [deviceId, setDeviceId] = useState("");
  const [commands, setCommands] = useState<CommandLogDto[]>([]);
  const [level, setLevel] = useState("60");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function load() {
    try {
      setError(null);
      const [devices, history] = await Promise.all([
        fetchDevices({ role: "actuator" }),
        fetchCommands(50),
      ]);
      setActuators(devices);
      setCommands(history);
      setDeviceId((current) => {
        if (devices.some((device) => device.id === current)) return current;
        return devices[0]?.id ?? "";
      });
    } catch {
      setError("Unable to load commands. Check that the API is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const selected = actuators.find((device) => device.id === deviceId) ?? null;
  const allowed = selected?.allowed_commands ?? [];
  const isPump = selected?.device_type === "water_pump";
  const isLight = selected?.device_type === "grow_light";
  const deviceNames = new Map(actuators.map((device) => [device.id, device.display_name]));

  async function submit(commandType: string) {
    if (!selected) return;
    setSubmitting(true);
    setNotice(null);
    setError(null);
    try {
      const payload =
        commandType === "set_light_level" ? { level: Number(level) } : {};
      const result = await executeCommand(selected.id, commandType, payload);
      setNotice(`${result.command_type} recorded as ${result.status}.`);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The command failed.");
      // Rejected and failed attempts are persisted, so refresh the history too.
      try {
        setCommands(await fetchCommands(50));
      } catch {
        // Keep the command error visible instead of replacing it with a fetch error.
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mt-4">
      <div className="rounded-lg bg-slate-50 p-4">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs font-medium text-slate-600">
            Actuator
            <select
              value={deviceId}
              onChange={(event) => setDeviceId(event.target.value)}
              disabled={submitting || actuators.length === 0}
              className="mt-1 block min-w-48 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800"
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
            Light level (0–100)
            <input
              type="number"
              min="0"
              max="100"
              value={level}
              onChange={(event) => setLevel(event.target.value)}
              disabled={submitting}
              className="mt-1 block w-28 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800"
            />
          </label>
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading || submitting}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
          >
            Refresh
          </button>
        </div>

        {selected && (
          <p className="mt-3 text-xs text-slate-600">
            State: <span className="font-semibold">{selected.state ?? "unknown"}</span>
            {" · "}
            Allowed now:{" "}
            <span className="font-mono">{allowed.join(", ") || "none"}</span>
          </p>
        )}

        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void submit("start_pump")}
            disabled={submitting || !isPump || !allowed.includes("start_pump")}
            className="rounded-md bg-emerald-600 px-3 py-2 text-xs font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {submitting ? "Sending…" : "Start pump"}
          </button>
          <button
            type="button"
            onClick={() => void submit("stop_pump")}
            disabled={submitting || !isPump || !allowed.includes("stop_pump")}
            className="rounded-md bg-slate-700 px-3 py-2 text-xs font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Stop pump
          </button>
          <button
            type="button"
            onClick={() => void submit("set_light_level")}
            disabled={submitting || !isLight || !allowed.includes("set_light_level")}
            className="rounded-md bg-amber-500 px-3 py-2 text-xs font-medium text-slate-900 hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Set light level
          </button>
        </div>

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
      </div>

      <div id="commands" className="mt-4">
        <h3 className="mb-2 text-sm font-semibold text-slate-800">Command history</h3>
        {loading ? (
          <p className="text-sm text-slate-500">Loading command history…</p>
        ) : commands.length === 0 ? (
          <p className="text-sm text-slate-500">No commands have been submitted yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead className="border-b border-slate-200 text-slate-500">
                <tr>
                  <th className="px-2 py-2 font-medium">Time</th>
                  <th className="px-2 py-2 font-medium">Device</th>
                  <th className="px-2 py-2 font-medium">Command</th>
                  <th className="px-2 py-2 font-medium">Status</th>
                  <th className="px-2 py-2 font-medium">Message</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {commands.map((command) => (
                  <tr key={command.id}>
                    <td className="whitespace-nowrap px-2 py-2 text-slate-600">
                      {formatTime(command.created_at)}
                    </td>
                    <td className="px-2 py-2 text-slate-700">
                      {deviceNames.get(command.device_id) ?? command.device_id.slice(0, 8)}
                    </td>
                    <td className="px-2 py-2 font-mono text-slate-700">
                      {command.command_type}
                      {Object.keys(command.payload).length > 0 && (
                        <span className="ml-1 text-slate-400">
                          {JSON.stringify(command.payload)}
                        </span>
                      )}
                    </td>
                    <td className="px-2 py-2">
                      <span
                        className={`rounded-full px-2 py-1 font-medium ${statusStyles[command.status]}`}
                      >
                        {command.status}
                      </span>
                    </td>
                    <td className="max-w-xs px-2 py-2 text-slate-600">
                      {command.error_message ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
