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
import {
  useCreateRent,
  useTenantRents,
  useUpdateRent,
  useUpdateTenant,
} from "@/hooks/useTenants";
import { getApiErrorMessage } from "@/lib/apiError";
import type { Rent, Tenant, TenantGenre } from "@/api/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tenant: Tenant | null;
}

function dateInputValue(v: string | null): string {
  if (!v) return "";
  return v.slice(0, 10); // "YYYY-MM-DD..." → "YYYY-MM-DD"
}

export function TenantEditDialog({ open, onOpenChange, tenant }: Props) {
  const { data: places } = usePlacesList();
  const { data: units } = useAllPlacesUnits();
  const { data: rooms } = useAllRooms();
  const updateMut = useUpdateTenant();
  const updateRentMut = useUpdateRent();
  const createRentMut = useCreateRent();
  const { data: tenantRents } = useTenantRents(open && tenant ? tenant.id : null);

  const [genre, setGenre] = useState<TenantGenre | "">("");
  const [firstName, setFirstName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [placeUnitId, setPlaceUnitId] = useState<string>("");
  const [placeUnitRoomId, setPlaceUnitRoomId] = useState<string>("");
  const [dateEntrance, setDateEntrance] = useState("");
  const [dateExit, setDateExit] = useState("");
  const [withdrawDay, setWithdrawDay] = useState("1");
  const [withdrawName, setWithdrawName] = useState("");
  const [billingSameAsRental, setBillingSameAsRental] = useState(true);
  const [billingAddress, setBillingAddress] = useState("");
  const [billingZipCode, setBillingZipCode] = useState("");
  const [billingCity, setBillingCity] = useState("");
  const [billingPhone, setBillingPhone] = useState("");
  const [loyerPrice, setLoyerPrice] = useState("");
  const [chargesPrice, setChargesPrice] = useState("");
  const [garantiePrice, setGarantiePrice] = useState("");
  const [sendNotice, setSendNotice] = useState(false);
  const [sendReceipt, setSendReceipt] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open && tenant) {
      setGenre((tenant.genre ?? "") as TenantGenre | "");
      setFirstName(tenant.firstName ?? "");
      setName(tenant.name ?? "");
      setEmail(tenant.email ?? "");
      setPhone(tenant.phone ?? "");
      setPlaceUnitId(tenant.placeUnitId !== null ? String(tenant.placeUnitId) : "");
      setPlaceUnitRoomId(
        tenant.placeUnitRoomId !== null ? String(tenant.placeUnitRoomId) : "",
      );
      setDateEntrance(dateInputValue(tenant.dateEntrance));
      setDateExit(dateInputValue(tenant.dateExit));
      setWithdrawDay(String(tenant.withdrawDay ?? 1));
      setWithdrawName(tenant.withdrawName ?? "");
      setBillingSameAsRental(!!tenant.billingSameAsRental);
      setBillingAddress(tenant.billingAddress ?? "");
      setBillingZipCode(
        tenant.billingZipCode !== null ? String(tenant.billingZipCode) : "",
      );
      setBillingCity(tenant.billingCity ?? "");
      setBillingPhone(tenant.billingPhone ?? "");
      setSendNotice(!!tenant.sendNoticeOfLeaseRental);
      setSendReceipt(!!tenant.sendLeaseRental);
      setSubmitting(false);
    }
  }, [open, tenant]);

  // Hydrate rent prices when the tenant's rents arrive (or change).
  useEffect(() => {
    if (open && tenantRents) {
      const findActive = (type: Rent["type"]) =>
        tenantRents.find((r) => r.type === type && r.active);
      const loyer = findActive("Loyer");
      const charges = findActive("Charges");
      const garantie = findActive("Garantie");
      setLoyerPrice(loyer?.price !== undefined && loyer?.price !== null ? String(loyer.price) : "");
      setChargesPrice(
        charges?.price !== undefined && charges?.price !== null ? String(charges.price) : "",
      );
      setGarantiePrice(
        garantie?.price !== undefined && garantie?.price !== null ? String(garantie.price) : "",
      );
    }
  }, [open, tenantRents]);

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
    if (!tenant) return;
    setSubmitting(true);
    try {
      await updateMut.mutateAsync({
        id: tenant.id,
        input: {
          genre: (genre as TenantGenre) || null,
          firstName: firstName.trim() || null,
          name: name.trim() || null,
          email: email.trim() || null,
          phone: phone.trim() || null,
          placeUnitId: placeUnitId ? Number(placeUnitId) : null,
          placeUnitRoomId:
            isFlatshare && placeUnitRoomId ? Number(placeUnitRoomId) : null,
          dateEntrance: dateEntrance ? `${dateEntrance}T00:00:00` : null,
          dateExit: dateExit ? `${dateExit}T00:00:00` : null,
          withdrawDay: Number(withdrawDay) || 1,
          withdrawName: withdrawName.trim() || null,
          billingSameAsRental: billingSameAsRental ? 1 : 0,
          billingAddress: billingSameAsRental
            ? null
            : billingAddress.trim() || null,
          billingZipCode: billingSameAsRental
            ? null
            : billingZipCode === ""
              ? null
              : Number(billingZipCode),
          billingCity: billingSameAsRental ? null : billingCity.trim() || null,
          billingPhone: billingSameAsRental
            ? null
            : billingPhone.trim() || null,
          sendNoticeOfLeaseRental: sendNotice ? 1 : 0,
          sendLeaseRental: sendReceipt ? 1 : 0,
        },
      });

      // Save rent price changes (Loyer / Charges / Garantie).
      // For each type: if an active rent exists, PATCH its price; otherwise
      // create a new active rent with that price.
      const updates: Array<{ type: Rent["type"]; raw: string }> = [
        { type: "Loyer", raw: loyerPrice },
        { type: "Charges", raw: chargesPrice },
        { type: "Garantie", raw: garantiePrice },
      ];
      for (const { type, raw } of updates) {
        if (raw === "") continue; // leave untouched
        const newPrice = Number(raw);
        if (Number.isNaN(newPrice)) continue;
        const existing = (tenantRents ?? []).find(
          (r) => r.type === type && r.active,
        );
        if (existing) {
          if (Number(existing.price ?? 0) !== newPrice) {
            await updateRentMut.mutateAsync({
              id: existing.id,
              input: { price: newPrice },
            });
          }
        } else {
          await createRentMut.mutateAsync({
            tenantId: tenant.id,
            type: type ?? "Loyer",
            price: newPrice,
            active: 1,
          });
        }
      }

      toast.success("Locataire modifié");
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
          <DialogTitle>Modifier le locataire</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-6">
          {/* Identité */}
          <section className="space-y-3 rounded-md border p-4">
            <h3 className="text-sm font-semibold">Identité</h3>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="egenre">Civilité</Label>
                <select
                  id="egenre"
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
                <Label htmlFor="ephone">Téléphone</Label>
                <Input
                  id="ephone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="efirstName">Prénom</Label>
                <Input
                  id="efirstName"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ename">Nom</Label>
                <Input
                  id="ename"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="eemail">Email</Label>
                <Input
                  id="eemail"
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
                <Label htmlFor="eplaceUnit">Logement</Label>
                <select
                  id="eplaceUnit"
                  value={placeUnitId}
                  onChange={(e) => {
                    setPlaceUnitId(e.target.value);
                    setPlaceUnitRoomId("");
                  }}
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                >
                  <option value="">— aucun —</option>
                  {units?.map((u) => (
                    <option key={u.id} value={u.id}>
                      {unitLabel(u.id)}
                    </option>
                  ))}
                </select>
              </div>
              {isFlatshare && (
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="eroom">Chambre</Label>
                  <select
                    id="eroom"
                    value={placeUnitRoomId}
                    onChange={(e) => setPlaceUnitRoomId(e.target.value)}
                    className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
                  >
                    <option value="">— aucune —</option>
                    {roomsForUnit.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.name ?? `Chambre #${r.id}`}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div className="space-y-1.5">
                <Label htmlFor="edateEntrance">Date d'entrée</Label>
                <Input
                  id="edateEntrance"
                  type="date"
                  value={dateEntrance}
                  onChange={(e) => setDateEntrance(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="edateExit">Date de sortie</Label>
                <Input
                  id="edateExit"
                  type="date"
                  value={dateExit}
                  onChange={(e) => setDateExit(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ewithdrawDay">Jour de prélèvement</Label>
                <Input
                  id="ewithdrawDay"
                  type="number"
                  min={1}
                  max={31}
                  value={withdrawDay}
                  onChange={(e) => setWithdrawDay(e.target.value)}
                />
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="ewithdrawName">Nom du virement</Label>
                <Input
                  id="ewithdrawName"
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
                <Label htmlFor="eloyer">Loyer mensuel (€)</Label>
                <Input
                  id="eloyer"
                  type="number"
                  step="0.01"
                  value={loyerPrice}
                  onChange={(e) => setLoyerPrice(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="echarges">Charges mensuelles (€)</Label>
                <Input
                  id="echarges"
                  type="number"
                  step="0.01"
                  value={chargesPrice}
                  onChange={(e) => setChargesPrice(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="egarantie">Caution (€)</Label>
                <Input
                  id="egarantie"
                  type="number"
                  step="0.01"
                  value={garantiePrice}
                  onChange={(e) => setGarantiePrice(e.target.value)}
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Modifier ces montants n'affecte que les futures quittances.
            </p>
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

          {/* Facturation */}
          <section className="space-y-3 rounded-md border p-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-input"
                checked={billingSameAsRental}
                onChange={(e) => setBillingSameAsRental(e.target.checked)}
              />
              <span>Même adresse de facturation que la location</span>
            </label>
            {!billingSameAsRental && (
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="ebillingAddress">Adresse</Label>
                  <Input
                    id="ebillingAddress"
                    value={billingAddress}
                    onChange={(e) => setBillingAddress(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="ebillingZipCode">Code postal</Label>
                  <Input
                    id="ebillingZipCode"
                    type="text"
                    inputMode="numeric"
                    value={billingZipCode}
                    onChange={(e) => setBillingZipCode(e.target.value.replace(/\D/g, ""))}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="ebillingCity">Ville</Label>
                  <Input
                    id="ebillingCity"
                    value={billingCity}
                    onChange={(e) => setBillingCity(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="ebillingPhone">Téléphone</Label>
                  <Input
                    id="ebillingPhone"
                    value={billingPhone}
                    onChange={(e) => setBillingPhone(e.target.value)}
                  />
                </div>
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
