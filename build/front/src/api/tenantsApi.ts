import { httpClient } from "./httpClient";
import type {
  Rent,
  RentReceipt,
  RentReceiptsDetail,
  RentsFee,
  Tenant,
  TenantFullInput,
  TenantFullResponse,
} from "./types";

export interface TenantsListFilter {
  active?: number;
  name?: string;
  email?: string;
  placeUnitId?: number;
  limit?: number;
  offset?: number;
}

export async function listTenants(filter: TenantsListFilter = {}): Promise<Tenant[]> {
  const { data } = await httpClient.get<Tenant[]>("/api/v1/tenants", { params: filter });
  return data;
}

export async function getTenant(id: number): Promise<Tenant> {
  const { data } = await httpClient.get<Tenant>(`/api/v1/tenants/${id}`);
  return data;
}

export async function createTenantFull(input: TenantFullInput): Promise<TenantFullResponse> {
  const { data } = await httpClient.post<TenantFullResponse>(
    "/api/v1/tenants/full",
    input,
  );
  return data;
}

export async function updateTenant(id: number, input: Partial<Tenant>): Promise<Tenant> {
  const { data } = await httpClient.patch<Tenant>(`/api/v1/tenants/${id}`, input);
  return data;
}

export async function getTenantReceipts(id: number): Promise<RentReceipt[]> {
  const { data } = await httpClient.get<RentReceipt[]>(`/api/v1/tenants/${id}/receipts`);
  return data;
}

export async function listRents(tenantId?: number): Promise<Rent[]> {
  const params = tenantId ? { tenantId } : {};
  const { data } = await httpClient.get<Rent[]>("/api/v1/rents", { params });
  return data;
}

export interface RentInput {
  tenantId?: number;
  type?: "Loyer" | "Charges" | "Garantie";
  price?: number | null;
  active?: number;
}

export async function createRent(input: RentInput): Promise<Rent> {
  const { data } = await httpClient.post<Rent>("/api/v1/rents", input);
  return data;
}

export async function updateRent(id: number, input: RentInput): Promise<Rent> {
  const { data } = await httpClient.patch<Rent>(`/api/v1/rents/${id}`, input);
  return data;
}

export async function listRentReceipts(): Promise<RentReceipt[]> {
  const { data } = await httpClient.get<RentReceipt[]>("/api/v1/rentReceipts", {
    params: { limit: 500 },
  });
  return data;
}

// --- RentReceipts CRUD ------------------------------------------------------
export interface RentReceiptInput {
  tenantId?: number | null;
  placeUnitId?: number | null;
  placeUnitRoomId?: number | null;
  amount?: number | null;
  periodBegin?: string | null;
  periodEnd?: string | null;
  paid?: number;
}

export async function createRentReceipt(input: RentReceiptInput): Promise<RentReceipt> {
  const { data } = await httpClient.post<RentReceipt>("/api/v1/rentReceipts", input);
  return data;
}

export async function updateRentReceipt(
  id: number,
  input: RentReceiptInput,
): Promise<RentReceipt> {
  const { data } = await httpClient.patch<RentReceipt>(
    `/api/v1/rentReceipts/${id}`,
    input,
  );
  return data;
}

export async function deleteRentReceipt(id: number): Promise<void> {
  await httpClient.delete(`/api/v1/rentReceipts/${id}`);
}

export async function listReceiptDetails(receiptId: number): Promise<RentReceiptsDetail[]> {
  const { data } = await httpClient.get<RentReceiptsDetail[]>("/api/v1/rentReceiptsDetails", {
    params: { rentReceiptsId: receiptId, limit: 50 },
  });
  return data;
}

export async function downloadReceiptPdf(id: number): Promise<Blob> {
  const { data } = await httpClient.get(`/api/v1/rentReceipts/${id}/pdf`, {
    responseType: "blob",
  });
  return data as Blob;
}

// --- RentsFees ---------------------------------------------------------------

export interface RentsFeeInput {
  tenantId?: number | null;
  applicationMonth?: string | null;
  description?: string | null;
  subDescription?: string | null;
  price?: number | null;
}

export async function listTenantFees(tenantId: number): Promise<RentsFee[]> {
  const { data } = await httpClient.get<RentsFee[]>("/api/v1/rentsFees", {
    params: { tenantId, limit: 200, sort: "-applicationMonth" },
  });
  return data;
}

export async function createRentsFee(input: RentsFeeInput): Promise<RentsFee> {
  const { data } = await httpClient.post<RentsFee>("/api/v1/rentsFees", input);
  return data;
}

export async function deleteRentsFee(id: number): Promise<void> {
  await httpClient.delete(`/api/v1/rentsFees/${id}`);
}

export async function uploadFeeDocument(id: number, file: File): Promise<void> {
  const form = new FormData();
  form.append("file", file);
  await httpClient.post(`/api/v1/rentsFees/${id}/document`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export async function downloadFeeDocument(id: number): Promise<Blob> {
  const { data } = await httpClient.get(`/api/v1/rentsFees/${id}/document`, {
    responseType: "blob",
  });
  return data as Blob;
}

export async function deleteFeeDocument(id: number): Promise<void> {
  await httpClient.delete(`/api/v1/rentsFees/${id}/document`);
}
