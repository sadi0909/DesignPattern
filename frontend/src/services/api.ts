export type HealthResponse = { status: string; db: "ok" | "fail" };

export type SensorDto = {
  id: string;
  device_type: string;
  display_name: string;
  default_config: Record<string, unknown>;
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

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
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
