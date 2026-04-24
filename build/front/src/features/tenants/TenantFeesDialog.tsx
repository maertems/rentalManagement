import { useRef, useState, type FormEvent, type ChangeEvent } from "react";
import { Paperclip, Plus, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useCreateRentsFee,
  useDeleteFeeDocument,
  useDeleteRentsFee,
  useDownloadFeeDocument,
  useTenantFees,
  useUploadFeeDocument,
} from "@/hooks/useTenants";
import { formatCurrency } from "@/lib/formatters";
import { getApiErrorMessage } from "@/lib/apiError";
import type { RentsFee, Tenant } from "@/api/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tenant: Tenant | null;
}

function formatMonth(applicationMonth: string | null): string {
  if (!applicationMonth) return "—";
  // applicationMonth is stored as YYYY-MM or YYYY-MM-DD
  const parts = applicationMonth.split("-");
  if (parts.length >= 2) return `${parts[1]}/${parts[0]}`;
  return applicationMonth;
}

// ---------------------------------------------------------------------------
// Add form
// ---------------------------------------------------------------------------

function AddFeeForm({ tenantId }: { tenantId: number }) {
  const createMut = useCreateRentsFee();
  const uploadMut = useUploadFeeDocument();
  const [applicationMonth, setApplicationMonth] = useState("");
  const [description, setDescription] = useState("");
  const [subDescription, setSubDescription] = useState("");
  const [price, setPrice] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!description || !price) {
      toast.error("Description et montant requis");
      return;
    }
    setSubmitting(true);
    try {
      const fee = await createMut.mutateAsync({
        tenantId,
        applicationMonth: applicationMonth || null,
        description,
        subDescription: subDescription || null,
        price: Number(price),
      });
      if (file) {
        await uploadMut.mutateAsync({ id: fee.id, file });
      }
      toast.success("Frais ajouté");
      setApplicationMonth("");
      setDescription("");
      setSubDescription("");
      setPrice("");
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={onSubmit}
      className="space-y-2 rounded-md border bg-muted/20 p-3"
    >
      <div className="flex flex-wrap gap-2">
        <div className="space-y-1">
          <Label className="text-xs">Mois</Label>
          <Input
            type="month"
            value={applicationMonth}
            onChange={(e) => setApplicationMonth(e.target.value)}
            className="w-40"
          />
        </div>
        <div className="min-w-[180px] flex-1 space-y-1">
          <Label className="text-xs">Description *</Label>
          <Input
            required
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="ex: Réparation plomberie"
          />
        </div>
        <div className="min-w-[140px] flex-1 space-y-1">
          <Label className="text-xs">Sous-description</Label>
          <Input
            value={subDescription}
            onChange={(e) => setSubDescription(e.target.value)}
            placeholder="optionnel"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs">Montant *</Label>
          <Input
            type="number"
            step="0.01"
            required
            value={price}
            onChange={(e) => setPrice(e.target.value)}
            className="w-28"
          />
        </div>
      </div>
      <div className="flex items-center gap-2">
        <div className="space-y-1">
          <Label className="text-xs">Justificatif</Label>
          <Input
            ref={fileRef}
            type="file"
            className="w-auto cursor-pointer text-sm"
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setFile(e.target.files?.[0] ?? null)
            }
          />
        </div>
        <Button type="submit" size="sm" disabled={submitting} className="mt-5">
          <Plus className="mr-1 h-4 w-4" />
          {submitting ? "…" : "Ajouter"}
        </Button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Fee row
// ---------------------------------------------------------------------------

function FeeRow({ fee }: { fee: RentsFee }) {
  const deleteMut = useDeleteRentsFee();
  const downloadMut = useDownloadFeeDocument();
  const uploadMut = useUploadFeeDocument();
  const deleteDocMut = useDeleteFeeDocument();
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleDownload() {
    try {
      const blob = await downloadMut.mutateAsync(fee.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `justificatif-${fee.id}`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch {
      toast.error("Justificatif non disponible");
    }
  }

  async function handleUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await uploadMut.mutateAsync({ id: fee.id, file });
      toast.success("Justificatif uploadé");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function handleDeleteDoc() {
    try {
      await deleteDocMut.mutateAsync(fee.id);
      toast.success("Justificatif supprimé");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  }

  async function handleDelete() {
    try {
      await deleteMut.mutateAsync(fee.id);
      toast.success("Frais supprimé");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  }

  return (
    <tr className="hover:bg-muted/30">
      <td className="px-3 py-2 text-muted-foreground">
        {formatMonth(fee.applicationMonth)}
      </td>
      <td className="px-3 py-2">
        <div className="font-medium">{fee.description ?? "—"}</div>
        {fee.subDescription && (
          <div className="text-xs text-muted-foreground">{fee.subDescription}</div>
        )}
      </td>
      <td className="px-3 py-2 text-right">{formatCurrency(fee.price)}</td>
      {/* Document */}
      <td className="px-3 py-2 text-center">
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          onChange={(e) => void handleUpload(e)}
        />
        <div className="flex items-center justify-center gap-1">
          {fee.hasDocument ? (
            <>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => void handleDownload()}
                disabled={downloadMut.isPending}
                title="Télécharger le justificatif"
              >
                <Paperclip className="h-4 w-4 text-primary" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => void handleDeleteDoc()}
                disabled={deleteDocMut.isPending}
                title="Supprimer le justificatif"
              >
                <Trash2 className="h-3 w-3 text-muted-foreground" />
              </Button>
            </>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fileRef.current?.click()}
              title="Attacher un justificatif"
            >
              <Upload className="h-4 w-4 text-muted-foreground" />
            </Button>
          )}
        </div>
      </td>
      <td className="px-3 py-2 text-center">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => void handleDelete()}
          disabled={deleteMut.isPending}
          title="Supprimer ce frais"
        >
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Dialog
// ---------------------------------------------------------------------------

export function TenantFeesDialog({ open, onOpenChange, tenant }: Props) {
  const { data, isLoading } = useTenantFees(open && tenant ? tenant.id : null);
  const [showAdd, setShowAdd] = useState(false);

  const fullName = tenant
    ? [tenant.firstName, tenant.name].filter(Boolean).join(" ")
    : "";

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        onOpenChange(v);
        if (!v) setShowAdd(false);
      }}
    >
      <DialogContent className="flex max-h-[85vh] max-w-3xl flex-col">
        <DialogHeader>
          <div className="flex items-center justify-between pr-8">
            <DialogTitle>Frais &amp; charges — {fullName}</DialogTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdd((v) => !v)}
            >
              <Plus className="mr-1 h-4 w-4" />
              {showAdd ? "Masquer" : "Nouveau"}
            </Button>
          </div>
        </DialogHeader>

        {showAdd && tenant && <AddFeeForm tenantId={tenant.id} />}

        {isLoading ? (
          <div className="py-8 text-center text-muted-foreground">Chargement…</div>
        ) : data && data.length > 0 ? (
          <div className="min-h-0 flex-1 overflow-y-auto rounded-md border">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-muted/50 text-left">
                <tr>
                  <th className="px-3 py-2 font-medium">Mois</th>
                  <th className="px-3 py-2 font-medium">Description</th>
                  <th className="px-3 py-2 font-medium text-right">Montant</th>
                  <th className="w-[88px] px-3 py-2 font-medium text-center">Justif.</th>
                  <th className="w-[44px] px-3 py-2"></th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data.map((fee) => (
                  <FeeRow key={fee.id} fee={fee} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center italic text-muted-foreground">
            Aucun frais enregistré.
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
