import { useEffect, useState } from "react";
import { ACTIVE_LOCATION_STORAGE_KEY, fetchOverview, type LocationOverviewDto } from "../../services/api";

export function OverviewPanel() {
  const [draftId, setDraftId] = useState(() => window.localStorage.getItem(ACTIVE_LOCATION_STORAGE_KEY) ?? "");
  const [locationId, setLocationId] = useState(draftId.trim());
  const [refresh, setRefresh] = useState(0);
  const [overview, setOverview] = useState<LocationOverviewDto | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!locationId) {
      setOverview(null);
      setError(null);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setOverview(null);
    setError(null);
    setLoading(true);
    // Defer the request so React StrictMode's development-only setup/cleanup does not fetch twice.
    const timer = window.setTimeout(() => {
      fetchOverview(locationId)
        .then((result) => { if (!cancelled) setOverview(result); })
        .catch((err: unknown) => {
          if (!cancelled) setError(err instanceof Error ? err.message : "Unable to load overview.");
        })
        .finally(() => { if (!cancelled) setLoading(false); });
    }, 0);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [locationId, refresh]);

  function handleLoad(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextId = draftId.trim();
    if (nextId === locationId) setRefresh((value) => value + 1);
    else setLocationId(nextId);
  }

  return (
    <div className="mt-4 space-y-4">
      <form className="flex flex-wrap items-end gap-2" onSubmit={handleLoad}>
        <div className="min-w-0 flex-1">
          <label htmlFor="overview-location-id" className="mb-1 block text-sm font-medium text-slate-700">Location ID</label>
          <input id="overview-location-id" value={draftId} onChange={(event) => setDraftId(event.target.value)}
            placeholder="Paste a location ID" className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-xs" />
        </div>
        <button type="submit" className="rounded-md border border-emerald-600 px-3 py-2 text-sm text-emerald-700">Load / refresh</button>
      </form>
      {!locationId && <p className="text-sm text-slate-500">Save a location configuration or enter its ID to see its overview.</p>}
      {loading && <p className="text-sm text-slate-500" role="status">Loading overview…</p>}
      {error && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
      {overview && (
        <div className="space-y-3" aria-live="polite">
          <h3 className="font-semibold text-slate-900">{overview.location.name}</h3>
          <p className="text-xs text-amber-800">Device counts and readings are global: devices are not yet assigned to locations. Recommendations use the latest global moisture reading.</p>
          <section className="rounded-md bg-slate-50 p-3 text-sm">
            <h4 className="font-semibold">Devices (global)</h4>
            <p>Sensors: {overview.device_counts.sensor} · Actuators: {overview.device_counts.actuator}</p>
          </section>
          <section className="rounded-md bg-slate-50 p-3 text-sm">
            <h4 className="font-semibold">Latest sensor readings (global)</h4>
            {overview.latest_readings.length === 0 ? <p>No readings recorded yet.</p> : (
              <ul className="space-y-2">
                {overview.latest_readings.map((reading) => (
                  <li key={reading.device_id}>
                    <span>{reading.value} {reading.unit}</span>
                    <p className="break-all text-xs text-slate-500">{reading.device_id} · {new Date(reading.recorded_at).toLocaleString()}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
          <section className="rounded-md bg-slate-50 p-3 text-sm">
            <h4 className="font-semibold">Active strategy</h4>
            <p>{overview.strategy_key ?? "None"}</p>
          </section>
          <section className="rounded-md bg-slate-50 p-3 text-sm">
            <h4 className="font-semibold">Current recommendation</h4>
            {overview.last_recommendation ? <p>{overview.last_recommendation.action}: {overview.last_recommendation.reason}</p> : <p>No recommendation available.</p>}
          </section>
        </div>
      )}
    </div>
  );
}
