import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Plus, Search } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/common/PageHeader";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { OwnersTable } from "@/features/owners/OwnersTable";
import { OwnerFormDialog } from "@/features/owners/OwnerFormDialog";
import { OwnerFullFormDialog } from "@/features/owners/OwnerFullFormDialog";
import { useDeleteOwner, useOwnersList } from "@/hooks/useOwners";
import { getApiErrorMessage } from "@/lib/apiError";
import type { Owner } from "@/api/types";

function OwnersPage() {
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [editing, setEditing] = useState<Owner | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState<Owner | null>(null);

  const filter = search.trim() ? { name: search.trim() } : {};
  const { data, isLoading } = useOwnersList(filter);
  const deleteMut = useDeleteOwner();

  function openCreate() {
    setCreateOpen(true);
  }
  function openEdit(o: Owner) {
    setEditing(o);
    setFormOpen(true);
  }
  function askDelete(o: Owner) {
    setDeleting(o);
    setConfirmOpen(true);
  }

  async function confirmDelete() {
    if (!deleting) return;
    try {
      await deleteMut.mutateAsync(deleting.id);
      toast.success("Propriétaire supprimé");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Propriétaires"
        actions={
          <Button onClick={openCreate}>
            <Plus className="mr-1 h-4 w-4" />
            Nouveau
          </Button>
        }
      />

      <div className="relative max-w-sm">
        <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Rechercher par nom…"
          className="pl-8"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <OwnersTable
        rows={data?.rows ?? []}
        isLoading={isLoading}
        onEdit={openEdit}
        onDelete={askDelete}
      />

      {/* Create: full form (user + owner) */}
      <OwnerFullFormDialog open={createOpen} onOpenChange={setCreateOpen} />

      {/* Edit: owner fields only */}
      <OwnerFormDialog open={formOpen} onOpenChange={setFormOpen} owner={editing} />

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Supprimer ce propriétaire ?"
        description={
          deleting
            ? `${deleting.name ?? "Sans nom"} sera définitivement supprimé. Cette action est irréversible.`
            : ""
        }
        confirmLabel="Supprimer"
        onConfirm={confirmDelete}
      />
    </div>
  );
}

export const Route = createFileRoute("/_authenticated/owners")({
  component: OwnersPage,
});
