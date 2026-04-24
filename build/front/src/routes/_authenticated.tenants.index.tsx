import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ChevronDown, ChevronRight, Plus, Search } from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TenantsTable } from "@/features/tenants/TenantsTable";
import { TenantFullFormDialog } from "@/features/tenants/TenantFullFormDialog";
import { TenantReceiptsDialog } from "@/features/tenants/TenantReceiptsDialog";
import {
  useAllRentReceipts,
  useAllRents,
  useTenantsList,
} from "@/hooks/useTenants";
import { useAllPlacesUnits, useAllRooms, usePlacesList } from "@/hooks/usePlaces";
import type { Tenant } from "@/api/types";

function filterTenants(rows: Tenant[] | undefined, q: string): Tenant[] {
  if (!rows) return [];
  if (!q) return rows;
  const lq = q.toLowerCase();
  return rows.filter(
    (t) =>
      (t.firstName && t.firstName.toLowerCase().includes(lq)) ||
      (t.name && t.name.toLowerCase().includes(lq)) ||
      (t.email && t.email.toLowerCase().includes(lq)) ||
      (t.phone && t.phone.toLowerCase().includes(lq)),
  );
}

function TenantsPage() {
  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [showReceipts, setShowReceipts] = useState<Tenant | null>(null);
  const [inactiveOpen, setInactiveOpen] = useState(false);

  const { data: activeTenants, isLoading: loadingActive } = useTenantsList({ active: 1 });
  const { data: inactiveTenants, isLoading: loadingInactive } = useTenantsList({ active: 0 });
  const { data: places } = usePlacesList();
  const { data: units } = useAllPlacesUnits();
  const { data: rooms } = useAllRooms();
  const { data: rents } = useAllRents();
  const { data: receipts } = useAllRentReceipts();

  const q = search.trim();
  const filteredActive = useMemo(() => filterTenants(activeTenants, q), [activeTenants, q]);
  const filteredInactive = useMemo(
    () => filterTenants(inactiveTenants, q),
    [inactiveTenants, q],
  );

  return (
    <div className="space-y-4">
      <PageHeader
        title="Locataires"
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-1 h-4 w-4" /> Nouveau
          </Button>
        }
      />

      <div className="relative max-w-sm">
        <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Rechercher par nom, email, téléphone…"
          className="pl-8"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold uppercase text-muted-foreground">
          Actifs ({filteredActive.length})
        </h2>
        <TenantsTable
          rows={filteredActive}
          isLoading={loadingActive}
          places={places ?? []}
          units={units ?? []}
          rooms={rooms ?? []}
          rents={rents ?? []}
          receipts={receipts ?? []}
          variant="active"
          onShowReceipts={setShowReceipts}
        />
      </section>

      <section className="space-y-2">
        <button
          onClick={() => setInactiveOpen((v) => !v)}
          className="flex items-center gap-2 text-sm font-semibold uppercase text-muted-foreground hover:text-foreground"
        >
          {inactiveOpen ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
          Inactifs ({filteredInactive.length})
        </button>
        {inactiveOpen && (
          <TenantsTable
            rows={filteredInactive}
            isLoading={loadingInactive}
            places={places ?? []}
            units={units ?? []}
            rooms={rooms ?? []}
            rents={rents ?? []}
            receipts={receipts ?? []}
            variant="inactive"
            onShowReceipts={setShowReceipts}
          />
        )}
      </section>

      <TenantFullFormDialog open={createOpen} onOpenChange={setCreateOpen} />

      <TenantReceiptsDialog
        open={showReceipts !== null}
        onOpenChange={(open) => !open && setShowReceipts(null)}
        tenant={showReceipts}
      />
    </div>
  );
}

export const Route = createFileRoute("/_authenticated/tenants/")({
  component: TenantsPage,
});
