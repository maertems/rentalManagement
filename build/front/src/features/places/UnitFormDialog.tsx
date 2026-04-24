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
import { useCreatePlacesUnit, useUpdatePlacesUnit } from "@/hooks/usePlaces";
import { getApiErrorMessage } from "@/lib/apiError";
import type { PlacesUnit } from "@/api/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  // Create mode: provide placeId. Edit mode: provide unit (placeId is read from it).
  placeId?: number;
  unit?: PlacesUnit | null;
}

export function UnitFormDialog({ open, onOpenChange, placeId, unit }: Props) {
  const isEdit = !!unit;
  const createMut = useCreatePlacesUnit();
  const updateMut = useUpdatePlacesUnit();

  const [name, setName] = useState("");
  const [level, setLevel] = useState("");
  const [surfaceArea, setSurfaceArea] = useState("");
  const [friendlyName, setFriendlyName] = useState("");
  const [flatshare, setFlatshare] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      if (unit) {
        setName(unit.name ?? "");
        setLevel(unit.level ?? "");
        setSurfaceArea(unit.surfaceArea !== null ? String(unit.surfaceArea) : "");
        setFriendlyName(unit.friendlyName ?? "");
        setFlatshare(!!unit.flatshare);
      } else {
        setName("");
        setLevel("");
        setSurfaceArea("");
        setFriendlyName("");
        setFlatshare(false);
      }
      setSubmitting(false);
    }
  }, [open, unit]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        name: name.trim() || null,
        level: level.trim() || null,
        flatshare: flatshare ? 1 : 0,
        surfaceArea: surfaceArea === "" ? null : Number(surfaceArea),
        friendlyName: friendlyName.trim() || null,
      };
      if (isEdit && unit) {
        await updateMut.mutateAsync({ id: unit.id, input: payload });
        toast.success("Logement modifié");
      } else {
        if (!placeId) {
          toast.error("Bien parent manquant");
          return;
        }
        await createMut.mutateAsync({ ...payload, placeId });
        toast.success("Logement ajouté");
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
            {isEdit ? "Modifier le logement" : "Ajouter un logement"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="uname">Nom</Label>
            <Input
              id="uname"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ulevel">Niveau</Label>
            <Input
              id="ulevel"
              value={level}
              onChange={(e) => setLevel(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="usurface">Surface (m²)</Label>
            <Input
              id="usurface"
              type="number"
              step="0.01"
              value={surfaceArea}
              onChange={(e) => setSurfaceArea(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ufriendly">Nom court</Label>
            <Input
              id="ufriendly"
              value={friendlyName}
              onChange={(e) => setFriendlyName(e.target.value)}
            />
          </div>
          <label className="flex items-center gap-2 sm:col-span-2">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-input"
              checked={flatshare}
              onChange={(e) => setFlatshare(e.target.checked)}
            />
            <span className="text-sm">Colocation</span>
          </label>
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
