import type {
  ClusterResponse,
  GlobalKPIs,
  ShowsResponse,
  ChatRequest,
  ChatResponse,
  HealthResponse,
} from "@/types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {}),
    },
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${path}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>("/api/v1/health");
}

export async function fetchClusters(): Promise<ClusterResponse> {
  return apiFetch<ClusterResponse>("/api/v1/clusters");
}

export async function fetchKPIs(): Promise<GlobalKPIs> {
  return apiFetch<GlobalKPIs>("/api/v1/kpis");
}

export async function fetchShows(): Promise<ShowsResponse> {
  return apiFetch<ShowsResponse>("/api/v1/shows");
}

export async function postSimulateTick(): Promise<void> {
  await apiFetch<unknown>("/api/v1/simulate/tick", { method: "POST" });
}

export async function postChat(req: ChatRequest): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/api/v1/chat", {
    method: "POST",
    body: JSON.stringify(req),
  });
}
