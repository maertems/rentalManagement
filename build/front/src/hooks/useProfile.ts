import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as profileApi from "@/api/profileApi";
import type { ProfileUpdate } from "@/api/types";

export function useMyProfile() {
  return useQuery({
    queryKey: ["myProfile"],
    queryFn: profileApi.getMyProfile,
  });
}

export function useUpdateMyProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: ProfileUpdate) => profileApi.updateMyProfile(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["myProfile"] }),
  });
}

export function useSendTestEmail() {
  return useMutation({
    mutationFn: (input: profileApi.TestEmailInput) => profileApi.sendTestEmail(input),
  });
}
