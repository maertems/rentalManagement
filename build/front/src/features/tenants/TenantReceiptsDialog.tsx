import { useState } from "react";
import { CheckCircle2, Eye, Receipt, Trash2, XCircle } from "lucide-react";
import { toast } from "sonner";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import {
  useDeleteRentReceipt,
  useDownloadReceiptPdf,
  useReceiptDetails,
  useTenantReceipts,
  useUpdateRentReceipt,
} from "@/hooks/useTenants";
import { TenantFeesDialog } from "@/features/tenants/TenantFeesDialog";
import { formatCurrency, formatDate } from "@/lib/formatters";
import { getApiErrorMessage } from "@/lib/apiError";
import type { RentReceipt, Tenant } from "@/api/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tenant: Tenant | null;
}

// ---------------------------------------------------------------------------
// Popup de confirmation de suppression
// ---------------------------------------------------------------------------

function DeleteConfirmDialog({
  receipt,
  onConfirm,
  onCancel,
  isPending,
}: {
  receipt: RentReceipt;
  onConfirm: () => void;
  onCancel: () => void;
  isPending: boolean;
}) {
  const { data: details, isLoading } = useReceiptDetails(receipt.id);

  return (
    <Dialog open onOpenChange={(v) => { if (!v) onCancel(); }}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-destructive">Supprimer la quittance ?</DialogTitle>
        </DialogHeader>

        <div className="space-y-3 text-sm">
          <div className="rounded-md border p-3 space-y-1">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Période</span>
              <span>{formatDate(receipt.periodBegin)} → {formatDate(receipt.periodEnd)}</span>
            </div>
            <div className="flex justify-between font-medium">
              <span className="text-muted-foreground">Total</span>
              <span>{formatCurrency(receipt.amount)}</span>
            </div>
          </div>

          {isLoading ? (
            <p className="text-center text-muted-foreground">Chargement des détails…</p>
          ) : details && details.length > 0 ? (
            <div className="rounded-md border">
              <p className="px-3 py-1.5 text-xs font-medium text-muted-foreground bg-muted/50">
                Détails ({details.length} ligne{details.length > 1 ? "s" : ""})
              </p>
              {details.map((d) => (
                <div key={d.id} className="flex justify-between border-t px-3 py-1.5">
                  <span className="text-muted-foreground">{d.description ?? "—"}</span>
                  <span>{formatCurrency(d.price)}</span>
                </div>
              ))}
            </div>
          ) : null}

          <p className="text-xs text-muted-foreground">
            La quittance et tous ses détails seront supprimés définitivement.
          </p>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onCancel} disabled={isPending}>
            Annuler
          </Button>
          <Button variant="destructive" onClick={onConfirm} disabled={isPending}>
            {isPending ? "Suppression…" : "Supprimer"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ---------------------------------------------------------------------------
// Ligne de quittance
// ---------------------------------------------------------------------------

function ReceiptRow({ r }: { r: RentReceipt }) {
  const updateMut = useUpdateRentReceipt();
  const deleteMut = useDeleteRentReceipt();
  const downloadMut = useDownloadReceiptPdf();
  const [toggling, setToggling] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  async function togglePaid() {
    setToggling(true);
    try {
      await updateMut.mutateAsync({
        id: r.id,
        input: { paid: r.paid ? 0 : 1 },
      });
      toast.success(r.paid ? "Marquée impayée" : "Marquée payée");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setToggling(false);
    }
  }

  async function handleDelete() {
    try {
      await deleteMut.mutateAsync(r.id);
      toast.success("Quittance supprimée");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
      setConfirmDelete(false);
    }
  }

  async function handleViewPdf() {
    try {
      const blob = await downloadMut.mutateAsync(r.id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch {
      toast.error("PDF non disponible — générez-le d'abord via POST /{id}/pdf");
    }
  }

  return (
    <>
      {confirmDelete && (
        <DeleteConfirmDialog
          receipt={r}
          onConfirm={() => void handleDelete()}
          onCancel={() => setConfirmDelete(false)}
          isPending={deleteMut.isPending}
        />
      )}
      <tr className="hover:bg-muted/30">
        <td className="px-3 py-2">{formatDate(r.periodBegin)}</td>
        <td className="px-3 py-2">{formatDate(r.periodEnd)}</td>
        <td className="px-3 py-2 text-right">{formatCurrency(r.amount)}</td>
        <td className="px-3 py-2 text-center">
          <button
            onClick={() => void togglePaid()}
            disabled={toggling}
            title={r.paid ? "Cliquer pour marquer impayée" : "Cliquer pour marquer payée"}
            className="mx-auto block disabled:opacity-50"
          >
            {r.paid ? (
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            ) : (
              <XCircle className="h-5 w-5 text-red-600" />
            )}
          </button>
        </td>
        <td className="px-3 py-2 text-center">
          <Button variant="ghost" size="icon" onClick={() => void handleViewPdf()} disabled={downloadMut.isPending} title="Voir le PDF">
            <Eye className="h-4 w-4 text-muted-foreground" />
          </Button>
        </td>
        <td className="px-3 py-2 text-center">
          {!r.paid && (
            <Button variant="ghost" size="icon" onClick={() => setConfirmDelete(true)} title="Supprimer">
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          )}
        </td>
      </tr>
    </>
  );
}

export function TenantReceiptsDialog({ open, onOpenChange, tenant }: Props) {
  const { data, isLoading } = useTenantReceipts(open && tenant ? tenant.id : null);
  const [showFees, setShowFees] = useState(false);

  const fullName = tenant
    ? [tenant.firstName, tenant.name].filter(Boolean).join(" ")
    : "";

  function handleClose(v: boolean) {
    onOpenChange(v);
    if (!v) setShowFees(false);
  }

  return (
    <>
      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent className="flex max-h-[85vh] max-w-2xl flex-col">
          <DialogHeader>
            <div className="flex items-center justify-between pr-8">
              <DialogTitle>Quittances — {fullName}</DialogTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowFees(true)}
              >
                <Receipt className="mr-1 h-4 w-4" />
                Frais &amp; charges
              </Button>
            </div>
          </DialogHeader>

          {isLoading ? (
            <div className="py-8 text-center text-muted-foreground">Chargement…</div>
          ) : data && data.length > 0 ? (
            <div className="min-h-0 flex-1 overflow-y-auto rounded-md border">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-muted/50 text-left">
                  <tr>
                    <th className="px-3 py-2 font-medium">Début</th>
                    <th className="px-3 py-2 font-medium">Fin</th>
                    <th className="px-3 py-2 font-medium text-right">Montant</th>
                    <th className="px-3 py-2 font-medium text-center">Payé</th>
                    <th className="w-[44px] px-3 py-2"></th>
                    <th className="w-[44px] px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {data.map((r) => (
                    <ReceiptRow key={r.id} r={r} />
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center italic text-muted-foreground">
              Aucune quittance.
            </div>
          )}
        </DialogContent>
      </Dialog>

      <TenantFeesDialog
        open={showFees}
        onOpenChange={setShowFees}
        tenant={tenant}
      />
    </>
  );
}
