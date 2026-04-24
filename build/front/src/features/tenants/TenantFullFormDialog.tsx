import { useEffect, useMemo, useState, type FormEvent } from "react";
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
import { useAllPlacesUnits, useAllRooms, usePlacesList } from "@/hooks/usePlaces";
import { useCreateTenantFull } from "@/hooks/useTenants";
import { getApiErrorMessage } from "@/lib/apiError";
import type { TenantFullInput, TenantGenre } from "@/api/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TenantFullFormDialog({ open, onOpenChange }: Props) {
  const { data: places } = usePlacesList();
  const { data: units } = useAllPlacesUnits();
  const { data: rooms } = useAllRooms();
  const createMut = useCreateTenantFull();

  const [genre, setGenre] = useState<TenantGenre | "">("");
  const [firstName, setFirstName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [placeUnitId, setPlaceUnitId] = useState<string>("");
  const [placeUnitRoomId, setPlaceUnitRoomId] = useState<string>("");
  const [dateEntrance, setDateEntrance] = useState("");
  const [withdrawDay, setWithdrawDay] = useState("1");
  const [withdrawName, setWithdrawName] = useState("");
  const [loyer, setLoyer] = useState("");
  const [charges, setCharges] = useState("");
  const [garantie, setGarantie] = useState("");
  const [cautionReceived, setCautionReceived] = useState(false);
  const [cautionDate, setCautionDate] = useState("");
  const [sendNotice, setSendNotice] = useState(false);
  const [sendReceipt, setSendReceipt] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setGenre("");
      setFirstName("");
      setName("");
      setEmail("");
      setPhone("");
      setPlaceUnitId("");
      setPlaceUnitRoomId("");
      setDateEntrance("");
      setWithdrawDay("1");
      setWithdrawName("");
      setLoyer("");
      setCharges("");
      setGarantie("");
      setCautionReceived(false);
      setCautionDate("");
      setSendNotice(false);
      setSendReceipt(false);
      setSubmitting(false);
    }
  }, [open]);

  const placesById = useMemo(
    () => new Map(places?.map((p) => [p.id, p]) ?? []),
    [places],
  );
  const selectedUnit = useMemo(() => {
    if (!placeUnitId) return null;
    return units?.find((u) => u.id === Number(placeUnitId)) ?? null;
  }, [units, placeUnitId]);
  const isFlatshare = !!selectedUnit?.flatshare;
  const roomsForUnit = useMemo(
    () =>
      selectedUnit
        ? (rooms ?? []).filter((r) => r.placesUnitsId === selectedUnit.id)
        : [],
    [rooms, selectedUnit],
  );

  function unitLabel(unitId: number) {
    const u = units?.find((x) => x.id === unitId);
    if (!u) return `#${unitId}`;
    const place = u.placeId !== null ? placesById.get(u.placeId) : null;
    const placeName = place?.name ?? "?";
    const unitName = u.friendlyName || u.name || `#${u.id}`;
    return `${placeName} — ${unitName}${u.flatshare ? " (coloc)" : ""}`;
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!firstName.trim() && !name.trim()) {
      toast.error("Renseignez au moins un prénom ou un nom");
      return;
    }
    if (!placeUnitId) {
      toast.error("Sélectionnez un logement");
      return;
    }
    if (isFlatshare && !placeUnitRoomId) {
      toast.error("Sélectionnez une chambre pour la colocation");
      return;
    }
    if (!loyer || !charges || !garantie) {
      toast.error("Les montants Loyer / Charges / Garantie sont requis");
      return;
    }
    setSubmitting(true);
    try {
      const payload: TenantFullInput = {
        tenant: {
          genre: (genre as TenantGenre) || null,
          firstName: firstName.trim() || null,
          name: name.trim() || null,
          email: email.trim() || null,
          phone: phone.trim() || null,
          placeUnitId: Number(placeUnitId),
          placeUnitRoomId: placeUnitRoomId ? Number(placeUnitRoomId) : null,
          dateEntrance: dateEntrance ? `${dateEntrance}T00:00:00` : null,
          withdrawDay: Number(withdrawDay) || 1,
          withdrawName: withdrawName.trim() || null,
          billingSameAsRental: 1,
          sendNoticeOfLeaseRental: sendNotice ? 1 : 0,
          sendLeaseRental: sendReceipt ? 1 : 0,
        },
        rents: {
          loyer: { price: Number(loyer) },
          charges: { price: Number(charges) },
          garantie: { price: Number(garantie) },
        },
        cautionReceipt: cautionReceived
          ? {
              amount: Number(garantie),
              periodBegin: cautionDate ? `${cautionDate}T00:00:00` : null,
              paid: 1,
            }
          : null,
      };
      await createMut.mutateAsync(payload);
      toast.success("Locataire créé");
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
          <DialogTitle>Nouveau locataire</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-6">
          {/* Identité */}
          <section className="space-y-3 rounded-md border p-4">
            <h3 className="text-sm font-semibold">Identité</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="genre">Civilité</Label>
                <select
                  id="genre"
                  value={genre}
                  onChange={(e) => setGenre(e.target.value as TenantGenre | "")}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                >
                  <option value="">—</option>
                  <option value="M">M.</option>
                  <option value="Mme">Mme</option>
                  <option value="Mlle">Mlle</option>
                  <option value="Societe">Société</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="phone">Téléphone</Label>
                <Input
                  id="phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="firstName">Prénom</Label>
                <Input
                  id="firstName"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="name">Nom</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
            </div>
          </section>

          {/* Logement */}
          <section className="space-y-3 rounded-md border p-4">
            <h3 className="text-sm font-semibold">Logement</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="placeUnit">Logement *</Label>
                <select
                  id="placeUnit"
                  value={placeUnitId}
                  onChange={(e) => {
                    setPlaceUnitId(e.target.value);
                    setPlaceUnitRoomId("");
                  }}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                  required
                >
                  <option value="">— sélectionner —</option>
                  {units?.map((u) => (
                    <option key={u.id} value={u.id}>
                      {unitLabel(u.id)}
                    </option>
                  ))}
                </select>
              </div>
              {isFlatshare && (
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="room">Chambre *</Label>
                  <select
                    id="room"
                    value={placeUnitRoomId}
                    onChange={(e) => setPlaceUnitRoomId(e.target.value)}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                    required
                  >
                    <option value="">— sélectionner —</option>
                    {roomsForUnit.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name ?? `Chambre #${r.id}`}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="dateEntrance">Date d'entrée</Label>
                <Input
                  id="dateEntrance"
                  type="date"
                  value={dateEntrance}
                  onChange={(e) => setDateEntrance(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="withdrawDay">Jour de prélèvement</Label>
                <Input
                  id="withdrawDay"
                  type="number"
                  min={1}
                  max={31}
                  value={withdrawDay}
                  onChange={(e) => setWithdrawDay(e.target.value)}
                />
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="withdrawName">Nom du virement</Label>
                <Input
                  id="withdrawName"
                  value={withdrawName}
                  onChange={(e) => setWithdrawName(e.target.value)}
                  placeholder="Nom tel qu'il apparaît sur le relevé bancaire"
                />
              </div>
            </div>
          </section>

          {/* Loyers */}
          <section className="space-y-3 rounded-md border p-4">
            <h3 className="text-sm font-semibold">Loyers</h3>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label htmlFor="loyer">Loyer mensuel (€) *</Label>
                <Input
                  id="loyer"
                  type="number"
                  step="0.01"
                  required
                  value={loyer}
                  onChange={(e) => setLoyer(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="charges">Charges mensuelles (€) *</Label>
                <Input
                  id="charges"
                  type="number"
                  step="0.01"
                  required
                  value={charges}
                  onChange={(e) => setCharges(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="garantie">Caution (€) *</Label>
                <Input
                  id="garantie"
                  type="number"
                  step="0.01"
                  required
                  value={garantie}
                  onChange={(e) => setGarantie(e.target.value)}
                />
              </div>
            </div>
          </section>

          {/* Notifications */}
          <section className="space-y-2 rounded-md border p-4">
            <h3 className="text-sm font-semibold">Notifications par email</h3>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-input"
                checked={sendNotice}
                onChange={(e) => setSendNotice(e.target.checked)}
              />
              <span>Recevoir l'avis d'échéance</span>
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-input"
                checked={sendReceipt}
                onChange={(e) => setSendReceipt(e.target.checked)}
              />
              <span>Recevoir la quittance de loyer</span>
            </label>
          </section>

          {/* Caution */}
          <section className="space-y-3 rounded-md border p-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-input"
                checked={cautionReceived}
                onChange={(e) => setCautionReceived(e.target.checked)}
              />
              <span>Caution déjà reçue</span>
            </label>
            {cautionReceived && (
              <div className="space-y-1.5">
                <Label htmlFor="cautionDate">Date de réception</Label>
                <Input
                  id="cautionDate"
                  type="date"
                  value={cautionDate}
                  onChange={(e) => setCautionDate(e.target.value)}
                />
              </div>
            )}
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
