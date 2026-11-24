/**
 * Phase 11 stub for live domain events.
 *
 * The backend publishes events through an in-process bus; this phase only
 * polls `GET /api/alerts`. Phase 12 replaces this module with a WebSocket
 * client that receives the same events. Keeping the interface here means the
 * dashboard can switch transports later without changing its event model.
 */

export type RealtimeEvent = { type: string; payload: unknown };

export type RealtimeHandler = (event: RealtimeEvent) => void;

/**
 * Register a realtime handler. No socket is opened in Phase 11, so this is a
 * no-op that still returns the unsubscribe function Phase 12 will need.
 */
export function subscribeRealtime(_handler: RealtimeHandler): () => void {
  return () => {};
}
