import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as tenantsApi from "@/api/tenantsApi";
import type { Tenant, TenantFullInput } from "@/api/types";

export function useTenantsList(filter: tenantsApi.TenantsListFilter = {}) {
  return useQuery({
    queryKey: ["tenants", filter],
    queryFn: () => tenantsApi.listTenants(filter),
    select: (d) => Array.isArray(d) ? d : [],
  });
}

export function useTenant(id: number | null) {
  return useQuery({
    queryKey: ["tenant", id],
    queryFn: () => tenantsApi.getTenant(id!),
    enabled: id !== null,
  });
}

export function useCreateTenantFull() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: TenantFullInput) => tenantsApi.createTenantFull(input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["tenants"] });
      qc.invalidateQueries({ queryKey: ["rents"] });
      qc.invalidateQueries({ queryKey: ["rentReceipts"] });
      qc.invalidateQueries({ queryKey: ["occupancy"] });
    },
  });
}

export function useUpdateTenant() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: Partial<Tenant> }) =>
      tenantsApi.updateTenant(id, input),
    onSuccess: (_, variables) => {
      qc.invalidateQueries({ queryKey: ["tenants"] });
      qc.invalidateQueries({ queryKey: ["tenant", variables.id] });
      qc.invalidateQueries({ queryKey: ["occupancy"] });
    },
  });
}

export function useTenantReceipts(tenantId: number | null) {
  return useQuery({
    queryKey: ["tenantReceipts", tenantId],
    queryFn: () => tenantsApi.getTenantReceipts(tenantId!),
    enabled: tenantId !== null,
  });
}

export function useAllRents() {
  return useQuery({
    queryKey: ["rents"],
    queryFn: () => tenantsApi.listRents(),
    select: (d) => Array.isArray(d) ? d : [],
  });
}

export function useTenantRents(tenantId: number | null) {
  return useQuery({
    queryKey: ["rents", { tenantId }],
    queryFn: () => tenantsApi.listRents(tenantId!),
    enabled: tenantId !== null,
  });
}

export function useUpdateRent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: tenantsApi.RentInput }) =>
      tenantsApi.updateRent(id, input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["rents"] });
      qc.invalidateQueries({ queryKey: ["occupancy"] });
    },
  });
}

export function useCreateRent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: tenantsApi.RentInput) => tenantsApi.createRent(input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["rents"] });
      qc.invalidateQueries({ queryKey: ["occupancy"] });
    },
  });
}

export function useAllRentReceipts() {
  return useQuery({
    queryKey: ["rentReceipts"],
    queryFn: () => tenantsApi.listRentReceipts(),
    select: (d) => Array.isArray(d) ? d : [],
  });
}

function invalidateReceipts(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["tenantReceipts"] });
  qc.invalidateQueries({ queryKey: ["rentReceipts"] });
  qc.invalidateQueries({ queryKey: ["occupancy"] });
}

export function useCreateRentReceipt() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: tenantsApi.RentReceiptInput) =>
      tenantsApi.createRentReceipt(input),
    onSuccess: () => invalidateReceipts(qc),
  });
}

export function useUpdateRentReceipt() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: tenantsApi.RentReceiptInput }) =>
      tenantsApi.updateRentReceipt(id, input),
    onSuccess: () => invalidateReceipts(qc),
  });
}

export function useDeleteRentReceipt() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => tenantsApi.deleteRentReceipt(id),
    onSuccess: () => invalidateReceipts(qc),
  });
}

export function useDownloadReceiptPdf() {
  return useMutation({
    mutationFn: (id: number) => tenantsApi.downloadReceiptPdf(id),
  });
}

export function useReceiptDetails(receiptId: number | null) {
  return useQuery({
    queryKey: ["receiptDetails", receiptId],
    queryFn: () => tenantsApi.listReceiptDetails(receiptId!),
    enabled: receiptId !== null,
  });
}

// --- RentsFees ---------------------------------------------------------------

export function useTenantFees(tenantId: number | null) {
  return useQuery({
    queryKey: ["rentsFees", tenantId],
    queryFn: () => tenantsApi.listTenantFees(tenantId!),
    enabled: tenantId !== null,
  });
}

export function useCreateRentsFee() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: tenantsApi.RentsFeeInput) => tenantsApi.createRentsFee(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rentsFees"] }),
  });
}

export function useDeleteRentsFee() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => tenantsApi.deleteRentsFee(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rentsFees"] }),
  });
}

export function useUploadFeeDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) =>
      tenantsApi.uploadFeeDocument(id, file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rentsFees"] }),
  });
}

export function useDownloadFeeDocument() {
  return useMutation({
    mutationFn: (id: number) => tenantsApi.downloadFeeDocument(id),
  });
}

export function useDeleteFeeDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => tenantsApi.deleteFeeDocument(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["rentsFees"] }),
  });
}
