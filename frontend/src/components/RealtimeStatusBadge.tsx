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
    badge: "bg-ok-100 text-ok-700",
    dot: "bg-ok-500",
  },
  connecting: {
    label: "connecting",
    badge: "bg-warn-100 text-warn-700",
    dot: "bg-warn-500",
  },
  down: {
    label: "down",
    badge: "bg-error-100 text-error-700",
    dot: "bg-error-500",
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
