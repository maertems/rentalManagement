import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as usersApi from "@/api/usersApi";

export function useUsersList() {
  return useQuery({
    queryKey: ["users"],
    queryFn: () => usersApi.listUsers(),
    select: (d) => Array.isArray(d) ? d : [],
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: usersApi.UserInput) => usersApi.createUser(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useUpdateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: usersApi.UserInput }) =>
      usersApi.updateUser(id, input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => usersApi.deleteUser(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}
