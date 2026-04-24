import { httpClient } from "./httpClient";
import type { OccupancyResponse } from "./types";

export async function getOccupancy(month: string): Promise<OccupancyResponse> {
  const { data } = await httpClient.get<OccupancyResponse>(
    "/api/v1/dashboard/occupancy",
    { params: { month } },
  );
  return data;
}
