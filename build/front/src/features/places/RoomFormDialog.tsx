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
import { useCreateRoom, useUpdateRoom } from "@/hooks/usePlaces";
import { getApiErrorMessage } from "@/lib/apiError";
import type { PlacesUnitsRoom } from "@/api/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  // Create mode: provide placesUnitsId. Edit mode: provide room.
  placesUnitsId?: number;
  room?: PlacesUnitsRoom | null;
}

export function RoomFormDialog({
  open,
  onOpenChange,
  placesUnitsId,
  room,
}: Props) {
  const isEdit = !!room;
  const createMut = useCreateRoom();
  const updateMut = useUpdateRoom();

  const [name, setName] = useState("");
  const [surfaceArea, setSurfaceArea] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      if (room) {
        setName(room.name ?? "");
        setSurfaceArea(room.surfaceArea !== null ? String(room.surfaceArea) : "");
      } else {
        setName("");
        setSurfaceArea("");
      }
      setSubmitting(false);
    }
  }, [open, room]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        name: name.trim() || null,
        surfaceArea: surfaceArea === "" ? null : Number(surfaceArea),
      };
      if (isEdit && room) {
        await updateMut.mutateAsync({ id: room.id, input: payload });
        toast.success("Chambre modifiée");
      } else {
        if (!placesUnitsId) {
          toast.error("Logement parent manquant");
          return;
        }
        await createMut.mutateAsync({ ...payload, placesUnitsId });
        toast.success("Chambre ajoutée");
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
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier la chambre" : "Ajouter une chambre"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="rname">Nom</Label>
            <Input
              id="rname"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="rsurface">Surface (m²)</Label>
            <Input
              id="rsurface"
              type="number"
              step="0.01"
              value={surfaceArea}
              onChange={(e) => setSurfaceArea(e.target.value)}
            />
          </div>
          <DialogFooter>
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
