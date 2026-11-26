import type {
  DecodedFSSAI14,
  FactReceipt,
  GhostBrandCluster,
  GrievanceCategory,
  GrievancePacket,
  VerifiedSwitchOption,
} from "./types";

export const DEFAULT_API_BASE =
  import.meta.env.PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  const text = await res.text();
  let data: (T & { error?: string }) | null = null;
  try {
    data = JSON.parse(text) as T & { error?: string };
  } catch {
    // Non-JSON error pages are rendered as a status-only ApiError below.
  }
  if (!res.ok) {
    throw new ApiError(res.status, data?.error ?? `HTTP ${res.status}`);
  }
  if (data === null) {
    throw new ApiError(res.status, "API returned a non-JSON response");
  }
  return data;
}

export async function checkApiHealth(
  apiBase = DEFAULT_API_BASE,
): Promise<boolean> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 1500);
  try {
    const data = await fetchJson<{ status: string }>(`${apiBase}/health`, {
      signal: controller.signal,
    });
    return data.status === "ok";
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchDecode(
  fssaiId: string,
  apiBase = DEFAULT_API_BASE,
): Promise<DecodedFSSAI14> {
  return fetchJson<DecodedFSSAI14>(
    `${apiBase}/v1/decode/${encodeURIComponent(fssaiId.trim())}`,
  );
}

export async function fetchFactReceipt(
  fssaiId: string,
  apiBase = DEFAULT_API_BASE,
): Promise<FactReceipt> {
  return fetchJson<FactReceipt>(
    `${apiBase}/v1/receipt/${encodeURIComponent(fssaiId.trim())}`,
  );
}

export async function fetchGhostCluster(
  fssaiId: string,
  apiBase = DEFAULT_API_BASE,
): Promise<GhostBrandCluster> {
  return fetchJson<GhostBrandCluster>(
    `${apiBase}/v1/cluster/${encodeURIComponent(fssaiId.trim())}`,
  );
}

export async function fetchVerifiedNearby(
  postalCode: string,
  apiBase = DEFAULT_API_BASE,
): Promise<{ postal_code: string; options: VerifiedSwitchOption[] }> {
  return fetchJson<{ postal_code: string; options: VerifiedSwitchOption[] }>(
    `${apiBase}/v1/nearby/${encodeURIComponent(postalCode.trim())}`,
  );
}

export async function submitGrievancePacket(
  payload: {
    fssai_id: string;
    issue_category: GrievanceCategory;
    order_reference?: string | null;
    description: string;
    incident_date: string;
    persist?: boolean;
  },
  apiBase = DEFAULT_API_BASE,
): Promise<GrievancePacket> {
  return fetchJson<GrievancePacket>(`${apiBase}/v1/grievance`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}
