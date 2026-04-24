import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getOwnerParams, updateOwnerParams } from "@/api/paramsApi";
import type { OwnerParamsInput } from "@/api/paramsApi";

export function useOwnerParams(ownerId: number | null) {
  return useQuery({
    queryKey: ["params", ownerId],
    queryFn: () => getOwnerParams(ownerId!),
    enabled: ownerId !== null,
  });
}

export function useUpdateOwnerParams() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ ownerId, input }: { ownerId: number; input: OwnerParamsInput }) =>
      updateOwnerParams(ownerId, input),
    onSuccess: (_, variables) => {
      void queryClient.invalidateQueries({ queryKey: ["params", variables.ownerId] });
    },
  });
}
