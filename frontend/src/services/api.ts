export type HealthResponse = { status: string; db: "ok" | "fail" };

export type SensorDto = {
  id: string;
  device_type: string;
  display_name: string;
  default_config: Record<string, unknown>;
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

export type DeviceDto = {
  id: string;
  device_type: string;
  role: DeviceRole;
  device_family: string;
  display_name: string;
  default_config: Record<string, unknown>;
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

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
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

export function fetchSensorReadings(sensorId: string, limit = 20): Promise<ReadingDto[]> {
  return request<ReadingDto[]>(
    `/api/sensors/${encodeURIComponent(sensorId)}/readings?limit=${limit}`,
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

export function provisionDeviceFamily(family: DeviceFamily): Promise<DeviceDto[]> {
  const params = new URLSearchParams({ family });
  return request<DeviceDto[]>(`/api/devices/provision?${params.toString()}`, {
    method: "POST",
  });
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
