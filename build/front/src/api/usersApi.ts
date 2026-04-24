import { httpClient } from "./httpClient";
import type { User } from "./types";

export interface UserInput {
  email?: string;
  username?: string | null;
  password?: string;
  name?: string | null;
  isAdmin?: number;
  isWithdraw?: number;
  ownerId?: number | null;
}

export async function listUsers(): Promise<User[]> {
  const { data } = await httpClient.get<User[]>("/api/v1/users");
  return data;
}

export async function createUser(input: UserInput): Promise<User> {
  const { data } = await httpClient.post<User>("/api/v1/users", input);
  return data;
}

export async function updateUser(id: number, input: UserInput): Promise<User> {
  const { data } = await httpClient.patch<User>(`/api/v1/users/${id}`, input);
  return data;
}

export async function deleteUser(id: number): Promise<void> {
  await httpClient.delete(`/api/v1/users/${id}`);
}
