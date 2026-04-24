import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateOwner, useUpdateOwner } from "@/hooks/useOwners";
import type { Owner, OwnerInput } from "@/api/types";
import { getApiErrorMessage } from "@/lib/apiError";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  owner: Owner | null; // null = create mode
}

const empty: OwnerInput = {
  name: "",
  email: "",
  phoneNumber: "",
  address: "",
  zipCode: null,
  city: "",
  iban: "",
};

export function OwnerFormDialog({ open, onOpenChange, owner }: Props) {
  const isEdit = owner !== null;
  const [form, setForm] = useState<OwnerInput>(empty);
  const [submitting, setSubmitting] = useState(false);
  const createMut = useCreateOwner();
  const updateMut = useUpdateOwner();

  useEffect(() => {
    if (open) {
      setForm(
        owner
          ? {
              name: owner.name,
              email: owner.email,
              phoneNumber: owner.phoneNumber,
              address: owner.address,
              zipCode: owner.zipCode,
              city: owner.city,
              iban: owner.iban,
            }
          : empty,
      );
    }
  }, [open, owner]);

  function setField<K extends keyof OwnerInput>(key: K, value: OwnerInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!form.name?.trim()) {
      toast.error("Le nom est requis");
      return;
    }
    setSubmitting(true);
    try {
      // Normalize empty strings to null for optional columns
      const payload: OwnerInput = {
        name: form.name?.trim() || null,
        email: form.email?.trim() || null,
        phoneNumber: form.phoneNumber?.trim() || null,
        address: form.address?.trim() || null,
        zipCode: form.zipCode ?? null,
        city: form.city?.trim() || null,
        iban: form.iban?.trim() || null,
      };
      if (isEdit && owner) {
        await updateMut.mutateAsync({ id: owner.id, input: payload });
        toast.success("Propriétaire modifié");
      } else {
        await createMut.mutateAsync(payload);
        toast.success("Propriétaire créé");
      }
      onOpenChange(false);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier le propriétaire" : "Nouveau propriétaire"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="name">Nom *</Label>
            <Input
              id="name"
              required
              value={form.name ?? ""}
              onChange={(e) => setField("name", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={form.email ?? ""}
              onChange={(e) => setField("email", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="phoneNumber">Téléphone</Label>
            <Input
              id="phoneNumber"
              value={form.phoneNumber ?? ""}
              onChange={(e) => setField("phoneNumber", e.target.value)}
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="address">Adresse</Label>
            <Input
              id="address"
              value={form.address ?? ""}
              onChange={(e) => setField("address", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="zipCode">Code postal</Label>
            <Input
              id="zipCode"
              type="text"
              inputMode="numeric"
              value={form.zipCode ?? ""}
              onChange={(e) =>
                setField(
                  "zipCode",
                  e.target.value === "" ? null : Number(e.target.value.replace(/\D/g, "")),
                )
              }
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="city">Ville</Label>
            <Input
              id="city"
              value={form.city ?? ""}
              onChange={(e) => setField("city", e.target.value)}
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="iban">IBAN</Label>
            <Input
              id="iban"
              value={form.iban ?? ""}
              onChange={(e) => setField("iban", e.target.value)}
            />
          </div>
          <DialogFooter className="sm:col-span-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
            >
              Annuler
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "…" : "Enregistrer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
