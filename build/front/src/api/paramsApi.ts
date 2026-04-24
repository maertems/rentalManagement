import { httpClient } from "./httpClient";

export interface OwnerParams {
  ownerId: number;
  rentReceiptDay: number | null;
}

export interface OwnerParamsInput {
  rentReceiptDay?: number | null;
}

export async function getOwnerParams(ownerId: number): Promise<OwnerParams> {
  const { data } = await httpClient.get<OwnerParams>(`/api/v1/params/${ownerId}`);
  return data;
}

export async function updateOwnerParams(ownerId: number, input: OwnerParamsInput): Promise<OwnerParams> {
  const { data } = await httpClient.patch<OwnerParams>(`/api/v1/params/${ownerId}`, input);
  return data;
}
