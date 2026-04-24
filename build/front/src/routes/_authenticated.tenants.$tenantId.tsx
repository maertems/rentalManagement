import { Fragment, useEffect, useMemo, useState, type ReactNode } from "react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { ArrowLeft, CheckCircle2, Pencil, RotateCcw, Save, UserMinus, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  useCreateRent,
  useTenant,
  useTenantRents,
  useUpdateRent,
  useUpdateTenant,
} from "@/hooks/useTenants";
import { useAllPlacesUnits, useAllRooms, usePlacesList } from "@/hooks/usePlaces";
import { getApiErrorMessage } from "@/lib/apiError";
import { formatCurrency, formatDate } from "@/lib/formatters";
import type { Rent, TenantGenre } from "@/api/types";

const GENRE_LABEL: Record<string, string> = {
  M: "M.",
  Mme: "Mme",
  Mlle: "Mlle",
  Societe: "Société",
};

// ---------------------------------------------------------------------------
// Read-only field display
// ---------------------------------------------------------------------------

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <div className="text-sm">{children}</div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

function TenantDetailPage() {
  const { tenantId } = Route.useParams();
  const navigate = useNavigate();
  const id = Number(tenantId);

  const [editing, setEditing] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const { data: tenant, isLoading } = useTenant(id);
  const { data: tenantRents } = useTenantRents(editing || true ? id : null);
  const { data: places } = usePlacesList();
  const { data: units } = useAllPlacesUnits();
  const { data: rooms } = useAllRooms();

  const updateMut = useUpdateTenant();
  const updateRentMut = useUpdateRent();
  const createRentMut = useCreateRent();

  // Form state
  const [genre, setGenre] = useState<TenantGenre | "">("");
  const [firstName, setFirstName] = useState("");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [placeUnitId, setPlaceUnitId] = useState("");
  const [placeUnitRoomId, setPlaceUnitRoomId] = useState("");
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

  function hydrateFromTenant() {
    if (!tenant) return;
    setGenre((tenant.genre ?? "") as TenantGenre | "");
    setFirstName(tenant.firstName ?? "");
    setName(tenant.name ?? "");
    setEmail(tenant.email ?? "");
    setPhone(tenant.phone ?? "");
    setPlaceUnitId(tenant.placeUnitId !== null ? String(tenant.placeUnitId) : "");
    setPlaceUnitRoomId(tenant.placeUnitRoomId !== null ? String(tenant.placeUnitRoomId) : "");
    setDateEntrance(tenant.dateEntrance ? tenant.dateEntrance.slice(0, 10) : "");
    setDateExit(tenant.dateExit ? tenant.dateExit.slice(0, 10) : "");
    setWithdrawDay(String(tenant.withdrawDay ?? 1));
    setWithdrawName(tenant.withdrawName ?? "");
    setBillingSameAsRental(!!tenant.billingSameAsRental);
    setBillingAddress(tenant.billingAddress ?? "");
    setBillingZipCode(tenant.billingZipCode !== null ? String(tenant.billingZipCode) : "");
    setBillingCity(tenant.billingCity ?? "");
    setBillingPhone(tenant.billingPhone ?? "");
    setSendNotice(!!tenant.sendNoticeOfLeaseRental);
    setSendReceipt(!!tenant.sendLeaseRental);
  }

  function hydrateFromRents() {
    if (!tenantRents) return;
    const find = (type: Rent["type"]) => tenantRents.find((r) => r.type === type && r.active);
    const loyer = find("Loyer");
    const charges = find("Charges");
    const garantie = find("Garantie");
    setLoyerPrice(loyer?.price != null ? String(loyer.price) : "");
    setChargesPrice(charges?.price != null ? String(charges.price) : "");
    setGarantiePrice(garantie?.price != null ? String(garantie.price) : "");
  }

  // Hydrate form when data arrives
  useEffect(() => { hydrateFromTenant(); }, [tenant]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { hydrateFromRents(); }, [tenantRents]); // eslint-disable-line react-hooks/exhaustive-deps

  const placesById = useMemo(() => new Map(places?.map((p) => [p.id, p]) ?? []), [places]);

  const selectedUnit = useMemo(
    () => (placeUnitId ? units?.find((u) => u.id === Number(placeUnitId)) ?? null : null),
    [units, placeUnitId],
  );
  const isFlatshare = !!selectedUnit?.flatshare;
  const roomsForUnit = useMemo(
    () => (selectedUnit ? (rooms ?? []).filter((r) => r.placesUnitsId === selectedUnit.id) : []),
    [rooms, selectedUnit],
  );

  // Place address for the currently selected unit in edit mode (for greyed-out billing fields)
  const rentalPlaceForEdit = useMemo(
    () => (selectedUnit?.placeId != null ? (placesById.get(selectedUnit.placeId) ?? null) : null),
    [selectedUnit, placesById],
  );

  // Place address for read mode (based on saved tenant data)
  const tenantPlace = useMemo(() => {
    if (!tenant?.placeUnitId) return null;
    const u = units?.find((x) => x.id === tenant.placeUnitId);
    return u?.placeId != null ? (placesById.get(u.placeId) ?? null) : null;
  }, [tenant, units, placesById]);

  function unitLabel(unitId: number) {
    const u = units?.find((x) => x.id === unitId);
    if (!u) return `#${unitId}`;
    const place = u.placeId !== null ? placesById.get(u.placeId) : null;
    const placeName = place?.name ?? "?";
    const unitName = u.friendlyName || u.name || `#${u.id}`;
    return `${placeName} — ${unitName}${u.flatshare ? " (coloc)" : ""}`;
  }

  function cancelEdit() {
    hydrateFromTenant();
    hydrateFromRents();
    setEditing(false);
  }

  async function handleSave() {
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
          placeUnitRoomId: isFlatshare && placeUnitRoomId ? Number(placeUnitRoomId) : null,
          dateEntrance: dateEntrance ? `${dateEntrance}T00:00:00` : null,
          dateExit: dateExit ? `${dateExit}T00:00:00` : null,
          withdrawDay: Number(withdrawDay) || 1,
          withdrawName: withdrawName.trim() || null,
          billingSameAsRental: billingSameAsRental ? 1 : 0,
          billingAddress: billingSameAsRental ? null : billingAddress.trim() || null,
          billingZipCode: billingSameAsRental
            ? null
            : billingZipCode
              ? Number(billingZipCode)
              : null,
          billingCity: billingSameAsRental ? null : billingCity.trim() || null,
          billingPhone: billingSameAsRental ? null : billingPhone.trim() || null,
          sendNoticeOfLeaseRental: sendNotice ? 1 : 0,
          sendLeaseRental: sendReceipt ? 1 : 0,
        },
      });

      const rentUpdates: Array<{ type: Rent["type"]; raw: string }> = [
        { type: "Loyer", raw: loyerPrice },
        { type: "Charges", raw: chargesPrice },
        { type: "Garantie", raw: garantiePrice },
      ];
      for (const { type, raw } of rentUpdates) {
        if (raw === "") continue;
        const newPrice = Number(raw);
        if (Number.isNaN(newPrice)) continue;
        const existing = (tenantRents ?? []).find((r) => r.type === type && r.active);
        if (existing) {
          if (Number(existing.price ?? 0) !== newPrice) {
            await updateRentMut.mutateAsync({ id: existing.id, input: { price: newPrice } });
          }
        } else {
          await createRentMut.mutateAsync({ tenantId: tenant.id, type, price: newPrice, active: 1 });
        }
      }

      toast.success("Locataire modifié");
      setEditing(false);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleToggleActive() {
    if (!tenant) return;
    const newActive = tenant.active ? 0 : 1;
    try {
      await updateMut.mutateAsync({ id: tenant.id, input: { active: newActive } });
      toast.success(newActive ? "Locataire réactivé" : "Locataire archivé");
      if (!newActive) void navigate({ to: "/tenants" });
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  }

  // ---------------------------------------------------------------------------
  // Loading / not found
  // ---------------------------------------------------------------------------

  if (isLoading) {
    return <div className="py-12 text-center text-muted-foreground">Chargement…</div>;
  }
  if (!tenant) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" asChild>
          <Link to="/tenants">
            <ArrowLeft className="mr-1 h-4 w-4" /> Locataires
          </Link>
        </Button>
        <p className="text-center text-muted-foreground">Locataire introuvable.</p>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Computed display values
  // ---------------------------------------------------------------------------

  const fullName = [tenant.firstName, tenant.name].filter(Boolean).join(" ") || "—";
  const loyerRent = tenantRents?.find((r) => r.type === "Loyer" && r.active);
  const chargesRent = tenantRents?.find((r) => r.type === "Charges" && r.active);
  const garantieRent = tenantRents?.find((r) => r.type === "Garantie" && r.active);
  const garantiePaid = tenant.warantyReceiptId !== null;

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <Button variant="ghost" size="icon" asChild className="mt-0.5 shrink-0">
            <Link to="/tenants">
              <ArrowLeft className="h-4 w-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-xl font-semibold">{fullName}</h1>
            <p className="text-sm text-muted-foreground">
              <span
                className={
                  tenant.active
                    ? "font-medium text-green-600"
                    : "font-medium text-muted-foreground"
                }
              >
                {tenant.active ? "Actif" : "Inactif"}
              </span>
              {tenant.placeUnitId !== null && (
                <> · {unitLabel(tenant.placeUnitId)}</>
              )}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          {editing ? (
            <Fragment key="edit-actions">
              <Button type="button" variant="outline" onClick={cancelEdit} disabled={submitting}>
                <X className="mr-1 h-4 w-4" /> Annuler
              </Button>
              <Button type="button" onClick={() => void handleSave()} disabled={submitting}>
                <Save className="mr-1 h-4 w-4" /> {submitting ? "…" : "Enregistrer"}
              </Button>
            </Fragment>
          ) : (
            <Fragment key="view-actions">
              <Button
                type="button"
                variant="outline"
                onClick={() => void handleToggleActive()}
                className={tenant.active ? "text-destructive hover:text-destructive" : ""}
              >
                {tenant.active ? (
                  <><UserMinus className="mr-1 h-4 w-4" /> Archiver</>
                ) : (
                  <><RotateCcw className="mr-1 h-4 w-4" /> Réactiver</>
                )}
              </Button>
              <Button type="button" onClick={() => setEditing(true)}>
                <Pencil className="mr-1 h-4 w-4" /> Modifier
              </Button>
            </Fragment>
          )}
        </div>
      </div>

      {/* ── Identité ── */}
      <section className="space-y-4 rounded-md border p-4">
        <h3 className="text-sm font-semibold">Identité</h3>
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Civilité">
            {editing ? (
              <select
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
            ) : (
              <span>{GENRE_LABEL[tenant.genre ?? ""] ?? "—"}</span>
            )}
          </Field>

          <Field label="Prénom">
            {editing ? (
              <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            ) : (
              <span>{tenant.firstName ?? "—"}</span>
            )}
          </Field>

          <Field label="Nom">
            {editing ? (
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            ) : (
              <span>{tenant.name ?? "—"}</span>
            )}
          </Field>

          <Field label="Email">
            {editing ? (
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            ) : (
              <span>{tenant.email ?? "—"}</span>
            )}
          </Field>

          <Field label="Téléphone">
            {editing ? (
              <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
            ) : (
              <span>{tenant.phone ?? "—"}</span>
            )}
          </Field>
        </div>

        {/* Billing address — always shown */}
        <div className="border-t pt-4">
          <p className="mb-3 text-xs font-medium text-muted-foreground">Adresse de facturation</p>
          {editing ? (
            <div className="space-y-3">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-input"
                  checked={billingSameAsRental}
                  onChange={(e) => setBillingSameAsRental(e.target.checked)}
                />
                <span>Même adresse que la location</span>
              </label>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="billingAddress">Adresse</Label>
                  <Input
                    id="billingAddress"
                    disabled={billingSameAsRental}
                    value={billingSameAsRental ? (rentalPlaceForEdit?.address ?? "") : billingAddress}
                    onChange={(e) => setBillingAddress(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="billingZip">Code postal</Label>
                  <Input
                    id="billingZip"
                    type="text"
                    inputMode="numeric"
                    disabled={billingSameAsRental}
                    value={billingSameAsRental ? (rentalPlaceForEdit?.zipCode != null ? String(rentalPlaceForEdit.zipCode) : "") : billingZipCode}
                    onChange={(e) => setBillingZipCode(e.target.value.replace(/\D/g, ""))}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="billingCity">Ville</Label>
                  <Input
                    id="billingCity"
                    disabled={billingSameAsRental}
                    value={billingSameAsRental ? (rentalPlaceForEdit?.city ?? "") : billingCity}
                    onChange={(e) => setBillingCity(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="billingPhone">Téléphone</Label>
                  <Input
                    id="billingPhone"
                    disabled={billingSameAsRental}
                    value={billingSameAsRental ? phone : billingPhone}
                    onChange={(e) => setBillingPhone(e.target.value)}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Adresse">
                <span>
                  {tenant.billingSameAsRental
                    ? (tenantPlace?.address ?? "—")
                    : (tenant.billingAddress ?? "—")}
                </span>
              </Field>
              <Field label="Code postal / Ville">
                <span>
                  {tenant.billingSameAsRental
                    ? ([tenantPlace?.zipCode, tenantPlace?.city].filter(Boolean).join(" ") || "—")
                    : ([tenant.billingZipCode, tenant.billingCity].filter(Boolean).join(" ") || "—")}
                </span>
              </Field>
              <Field label="Téléphone">
                <span>
                  {tenant.billingSameAsRental
                    ? (tenant.phone ?? "—")
                    : (tenant.billingPhone ?? "—")}
                </span>
              </Field>
            </div>
          )}
        </div>
      </section>

      {/* ── Logement ── */}
      <section className="space-y-4 rounded-md border p-4">
        <h3 className="text-sm font-semibold">Logement</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <Field label="Bien">
              {editing ? (
                <select
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
              ) : (
                <span>
                  {tenant.placeUnitId !== null ? unitLabel(tenant.placeUnitId) : "—"}
                </span>
              )}
            </Field>
          </div>

          {(isFlatshare || tenant.placeUnitRoomId !== null) && (
            <div className="sm:col-span-2">
              <Field label="Chambre">
                {editing && isFlatshare ? (
                  <select
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
                ) : (
                  <span>
                    {tenant.placeUnitRoomId !== null
                      ? (rooms?.find((r) => r.id === tenant.placeUnitRoomId)?.name ??
                        `#${tenant.placeUnitRoomId}`)
                      : "—"}
                  </span>
                )}
              </Field>
            </div>
          )}

          <Field label="Date d'entrée">
            {editing ? (
              <Input
                type="date"
                value={dateEntrance}
                onChange={(e) => setDateEntrance(e.target.value)}
              />
            ) : (
              <span>{formatDate(tenant.dateEntrance) || "—"}</span>
            )}
          </Field>

          <Field label="Date de sortie">
            {editing ? (
              <Input
                type="date"
                value={dateExit}
                onChange={(e) => setDateExit(e.target.value)}
              />
            ) : (
              <span>{formatDate(tenant.dateExit) || "—"}</span>
            )}
          </Field>
        </div>
      </section>

      {/* ── Paiement ── */}
      <section className="space-y-4 rounded-md border p-4">
        <h3 className="text-sm font-semibold">Paiement</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Jour de prélèvement">
            {editing ? (
              <Input
                type="number"
                min={1}
                max={31}
                value={withdrawDay}
                onChange={(e) => setWithdrawDay(e.target.value)}
              />
            ) : (
              <span>{tenant.withdrawDay ?? "—"}</span>
            )}
          </Field>

          <Field label="Nom du virement">
            {editing ? (
              <Input
                value={withdrawName}
                onChange={(e) => setWithdrawName(e.target.value)}
                placeholder="Nom tel qu'il apparaît sur le relevé bancaire"
              />
            ) : (
              <span>{tenant.withdrawName ?? "—"}</span>
            )}
          </Field>

          <div className="sm:col-span-2 space-y-2">
            <p className="text-xs font-medium text-muted-foreground">Notifications par email</p>
            {editing ? (
              <div className="space-y-1.5">
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
              </div>
            ) : (
              <div className="text-sm space-y-0.5">
                <p>{tenant.sendNoticeOfLeaseRental ? "✓ Avis d'échéance" : "✗ Avis d'échéance"}</p>
                <p>{tenant.sendLeaseRental ? "✓ Quittance de loyer" : "✗ Quittance de loyer"}</p>
              </div>
            )}
          </div>
        </div>

      </section>

      {/* ── Loyers ── */}
      <section className="space-y-4 rounded-md border p-4">
        <h3 className="text-sm font-semibold">Loyers</h3>
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Loyer mensuel">
            {editing ? (
              <Input
                type="number"
                step="0.01"
                value={loyerPrice}
                onChange={(e) => setLoyerPrice(e.target.value)}
              />
            ) : (
              <span>{formatCurrency(loyerRent?.price ?? null)}</span>
            )}
          </Field>

          <Field label="Charges mensuelles">
            {editing ? (
              <Input
                type="number"
                step="0.01"
                value={chargesPrice}
                onChange={(e) => setChargesPrice(e.target.value)}
              />
            ) : (
              <span>{formatCurrency(chargesRent?.price ?? null)}</span>
            )}
          </Field>

          <Field label="Caution">
            {editing ? (
              <Input
                type="number"
                step="0.01"
                value={garantiePrice}
                onChange={(e) => setGarantiePrice(e.target.value)}
              />
            ) : (
              <span className="flex items-center gap-2">
                {formatCurrency(garantieRent?.price ?? null)}
                {garantieRent && (
                  garantiePaid ? (
                    <span className="inline-flex items-center gap-1 text-xs font-medium text-green-600">
                      <CheckCircle2 className="h-3.5 w-3.5" /> Payée
                    </span>
                  ) : (
                    <span className="text-xs text-muted-foreground">Non payée</span>
                  )
                )}
              </span>
            )}
          </Field>
        </div>
        {editing && (
          <p className="text-xs text-muted-foreground">
            Modifier ces montants n'affecte que les futures quittances.
          </p>
        )}
      </section>
    </div>
  );
}

export const Route = createFileRoute("/_authenticated/tenants/$tenantId")({
  component: TenantDetailPage,
});
