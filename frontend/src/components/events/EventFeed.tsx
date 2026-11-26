import { useCallback, useEffect, useState } from "react";
import { Skeleton } from "../../components/ui/Skeleton";
import {
  fetchAlerts,
  type AlertDto,
  type AlertSeverity,
} from "../../services/api";
import { subscribeRealtime } from "../../services/realtime";

// WebSocket pushes new alerts immediately; this slower GET reconciles any
// events missed while the socket was down or reconnecting.
const FALLBACK_POLL_MS = 30000;

type AlertFilter = "active" | "all";

const severityStyles: Record<AlertSeverity, string> = {
  info: "bg-sky-100 text-sky-800",
  warning: "bg-warn-100 text-warn-800",
  critical: "bg-error-100 text-error-800",
};

const severityRank: Record<AlertSeverity, number> = {
  info: 1,
  warning: 2,
  critical: 3,
};

function formatTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "medium",
  });
}

export function EventFeed() {
  const [alerts, setAlerts] = useState<AlertDto[]>([]);
  const [filter, setFilter] = useState<AlertFilter>("active");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const load = useCallback(async () => {
    try {
      const rows = await fetchAlerts({
        status: filter === "active" ? "active" : undefined,
        limit: 50,
      });
      setAlerts(rows);
      setError(null);
      setLastUpdated(new Date());
    } catch {
      setError("Unable to load alerts. Check that the API is running.");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    setLoading(true);
    void load();
    const timer = window.setInterval(() => void load(), FALLBACK_POLL_MS);
    return () => window.clearInterval(timer);
  }, [load]);

  useEffect(
    () =>
      subscribeRealtime((event) => {
        if (event.type !== "alert.created") return;
        const alert = event.payload as AlertDto | null;
        if (!alert || typeof alert.id !== "string" || alert.status !== "active") {
          return;
        }
        setAlerts((current) => {
          if (current.some((row) => row.id === alert.id)) return current;
          return [alert, ...current].slice(0, 50);
        });
        setLastUpdated(new Date());
      }),
    [],
  );

  const visibleAlerts = [...alerts].sort(
    (left, right) =>
      severityRank[right.severity] - severityRank[left.severity] ||
      new Date(right.created_at).getTime() - new Date(left.created_at).getTime(),
  );

  return (
    <div className="mt-4 rounded-lg bg-slate-50 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">
            {filter === "active" ? "Active alerts" : "All alerts"}
          </h3>
          <p className="text-xs text-slate-500">
            Live over WebSocket; GET /api/alerts every 30 seconds reconciles missed events.
            {lastUpdated && ` Last updated ${lastUpdated.toLocaleTimeString()}.`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div
            role="group"
            aria-label="Alert filter"
            className="flex rounded-md border border-slate-300 bg-white p-0.5"
          >
            {(["active", "all"] as const).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setFilter(option)}
                aria-pressed={filter === option}
                className={`rounded px-2 py-1 text-xs font-medium ${
                  filter === option
                    ? "bg-slate-800 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {option === "active" ? "Active" : "All"}
              </button>
            ))}
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
      </div>

      {error && (
        <p className="mt-3 text-sm text-error-600" role="alert">
          {error}
        </p>
      )}

      {loading ? (
        <Skeleton rows={3} className="mt-4" />
      ) : visibleAlerts.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          {filter === "active"
            ? "No active alerts. Readings within their zone thresholds and successful commands produce no alerts."
            : "No alerts recorded yet."}
        </p>
      ) : (
        <ul className="mt-4 max-h-96 divide-y divide-slate-200 overflow-y-auto pr-1">
          {visibleAlerts.map((alert) => (
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
                  {filter === "all" && ` · ${alert.status}`}
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
