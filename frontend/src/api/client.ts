const fallbackBaseUrl = "http://localhost:8000";

export const apiBaseUrl =
  import.meta.env.VITE_API_BASE_URL?.trim() || fallbackBaseUrl;

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

