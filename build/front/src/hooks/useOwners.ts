import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as ownersApi from "@/api/ownersApi";
import type { OwnerInput, OwnerFullInput } from "@/api/types";

export function useOwnersList(filter: ownersApi.OwnersListFilter = {}) {
  return useQuery({
    queryKey: ["owners", filter],
    queryFn: () => ownersApi.listOwners(filter),
  });
}

export function useCreateOwner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: OwnerInput) => ownersApi.createOwner(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["owners"] }),
  });
}

export function useUpdateOwner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: OwnerInput }) =>
      ownersApi.updateOwner(id, input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["owners"] }),
  });
}

export function useDeleteOwner() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => ownersApi.deleteOwner(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["owners"] }),
  });
}

export function useCreateOwnerFull() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: OwnerFullInput) => ownersApi.createOwnerFull(input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["owners"] });
      qc.invalidateQueries({ queryKey: ["users"] });
    },
  });
}
