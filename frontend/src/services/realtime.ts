/**
 * WebSocket client for live domain events.
 *
 * One shared socket serves every subscriber (the event feed and the header
 * indicator). REST keeps working through `api.ts`; this module only receives
 * the `{ type, payload }` envelopes the backend fan-out publishes.
 */

import { API_BASE_URL } from "./api";

export type RealtimeEvent = { type: string; payload: unknown };
export type RealtimeHandler = (event: RealtimeEvent) => void;
export type RealtimeStatus = "connected" | "connecting" | "down";

const RECONNECT_DELAYS_MS = [500, 1000, 2000, 5000, 10000];

let socket: WebSocket | null = null;
let status: RealtimeStatus = "down";
let reconnectAttempt = 0;
let reconnectTimer: number | null = null;
let closing = false;

const eventHandlers = new Set<RealtimeHandler>();
const statusHandlers = new Set<(status: RealtimeStatus) => void>();

function setStatus(next: RealtimeStatus) {
  if (status === next) return;
  status = next;
  statusHandlers.forEach((handler) => handler(status));
}

function realtimeUrl(): string {
  const base = API_BASE_URL.trim();
  if (base) {
    const url = new URL(base, window.location.origin);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = `${url.pathname.replace(/\/$/, "")}/api/ws`;
    url.search = "";
    url.hash = "";
    return url.toString();
  }
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/ws`;
}

function scheduleReconnect() {
  if (reconnectTimer !== null) return;
  if (eventHandlers.size + statusHandlers.size === 0) return;
  const delay =
    RECONNECT_DELAYS_MS[Math.min(reconnectAttempt, RECONNECT_DELAYS_MS.length - 1)];
  reconnectAttempt += 1;
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, delay);
}

function connect() {
  if (socket || eventHandlers.size + statusHandlers.size === 0) return;
  closing = false;
  setStatus("connecting");

  let ws: WebSocket;
  try {
    ws = new WebSocket(realtimeUrl());
  } catch {
    setStatus("down");
    scheduleReconnect();
    return;
  }
  socket = ws;

  ws.onopen = () => {
    reconnectAttempt = 0;
    setStatus("connected");
  };
  ws.onmessage = (message) => {
    try {
      const event = JSON.parse(String(message.data)) as RealtimeEvent;
      if (typeof event?.type !== "string") return;
      eventHandlers.forEach((handler) => handler(event));
    } catch {
      // Ignore frames that are not our JSON envelope.
    }
  };
  ws.onerror = () => {
    ws.close();
  };
  ws.onclose = () => {
    if (socket === ws) socket = null;
    if (closing) return;
    setStatus("down");
    scheduleReconnect();
  };
}

function disconnectIfIdle() {
  if (eventHandlers.size + statusHandlers.size > 0) return;
  closing = true;
  reconnectAttempt = 0;
  if (reconnectTimer !== null) {
    window.clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  socket?.close();
  socket = null;
  setStatus("down");
}

export function subscribeRealtime(handler: RealtimeHandler): () => void {
  eventHandlers.add(handler);
  connect();
  return () => {
    eventHandlers.delete(handler);
    disconnectIfIdle();
  };
}

export function subscribeRealtimeStatus(
  handler: (status: RealtimeStatus) => void,
): () => void {
  statusHandlers.add(handler);
  handler(status);
  connect();
  return () => {
    statusHandlers.delete(handler);
    disconnectIfIdle();
  };
}

export function getRealtimeStatus(): RealtimeStatus {
  return status;
}
