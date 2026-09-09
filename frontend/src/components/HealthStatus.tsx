import { useEffect, useState } from "react";
import { fetchHealth, type HealthResponse } from "../services/api";

export function HealthStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let mounted = true;
    const interval = setInterval(async () => {
      try {
        const data = await fetchHealth();
        if (mounted) {
          setHealth(data);
          setError(false);
        }
      } catch {
        if (mounted) {
          setError(true);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }, 10000);

    fetchHealth()
      .then((data) => {
        if (mounted) {
          setHealth(data);
          setError(false);
        }
      })
      .catch(() => {
        if (mounted) setError(true);
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (loading) return <span className="inline-flex items-center gap-1.5 text-sm text-slate-500">Checking…</span>;
  if (error || !health) return <span className="inline-flex items-center gap-1.5 text-sm text-red-600">API: unreachable</span>;

  // Tailwind v4 scans source text for class names, so full class strings are written out
  // instead of building them dynamically (bg-${color}-100 would never be generated).
  const apiOk = health.status === "ok";
  const dbOk = health.db === "ok";

  return (
    <span className="inline-flex items-center gap-2 text-sm font-medium">
      <span
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
          apiOk ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700"
        }`}
      >
        API: {health.status}
      </span>
      <span
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
          dbOk ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
        }`}
      >
        DB: {health.db}
      </span>
    </span>
  );
}