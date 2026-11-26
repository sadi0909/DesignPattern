export type HealthResponse = { status: string; db: "ok" | "fail" };

export type SensorDto = {
  id: string;
  device_type: string;
  display_name: string;
  default_config: Record<string, unknown>;
  location_id: string | null;
};

export type ReadingDto = {
  device_id: string;
  value: number;
  unit: string;
  source: string;
  recorded_at: string;
};

export type DeviceFamily = "simulation" | "edge";
export type DeviceRole = "sensor" | "actuator";

export type ActuatorState = "off" | "idle" | "running" | "error" | "maintenance";

export type DeviceDto = {
  id: string;
  device_type: string;
  role: DeviceRole;
  device_family: string;
  display_name: string;
  default_config: Record<string, unknown>;
  location_id: string | null;
  state: ActuatorState | null;
  allowed_commands: string[];
};

export type CommandStatus = "success" | "failed" | "rejected";

export type CommandLogDto = {
  id: string;
  command_type: string;
  device_id: string;
  payload: Record<string, unknown>;
  status: CommandStatus;
  error_message: string | null;
  created_at: string;
};

export type AlertSeverity = "info" | "warning" | "critical";
export type AlertStatus = "active" | "resolved";

export type AlertDto = {
  id: string;
  location_id: string | null;
  device_id: string | null;
  severity: AlertSeverity;
  message: string;
  event_type: string;
  status: AlertStatus;
  created_at: string;
  acknowledged_at: string | null;
};

export type ActuatorExecutionDto = {
  id: string;
  device_id: string;
  success: boolean;
  policy_applied: string[];
  message: string | null;
  created_at: string;
};

export type ZoneConfigRequest = {
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule: Record<string, unknown>;
};

export type LocationConfigRequest = {
  location_name: string;
  zones: ZoneConfigRequest[];
};

export type LocationConfigDto = {
  location: { id: string; name: string };
  zones: {
    id: string;
    location_id: string;
    name: string;
    moisture_threshold_low: number;
    moisture_threshold_high: number;
    schedule: Record<string, unknown>;
  }[];
};

// One base URL for REST and for the realtime module's ws:// derivation. Leave
// it empty in development: Vite proxies `/api` (including the WebSocket).
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: unknown } | null;
    const detail = payload?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map((item) => {
                if (typeof item !== "object" || item === null || !("msg" in item)) return null;
                const location = "loc" in item && Array.isArray(item.loc) ? `${item.loc.join(".")}: ` : "";
                return `${location}${String(item.msg)}`;
              })
              .filter((item): item is string => item !== null)
              .join("; ") || `Request failed: ${response.status}`
          : `Request failed: ${response.status}`;
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/health");
}

export function fetchSensors(): Promise<SensorDto[]> {
  return request<SensorDto[]>("/api/sensors");
}

export function createSensor(type: "moisture" | "light", displayName?: string): Promise<SensorDto> {
  return request<SensorDto>("/api/sensors", {
    method: "POST",
    body: JSON.stringify({ type, display_name: displayName ?? null }),
  });
}

export function readSensor(sensorId: string): Promise<ReadingDto> {
  return request<ReadingDto>(`/api/sensors/${encodeURIComponent(sensorId)}/read`, {
    method: "POST",
  });
}

export type ReadingRange = { from?: string; to?: string };

export function fetchSensorReadings(
  sensorId: string,
  limit = 20,
  range: ReadingRange = {},
): Promise<ReadingDto[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (range.from) params.set("from", range.from);
  if (range.to) params.set("to", range.to);
  return request<ReadingDto[]>(
    `/api/sensors/${encodeURIComponent(sensorId)}/readings?${params.toString()}`,
  );
}

export function fetchDevices(filters: {
  family?: DeviceFamily;
  role?: DeviceRole;
} = {}): Promise<DeviceDto[]> {
  const params = new URLSearchParams();
  if (filters.family) params.set("family", filters.family);
  if (filters.role) params.set("role", filters.role);
  const query = params.size > 0 ? `?${params.toString()}` : "";
  return request<DeviceDto[]>(`/api/devices${query}`);
}

export function assignDeviceLocation(
  deviceId: string,
  locationId: string | null,
): Promise<DeviceDto> {
  return request<DeviceDto>(`/api/devices/${encodeURIComponent(deviceId)}/location`, {
    method: "PATCH",
    body: JSON.stringify({ location_id: locationId }),
  });
}

export function provisionDeviceFamily(family: DeviceFamily): Promise<DeviceDto[]> {
  const params = new URLSearchParams({ family });
  return request<DeviceDto[]>(`/api/devices/provision?${params.toString()}`, {
    method: "POST",
  });
}

export function fetchActuatorExecutions(limit = 20): Promise<ActuatorExecutionDto[]> {
  return request<ActuatorExecutionDto[]>(`/api/actuators/executions?limit=${limit}`);
}

export function applyActuatorCommand(
  deviceId: string,
  command: string,
  payload: Record<string, unknown> = {},
): Promise<{ status: string }> {
  return request<{ status: string }>(`/api/actuators/${encodeURIComponent(deviceId)}/apply`, {
    method: "POST",
    body: JSON.stringify({ command, payload }),
  });
}

export function executeCommand(
  deviceId: string,
  commandType: string,
  payload: Record<string, unknown> = {},
): Promise<CommandLogDto> {
  return request<CommandLogDto>("/api/commands", {
    method: "POST",
    body: JSON.stringify({ command_type: commandType, device_id: deviceId, payload }),
  });
}

export function fetchCommands(limit = 50): Promise<CommandLogDto[]> {
  return request<CommandLogDto[]>(`/api/commands?limit=${limit}`);
}

export function fetchAlerts(params: {
  status?: AlertStatus;
  locationId?: string;
  limit?: number;
} = {}): Promise<AlertDto[]> {
  const search = new URLSearchParams();
  if (params.status) search.set("status", params.status);
  if (params.locationId) search.set("location_id", params.locationId);
  search.set("limit", String(params.limit ?? 50));
  return request<AlertDto[]>(`/api/alerts?${search.toString()}`);
}

export function createLocationConfig(payload: LocationConfigRequest): Promise<LocationConfigDto> {
  return request<LocationConfigDto>("/api/locations/config", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchLocationConfig(locationId: string): Promise<LocationConfigDto> {
  return request<LocationConfigDto>(`/api/locations/${encodeURIComponent(locationId)}/config`);
}

export type LocationOverviewDto = {
  location: { id: string; name: string };
  device_counts: { sensor: number; actuator: number };
  latest_readings: { device_id: string; value: number; unit: string; recorded_at: string }[];
  strategy_key: string | null;
  last_recommendation: { action: string; reason: string } | null;
};

export function fetchOverview(locationId: string): Promise<LocationOverviewDto> {
  return request<LocationOverviewDto>(`/api/locations/${encodeURIComponent(locationId)}/overview`);
}

// Remembers the location the configuration wizard last saved, so the strategy panel can use it.
export const ACTIVE_LOCATION_STORAGE_KEY = "greenhouse.activeLocationId";

export type AutomationRuleDto = {
  location_id: string;
  strategy_key: string;
  is_default: boolean;
  updated_at: string | null;
  available_strategies: string[];
};

export type RecommendationDto = {
  location_id: string;
  strategy_key: string;
  action: string;
  reason: string;
};

export function fetchAutomationRule(locationId: string): Promise<AutomationRuleDto> {
  return request<AutomationRuleDto>(`/api/locations/${encodeURIComponent(locationId)}/automation`);
}

export function saveAutomationStrategy(locationId: string, strategyKey: string): Promise<AutomationRuleDto> {
  return request<AutomationRuleDto>(`/api/locations/${encodeURIComponent(locationId)}/automation`, {
    method: "PUT",
    body: JSON.stringify({ strategy_key: strategyKey }),
  });
}

export function evaluateAutomation(locationId: string): Promise<RecommendationDto> {
  return request<RecommendationDto>(
    `/api/locations/${encodeURIComponent(locationId)}/automation/evaluate`,
    { method: "POST" },
  );
}
