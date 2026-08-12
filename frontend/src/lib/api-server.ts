import "server-only";

import type {
  DataSourceSummary,
  DrugAssetDetail,
  IngestionJobSummary,
  OverviewStats,
  PaginatedResponse,
} from "./types";
import { cookies } from "next/headers";
import { AUTH_COOKIE_NAME } from "./auth-token";
import { apiUrl } from "./api-base";

async function serverApiFetch<T>(path: string): Promise<T> {
  const cookieStore = await cookies();
  let accessToken = cookieStore.get(AUTH_COOKIE_NAME)?.value;
  if (!accessToken && process.env.NODE_ENV !== "production" && process.env.E2E_BYPASS_AUTH === "true") {
    accessToken = process.env.API_INTERNAL_KEY;
  }
  if (!accessToken) throw new Error("Authenticated server session required");
  const response = await fetch(apiUrl(path), {
    cache: "no-store",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export const serverAssetsApi = {
  detail: (id: string) =>
    serverApiFetch<{ success: boolean; data: DrugAssetDetail }>(`api/v1/assets/${id}`),
};
export const serverSourcesApi = {
  list: () => serverApiFetch<PaginatedResponse<DataSourceSummary>>("api/v1/sources"),
};
export const serverJobsApi = {
  list: () => serverApiFetch<PaginatedResponse<IngestionJobSummary>>("api/v1/jobs"),
};
export const fetchServerOverviewStats = () =>
  serverApiFetch<{ success: boolean; data: OverviewStats }>("api/v1/overview").then(
    (response) => response.data,
  );
