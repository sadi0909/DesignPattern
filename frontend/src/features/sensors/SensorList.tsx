import { useEffect, useState } from "react";
import {
  createSensor,
  fetchSensorReadings,
  fetchSensors,
  readSensor,
  type ReadingDto,
  type SensorDto,
} from "../../services/api";

function sourceBadgeClasses(source: string): string {
  return source === "vendor"
    ? "bg-amber-100 text-amber-800"
    : "bg-emerald-100 text-emerald-800";
}

function SensorCard({ sensor }: { sensor: SensorDto }) {
  const [latest, setLatest] = useState<ReadingDto | null>(null);
  const [loadingLatest, setLoadingLatest] = useState(true);
  const [reading, setReading] = useState(false);
  const [readError, setReadError] = useState<string | null>(null);

  // Load the last persisted reading so history survives a page refresh.
  useEffect(() => {
    let cancelled = false;
    async function loadLatest() {
      try {
        const history = await fetchSensorReadings(sensor.id, 1);
        if (!cancelled) {
          setLatest(history[0] ?? null);
        }
      } catch {
        // Card stays usable even when the history fetch fails.
      } finally {
        if (!cancelled) {
          setLoadingLatest(false);
        }
      }
    }
    void loadLatest();
    return () => {
      cancelled = true;
    };
  }, [sensor.id]);

  async function handleReadNow() {
    try {
      setReading(true);
      setReadError(null);
      setLatest(await readSensor(sensor.id));
    } catch (error) {
      setReadError(error instanceof Error ? error.message : "Unable to read sensor.");
    } finally {
      setReading(false);
    }
  }

  return (
    <li className="rounded-md border border-slate-200 bg-white p-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-medium text-slate-800">{sensor.display_name}</p>
          <p className="text-xs text-slate-500">{sensor.device_type}</p>
        </div>
        <button
          type="button"
          onClick={() => void handleReadNow()}
          disabled={reading}
          className="rounded-md bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {reading ? "Reading…" : "Read now"}
        </button>
      </div>

      {readError && <p className="mt-2 text-sm text-red-600">{readError}</p>}

      {loadingLatest ? (
        <p className="mt-2 text-sm text-slate-500">Loading latest reading…</p>
      ) : latest ? (
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <span className="text-sm font-semibold text-slate-800">
            {latest.value} {latest.unit}
          </span>
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${sourceBadgeClasses(latest.source)}`}
          >
            {latest.source}
          </span>
          <span className="text-xs text-slate-500">
            {new Date(latest.recorded_at).toLocaleString()}
          </span>
        </div>
      ) : (
        <p className="mt-2 text-sm text-slate-500">No readings yet. Use “Read now”.</p>
      )}

      <pre className="mt-2 overflow-x-auto text-xs text-slate-600">
        {JSON.stringify(sensor.default_config, null, 2)}
      </pre>
    </li>
  );
}

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
            <SensorCard key={sensor.id} sensor={sensor} />
          ))}
        </ul>
      )}
    </div>
  );
}
