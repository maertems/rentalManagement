import { httpClient } from "./httpClient";
import type { User } from "./types";

export async function login(email: string, password: string): Promise<User> {
  const { data } = await httpClient.post<User>("/api/v1/auth/login", {
    email,
    password,
  });
  return data;
}

export async function logout(): Promise<void> {
  await httpClient.post("/api/v1/auth/logout");
}

export async function getMe(): Promise<User> {
  const { data } = await httpClient.get<User>("/api/v1/auth/me");
  return data;
}
