import { useQuery } from "@tanstack/react-query";
import { getOccupancy } from "@/api/dashboardApi";

export function useOccupancy(month: string) {
  return useQuery({
    queryKey: ["occupancy", month],
    queryFn: () => getOccupancy(month),
  });
}
