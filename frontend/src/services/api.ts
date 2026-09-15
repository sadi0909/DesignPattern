export type HealthResponse = { status: string; db: "ok" | "fail" };

export type SensorDto = {
  id: string;
  device_type: string;
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
