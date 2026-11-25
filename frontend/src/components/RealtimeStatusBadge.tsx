import { useEffect, useState } from "react";
import {
  getRealtimeStatus,
  subscribeRealtimeStatus,
  type RealtimeStatus,
} from "../services/realtime";

const statusStyles: Record<
  RealtimeStatus,
  { label: string; badge: string; dot: string }
> = {
  connected: {
    label: "connected",
    badge: "bg-emerald-100 text-emerald-700",
    dot: "bg-emerald-500",
  },
  connecting: {
    label: "connecting",
    badge: "bg-amber-100 text-amber-700",
    dot: "bg-amber-500",
  },
  down: {
    label: "down",
    badge: "bg-red-100 text-red-700",
    dot: "bg-red-500",
  },
};

export function RealtimeStatusBadge() {
  const [status, setStatus] = useState<RealtimeStatus>(getRealtimeStatus);

  useEffect(() => subscribeRealtimeStatus(setStatus), []);

  const style = statusStyles[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold ${style.badge}`}
      title="Live event stream (WS /api/ws)"
    >
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      WS: {style.label}
    </span>
  );
}
