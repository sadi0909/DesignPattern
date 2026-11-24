import { useCallback, useEffect, useState } from "react";
import {
  fetchAlerts,
  type AlertDto,
  type AlertSeverity,
} from "../../services/api";

// Phase 11 polls; Phase 12 replaces this with the realtime subscription.
const POLL_INTERVAL_MS = 5000;

const severityStyles: Record<AlertSeverity, string> = {
  info: "bg-sky-100 text-sky-800",
  warning: "bg-amber-100 text-amber-800",
  critical: "bg-red-100 text-red-800",
};

function formatTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "medium",
  });
}

export function EventFeed() {
  const [alerts, setAlerts] = useState<AlertDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(async () => {
    try {
      const rows = await fetchAlerts({ status: "active", limit: 50 });
      setAlerts(rows);
      setError(null);
      setLastUpdated(new Date());
    } catch {
      setError("Unable to load alerts. Check that the API is running.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  return (
    <div className="mt-4 rounded-lg bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Active alerts</h3>
          <p className="text-xs text-slate-500">
            Polling every 5 seconds. Live push arrives in Phase 12.
            {lastUpdated && ` Last updated ${lastUpdated.toLocaleTimeString()}.`}
          </p>
        </div>
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
        <p className="mt-4 text-sm text-slate-500">Loading alerts…</p>
      ) : alerts.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No active alerts. Readings within their zone thresholds and successful commands
          produce no alerts.
        </p>
      ) : (
        <ul className="mt-4 divide-y divide-slate-200">
          {alerts.map((alert) => (
            <li key={alert.id} className="flex flex-wrap items-start gap-3 py-3">
              <span
                className={`rounded-full px-2 py-1 text-xs font-medium ${severityStyles[alert.severity]}`}
              >
                {alert.severity}
              </span>
              <div className="min-w-48 flex-1">
                <p className="text-sm text-slate-800">{alert.message}</p>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  {alert.event_type}
                  {alert.device_id && ` · device ${alert.device_id.slice(0, 8)}`}
                </p>
              </div>
              <time className="whitespace-nowrap text-xs text-slate-500">
                {formatTime(alert.created_at)}
              </time>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
