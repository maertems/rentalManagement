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
import { useUpdatePlace } from "@/hooks/usePlaces";
import { useOwnersList } from "@/hooks/useOwners";
import { getApiErrorMessage } from "@/lib/apiError";
import type { Place } from "@/api/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  place: Place | null;
}

export function PlaceEditDialog({ open, onOpenChange, place }: Props) {
  const { data: ownersData } = useOwnersList();
  const updateMut = useUpdatePlace();

  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [zipCode, setZipCode] = useState("");
  const [city, setCity] = useState("");
  const [ownerId, setOwnerId] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open && place) {
      setName(place.name ?? "");
      setAddress(place.address ?? "");
      setZipCode(place.zipCode !== null ? String(place.zipCode) : "");
      setCity(place.city ?? "");
      setOwnerId(place.ownerId !== null ? String(place.ownerId) : "");
      setSubmitting(false);
    }
  }, [open, place]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!place) return;
    if (!name.trim()) {
      toast.error("Le nom est requis");
      return;
    }
    setSubmitting(true);
    try {
      await updateMut.mutateAsync({
        id: place.id,
        input: {
          name: name.trim(),
          address: address.trim() || null,
          zipCode: zipCode === "" ? null : Number(zipCode),
          city: city.trim() || null,
          ownerId: ownerId === "" ? null : Number(ownerId),
        },
      });
      toast.success("Bien modifié");
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
          <DialogTitle>Modifier le bien</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="name">Nom *</Label>
            <Input
              id="name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="address">Adresse</Label>
            <Input
              id="address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="zipCode">Code postal</Label>
            <Input
              id="zipCode"
              type="text"
              inputMode="numeric"
              value={zipCode}
              onChange={(e) => setZipCode(e.target.value.replace(/\D/g, ""))}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="city">Ville</Label>
            <Input
              id="city"
              value={city}
              onChange={(e) => setCity(e.target.value)}
            />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="ownerId">Propriétaire</Label>
            <select
              id="ownerId"
              value={ownerId}
              onChange={(e) => setOwnerId(e.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
            >
              <option value="">— aucun —</option>
              {(ownersData?.rows ?? []).map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name ?? `Propriétaire #${o.id}`}
                </option>
              ))}
            </select>
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
