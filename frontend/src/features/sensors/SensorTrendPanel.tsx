import { useEffect, useMemo, useState } from "react";
import { Skeleton } from "../../components/ui/Skeleton";
import {
  fetchSensorReadings,
  fetchSensors,
  type ReadingDto,
  type SensorDto,
} from "../../services/api";

const RANGE_OPTIONS = [
  { label: "Last hour", hours: 1 },
  { label: "Last 6 hours", hours: 6 },
  { label: "Last 24 hours", hours: 24 },
  { label: "Last 7 days", hours: 24 * 7 },
] as const;

const CHART_WIDTH = 720;
const CHART_HEIGHT = 240;
const PADDING = { top: 16, right: 16, bottom: 28, left: 48 };

function formatTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "short",
  });
}

function TrendChart({ readings, unit }: { readings: ReadingDto[]; unit: string }) {
  const values = readings.map((row) => row.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const innerWidth = CHART_WIDTH - PADDING.left - PADDING.right;
  const innerHeight = CHART_HEIGHT - PADDING.top - PADDING.bottom;
  const x = (index: number) =>
    PADDING.left +
    (readings.length === 1 ? innerWidth / 2 : (index / (readings.length - 1)) * innerWidth);
  const y = (value: number) =>
    PADDING.top + innerHeight - ((value - min) / span) * innerHeight;
  const points = readings.map((row, index) => `${x(index)},${y(row.value)}`).join(" ");
  const last = readings[readings.length - 1];

  return (
    <svg
      viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
      className="mt-3 h-56 w-full"
      role="img"
      aria-label={`${unit} readings over time`}
    >
      {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {
        const lineY = PADDING.top + innerHeight * fraction;
        return (
          <line
            key={fraction}
            x1={PADDING.left}
            x2={CHART_WIDTH - PADDING.right}
            y1={lineY}
            y2={lineY}
            className="stroke-slate-200"
            strokeDasharray="3 3"
          />
        );
      })}
      <text x={PADDING.left - 8} y={PADDING.top + 4} textAnchor="end" className="fill-slate-500 text-[10px]">
        {max.toFixed(1)}
      </text>
      <text
        x={PADDING.left - 8}
        y={PADDING.top + innerHeight}
        textAnchor="end"
        className="fill-slate-500 text-[10px]"
      >
        {min.toFixed(1)}
      </text>
      <text x={PADDING.left} y={CHART_HEIGHT - 8} className="fill-slate-500 text-[10px]">
        {formatTime(readings[0].recorded_at)}
      </text>
      <text
        x={CHART_WIDTH - PADDING.right}
        y={CHART_HEIGHT - 8}
        textAnchor="end"
        className="fill-slate-500 text-[10px]"
      >
        {formatTime(last.recorded_at)}
      </text>
      <polyline
        points={points}
        fill="none"
        strokeWidth={2}
        strokeLinejoin="round"
        strokeLinecap="round"
        className="stroke-ok-600"
      />
      <circle cx={x(readings.length - 1)} cy={y(last.value)} r={3.5} className="fill-ok-600" />
    </svg>
  );
}

export function SensorTrendPanel() {
  const [sensors, setSensors] = useState<SensorDto[]>([]);
  const [sensorId, setSensorId] = useState("");
  const [rangeHours, setRangeHours] = useState<number>(24);
  const [readings, setReadings] = useState<ReadingDto[]>([]);
  const [loadingSensors, setLoadingSensors] = useState(true);
  const [loadingReadings, setLoadingReadings] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoadingSensors(true);
    fetchSensors()
      .then((rows) => {
        if (cancelled) return;
        const moistureSensors = rows.filter((row) => row.device_type === "moisture_sensor");
        setSensors(moistureSensors);
        setSensorId((current) =>
          moistureSensors.some((row) => row.id === current)
            ? current
            : (moistureSensors[0]?.id ?? ""),
        );
      })
      .catch(() => {
        if (!cancelled) setError("Unable to load sensors for the trend chart.");
      })
      .finally(() => {
        if (!cancelled) setLoadingSensors(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  useEffect(() => {
    if (!sensorId) {
      setReadings([]);
      return;
    }
    let cancelled = false;
    const to = new Date();
    const from = new Date(to.getTime() - rangeHours * 60 * 60 * 1000);
    setLoadingReadings(true);
    setError(null);
    fetchSensorReadings(sensorId, 500, {
      from: from.toISOString(),
      to: to.toISOString(),
    })
      .then((rows) => {
        if (!cancelled) setReadings(rows);
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : "Unable to load reading history.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingReadings(false);
      });
    return () => {
      cancelled = true;
    };
  }, [sensorId, rangeHours, reloadToken]);

  const summary = useMemo(() => {
    if (readings.length === 0) return null;
    const values = readings.map((row) => row.value);
    return {
      count: readings.length,
      unit: readings[0].unit,
      latest: readings[readings.length - 1],
      min: Math.min(...values),
      max: Math.max(...values),
    };
  }, [readings]);

  return (
    <div className="mt-4 rounded-lg bg-slate-50 p-4">
      <div className="flex flex-wrap items-end gap-3">
        <label className="text-xs font-medium text-slate-600">
          Moisture sensor
          <select
            value={sensorId}
            onChange={(event) => setSensorId(event.target.value)}
            disabled={loadingSensors || sensors.length === 0}
            className="mt-1 block min-w-48 rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800"
          >
            {sensors.length === 0 && <option value="">No moisture sensors</option>}
            {sensors.map((sensor) => (
              <option key={sensor.id} value={sensor.id}>
                {sensor.display_name}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-medium text-slate-600">
          Range
          <select
            value={rangeHours}
            onChange={(event) => setRangeHours(Number(event.target.value))}
            className="mt-1 block rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-800"
          >
            {RANGE_OPTIONS.map((option) => (
              <option key={option.hours} value={option.hours}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <button
          type="button"
          onClick={() => setReloadToken((value) => value + 1)}
          disabled={loadingSensors || loadingReadings}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      {loadingSensors ? (
        <Skeleton rows={2} className="mt-4" />
      ) : error ? (
        <div className="mt-4 rounded-md bg-error-50 p-3">
          <p className="text-sm text-error-700" role="alert">
            {error}
          </p>
          <button
            type="button"
            onClick={() => setReloadToken((value) => value + 1)}
            className="mt-2 text-sm font-medium text-error-700 underline"
          >
            Retry
          </button>
        </div>
      ) : sensors.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No moisture sensors yet. Add one in Sensors to start charting history.
        </p>
      ) : loadingReadings ? (
        <Skeleton rows={4} className="mt-4" />
      ) : readings.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">No readings in this range.</p>
      ) : summary ? (
        <div>
          <p className="mt-4 text-sm text-slate-700">
            <span className="font-semibold">
              {summary.latest.value.toFixed(1)} {summary.unit}
            </span>
            {" · "}
            {summary.count} readings
            {" · "}
            latest {formatTime(summary.latest.recorded_at)}
            {" · "}
            range {summary.min.toFixed(1)}–{summary.max.toFixed(1)} {summary.unit}
          </p>
          <TrendChart readings={readings} unit={summary.unit} />
        </div>
      ) : null}
    </div>
  );
}
