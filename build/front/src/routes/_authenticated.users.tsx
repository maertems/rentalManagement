import { useState } from "react";
import { createFileRoute, redirect } from "@tanstack/react-router";
import { Landmark, Pencil, Plus, Shield, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/common/PageHeader";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { UserFormDialog } from "@/features/users/UserFormDialog";
import { useDeleteUser, useUsersList } from "@/hooks/useUsers";
import { getApiErrorMessage } from "@/lib/apiError";
import { formatDate } from "@/lib/formatters";
import * as authApi from "@/api/authApi";
import type { User } from "@/api/types";

function UsersPage() {
  const { data: users, isLoading } = useUsersList();
  const deleteMut = useDeleteUser();

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState<User | null>(null);

  function openCreate() {
    setEditing(null);
    setFormOpen(true);
  }
  function openEdit(u: User) {
    setEditing(u);
    setFormOpen(true);
  }
  function askDelete(u: User) {
    setDeleting(u);
    setConfirmOpen(true);
  }
  async function confirmDelete() {
    if (!deleting) return;
    try {
      await deleteMut.mutateAsync(deleting.id);
      toast.success("Utilisateur supprimé");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Utilisateurs"
        subtitle="Gestion des comptes utilisateurs."
        actions={
          <Button onClick={openCreate}>
            <Plus className="mr-1 h-4 w-4" /> Nouveau
          </Button>
        }
      />

      {isLoading ? (
        <div className="py-12 text-center text-muted-foreground">Chargement…</div>
      ) : !users || users.length === 0 ? (
        <div className="py-12 text-center text-muted-foreground">
          Aucun utilisateur.
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left">
              <tr>
                <th className="px-4 py-2 font-medium">Email</th>
                <th className="px-4 py-2 font-medium">Nom</th>
                <th className="px-4 py-2 font-medium">Username</th>
                <th className="px-4 py-2 font-medium text-center">Admin</th>
                <th className="px-4 py-2 font-medium text-center">Withdraw</th>
                <th className="px-4 py-2 font-medium">Créé le</th>
                <th className="w-[120px] px-4 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-muted/30">
                  <td className="px-4 py-2 font-medium">{u.email}</td>
                  <td className="px-4 py-2 text-muted-foreground">{u.name ?? "—"}</td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {u.username ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {u.isAdmin ? (
                      <Shield className="mx-auto h-4 w-4 text-primary" />
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-center">
                    {u.isWithdraw ? (
                      <Landmark className="mx-auto h-4 w-4 text-primary" />
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {formatDate(u.createdAt)}
                  </td>
                  <td className="px-4 py-2">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => openEdit(u)}
                        title="Modifier"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => askDelete(u)}
                        title="Supprimer"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <UserFormDialog open={formOpen} onOpenChange={setFormOpen} user={editing} />

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Supprimer cet utilisateur ?"
        description={
          deleting
            ? `${deleting.email} sera définitivement supprimé.`
            : ""
        }
        confirmLabel="Supprimer"
        onConfirm={confirmDelete}
      />
    </div>
  );
}

export const Route = createFileRoute("/_authenticated/users")({
  beforeLoad: async () => {
    try {
      const me = await authApi.getMe();
      if (!me.isAdmin) throw redirect({ to: "/" });
    } catch (err) {
      if (err && typeof err === "object" && "redirect" in err) throw err;
      throw redirect({ to: "/login" });
    }
  },
  component: UsersPage,
});
