import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";

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
import { useCreatePlaceFull } from "@/hooks/usePlaces";
import { useOwnersList } from "@/hooks/useOwners";
import { getApiErrorMessage } from "@/lib/apiError";
import type { PlaceFullInput } from "@/api/types";

interface RoomDraft {
  name: string;
  surfaceArea: string;
}

interface UnitDraft {
  name: string;
  level: string;
  flatshare: boolean;
  surfaceArea: string;
  friendlyName: string;
  rooms: RoomDraft[];
}

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const emptyUnit = (): UnitDraft => ({
  name: "",
  level: "",
  flatshare: false,
  surfaceArea: "",
  friendlyName: "",
  rooms: [],
});

const emptyRoom = (): RoomDraft => ({ name: "", surfaceArea: "" });

export function PlaceFullFormDialog({ open, onOpenChange }: Props) {
  const { data: ownersData } = useOwnersList();
  const createMut = useCreatePlaceFull();

  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [zipCode, setZipCode] = useState("");
  const [city, setCity] = useState("");
  const [ownerId, setOwnerId] = useState<string>("");
  const [units, setUnits] = useState<UnitDraft[]>([]);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setName("");
      setAddress("");
      setZipCode("");
      setCity("");
      setOwnerId("");
      setUnits([]);
      setSubmitting(false);
    }
  }, [open]);

  function updateUnit(idx: number, patch: Partial<UnitDraft>) {
    setUnits((prev) =>
      prev.map((u, i) => (i === idx ? { ...u, ...patch } : u)),
    );
  }
  function removeUnit(idx: number) {
    setUnits((prev) => prev.filter((_, i) => i !== idx));
  }
  function addUnit() {
    setUnits((prev) => [...prev, emptyUnit()]);
  }
  function addRoom(unitIdx: number) {
    setUnits((prev) =>
      prev.map((u, i) =>
        i === unitIdx ? { ...u, rooms: [...u.rooms, emptyRoom()] } : u,
      ),
    );
  }
  function updateRoom(unitIdx: number, roomIdx: number, patch: Partial<RoomDraft>) {
    setUnits((prev) =>
      prev.map((u, i) =>
        i === unitIdx
          ? {
              ...u,
              rooms: u.rooms.map((r, j) => (j === roomIdx ? { ...r, ...patch } : r)),
            }
          : u,
      ),
    );
  }
  function removeRoom(unitIdx: number, roomIdx: number) {
    setUnits((prev) =>
      prev.map((u, i) =>
        i === unitIdx
          ? { ...u, rooms: u.rooms.filter((_, j) => j !== roomIdx) }
          : u,
      ),
    );
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      toast.error("Le nom du bien est requis");
      return;
    }
    setSubmitting(true);
    try {
      const payload: PlaceFullInput = {
        place: {
          name: name.trim(),
          address: address.trim() || null,
          zipCode: zipCode === "" ? null : Number(zipCode),
          city: city.trim() || null,
          ownerId: ownerId === "" ? null : Number(ownerId),
        },
        units: units.map((u) => ({
          name: u.name.trim() || null,
          level: u.level.trim() || null,
          flatshare: u.flatshare ? 1 : 0,
          surfaceArea: u.surfaceArea === "" ? null : Number(u.surfaceArea),
          friendlyName: u.friendlyName.trim() || null,
          rooms: u.flatshare
            ? u.rooms.map((r) => ({
                name: r.name.trim() || null,
                surfaceArea: r.surfaceArea === "" ? null : Number(r.surfaceArea),
              }))
            : [],
        })),
      };
      await createMut.mutateAsync(payload);
      toast.success("Bien créé");
      onOpenChange(false);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-3xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Nouveau bien</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-6">
          {/* Place fields */}
          <section className="space-y-3 rounded-md border p-4">
            <h3 className="text-sm font-semibold">Bien</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="placeName">Nom *</Label>
                <Input
                  id="placeName"
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
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm"
                >
                  <option value="">— aucun —</option>
                  {(ownersData?.rows ?? []).map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.name ?? `Propriétaire #${o.id}`}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          {/* Units */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Logements</h3>
              <Button type="button" variant="outline" size="sm" onClick={addUnit}>
                <Plus className="mr-1 h-4 w-4" /> Ajouter un logement
              </Button>
            </div>
            {units.length === 0 && (
              <p className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
                Aucun logement. Cliquez sur « Ajouter un logement ».
              </p>
            )}
            {units.map((u, uIdx) => (
              <div key={uIdx} className="space-y-3 rounded-md border p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Logement {uIdx + 1}</span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => removeUnit(uIdx)}
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label>Nom</Label>
                    <Input
                      value={u.name}
                      onChange={(e) => updateUnit(uIdx, { name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Niveau</Label>
                    <Input
                      value={u.level}
                      onChange={(e) => updateUnit(uIdx, { level: e.target.value })}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Surface (m²)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={u.surfaceArea}
                      onChange={(e) =>
                        updateUnit(uIdx, { surfaceArea: e.target.value })
                      }
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Nom court</Label>
                    <Input
                      value={u.friendlyName}
                      onChange={(e) =>
                        updateUnit(uIdx, { friendlyName: e.target.value })
                      }
                    />
                  </div>
                  <label className="flex items-center gap-2 sm:col-span-2">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-input"
                      checked={u.flatshare}
                      onChange={(e) =>
                        updateUnit(uIdx, { flatshare: e.target.checked })
                      }
                    />
                    <span className="text-sm">Colocation</span>
                  </label>
                </div>

                {u.flatshare && (
                  <div className="space-y-2 rounded-md border bg-muted/20 p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase text-muted-foreground">
                        Chambres
                      </span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => addRoom(uIdx)}
                      >
                        <Plus className="mr-1 h-3 w-3" /> Ajouter une chambre
                      </Button>
                    </div>
                    {u.rooms.length === 0 && (
                      <p className="text-xs italic text-muted-foreground">
                        Pas encore de chambre.
                      </p>
                    )}
                    {u.rooms.map((r, rIdx) => (
                      <div
                        key={rIdx}
                        className="grid grid-cols-[1fr_120px_auto] items-end gap-2"
                      >
                        <div className="space-y-1">
                          <Label className="text-xs">Nom</Label>
                          <Input
                            value={r.name}
                            onChange={(e) =>
                              updateRoom(uIdx, rIdx, { name: e.target.value })
                            }
                          />
                        </div>
                        <div className="space-y-1">
                          <Label className="text-xs">Surface (m²)</Label>
                          <Input
                            type="number"
                            step="0.01"
                            value={r.surfaceArea}
                            onChange={(e) =>
                              updateRoom(uIdx, rIdx, { surfaceArea: e.target.value })
                            }
                          />
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeRoom(uIdx, rIdx)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </section>

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
