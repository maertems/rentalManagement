import { useEffect, useState } from "react";
import { toast } from "sonner";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useOwnerParams, useUpdateOwnerParams } from "@/hooks/useParams";
import { getApiErrorMessage } from "@/lib/apiError";
import type { Owner } from "@/api/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  owner: Owner | null;
}

export function OwnerParamsDialog({ open, onOpenChange, owner }: Props) {
  const { data, isLoading } = useOwnerParams(open && owner ? owner.id : null);
  const updateMut = useUpdateOwnerParams();

  const [rentReceiptDay, setRentReceiptDay] = useState("");

  useEffect(() => {
    if (data) {
      setRentReceiptDay(data.rentReceiptDay != null ? String(data.rentReceiptDay) : "");
    }
  }, [data]);

  async function handleSave() {
    if (!owner) return;
    const day = rentReceiptDay ? Number(rentReceiptDay) : null;
    if (day !== null && (day < 1 || day > 31 || !Number.isInteger(day))) {
      toast.error("Le jour doit être compris entre 1 et 31");
      return;
    }
    try {
      await updateMut.mutateAsync({ ownerId: owner.id, input: { rentReceiptDay: day } });
      toast.success("Paramètres enregistrés");
      onOpenChange(false);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  }

  const ownerName = owner?.name ?? "—";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Paramètres — {ownerName}</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="py-6 text-center text-sm text-muted-foreground">Chargement…</div>
        ) : (
          <div className="space-y-4 py-2">
            <div className="space-y-1.5">
              <Label htmlFor="rentReceiptDay">
                Jour de génération des quittances
              </Label>
              <Input
                id="rentReceiptDay"
                type="number"
                min={1}
                max={31}
                placeholder="ex : 1"
                value={rentReceiptDay}
                onChange={(e) => setRentReceiptDay(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Jour du mois auquel le cron génère les quittances (1–31).
                Si le mois est plus court, le dernier jour du mois est utilisé.
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button onClick={() => void handleSave()} disabled={updateMut.isPending || isLoading}>
            {updateMut.isPending ? "…" : "Enregistrer"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
