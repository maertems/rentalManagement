import { httpClient } from "./httpClient";
import type { Owner, OwnerInput, OwnerFullInput, OwnerFullResponse } from "./types";

export interface OwnersListFilter {
  name?: string;
  email?: string;
  city?: string;
  limit?: number;
  offset?: number;
  sort?: string;
}

export interface OwnersListResult {
  rows: Owner[];
  total: number;
}

export async function listOwners(filter: OwnersListFilter = {}): Promise<OwnersListResult> {
  const { data, headers } = await httpClient.get<Owner[]>("/api/v1/owners", {
    params: filter,
  });
  const total = Number(headers["x-total-count"] ?? data.length);
  return { rows: data, total };
}

export async function getOwner(id: number): Promise<Owner> {
  const { data } = await httpClient.get<Owner>(`/api/v1/owners/${id}`);
  return data;
}

export async function createOwner(input: OwnerInput): Promise<Owner> {
  const { data } = await httpClient.post<Owner>("/api/v1/owners", input);
  return data;
}

export async function updateOwner(id: number, input: OwnerInput): Promise<Owner> {
  const { data } = await httpClient.patch<Owner>(`/api/v1/owners/${id}`, input);
  return data;
}

export async function deleteOwner(id: number): Promise<void> {
  await httpClient.delete(`/api/v1/owners/${id}`);
}

export async function createOwnerFull(input: OwnerFullInput): Promise<OwnerFullResponse> {
  const { data } = await httpClient.post<OwnerFullResponse>("/api/v1/owners/full", input);
  return data;
}
