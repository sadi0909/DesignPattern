import { useEffect, useState } from "react";
import { createSensor, fetchSensors, type SensorDto } from "../../services/api";

export function SensorList() {
  const [sensors, setSensors] = useState<SensorDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState<string | null>(null);

  async function loadSensors() {
    try {
      setError(null);
      setSensors(await fetchSensors());
    } catch {
      setError("Unable to load sensors. Check that the API is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSensors();
  }, []);

  async function handleCreate(type: "moisture" | "light") {
    try {
      setCreating(type);
      setError(null);
      await createSensor(type);
      await loadSensors();
    } catch {
      setError("Unable to create the sensor.");
    } finally {
      setCreating(null);
    }
  }

  return (
    <div className="mt-4 rounded-lg bg-slate-50 p-4">
      <div className="mb-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => void handleCreate("moisture")}
          disabled={creating !== null}
          className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {creating === "moisture" ? "Adding…" : "Add moisture sensor"}
        </button>
        <button
          type="button"
          onClick={() => void handleCreate("light")}
          disabled={creating !== null}
          className="rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
        >
          {creating === "light" ? "Adding…" : "Add light sensor"}
        </button>
      </div>
      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
      {loading ? (
        <p className="text-sm text-slate-500">Loading sensors…</p>
      ) : sensors.length === 0 ? (
        <p className="text-sm text-slate-500">No sensors yet. Add one above.</p>
      ) : (
        <ul className="space-y-2">
          {sensors.map((sensor) => (
            <li key={sensor.id} className="rounded-md border border-slate-200 bg-white p-3">
              <p className="font-medium text-slate-800">{sensor.display_name}</p>
              <p className="text-xs text-slate-500">{sensor.device_type}</p>
              <pre className="mt-2 overflow-x-auto text-xs text-slate-600">
                {JSON.stringify(sensor.default_config, null, 2)}
              </pre>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
