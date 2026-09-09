export type HealthResponse = { status: string; db: "ok" | "fail" };

export async function fetchHealth(): Promise<HealthResponse> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "";
  const response = await fetch(`${baseUrl}/health`);
  if (!response.ok) {
    throw new Error("Failed to fetch health");
  }
  return response.json();
}