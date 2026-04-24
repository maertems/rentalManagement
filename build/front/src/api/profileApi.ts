import { httpClient } from "./httpClient";
import type { ProfileRead, ProfileUpdate } from "./types";

export async function getMyProfile(): Promise<ProfileRead> {
  const { data } = await httpClient.get<ProfileRead>("/api/v1/me/profile");
  return data;
}

export async function updateMyProfile(input: ProfileUpdate): Promise<ProfileRead> {
  const { data } = await httpClient.patch<ProfileRead>("/api/v1/me/profile", input);
  return data;
}

export interface TestEmailInput {
  tenant_id: number | null;
  month: string; // "YYYY-MM"
}

export interface TestEmailResult {
  sent: string[];
  skipped: { name: string; reason: string }[];
}

export async function sendTestEmail(input: TestEmailInput): Promise<TestEmailResult> {
  const { data } = await httpClient.post<TestEmailResult>("/api/v1/me/test-email", input);
  return data;
}
