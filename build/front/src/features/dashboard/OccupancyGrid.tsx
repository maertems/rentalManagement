import { CheckCircle2, XCircle, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/formatters";
import type {
  OccupancyPlace,
  OccupancyResponse,
  OccupancyTenant,
  OccupancyUnit,
} from "@/api/types";

interface Props {
  data: OccupancyResponse | undefined;
  isLoading: boolean;
}

function isGracePeriodFor(month: string): boolean {
  const today = new Date();
  const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
  return month === currentMonth && today.getDate() <= 6;
}

function unitAllPaid(unit: OccupancyUnit): boolean {
  if (unit.flatshare) {
    const tenants = unit.rooms.flatMap((r) => r.tenants);
    return tenants.length > 0 && tenants.every((t) => t.rentPaid);
  }
  return unit.tenants.length > 0 && unit.tenants.every((t) => t.rentPaid);
}

function placeAllPaid(place: OccupancyPlace): boolean {
  const occupiedUnits = place.units.filter((u) =>
    u.flatshare ? u.rooms.flatMap((r) => r.tenants).length > 0 : u.tenants.length > 0,
  );
  return occupiedUnits.length > 0 && occupiedUnits.every(unitAllPaid);
}

function PaymentIcon({ paid, gracePeriod }: { paid: boolean; gracePeriod: boolean }) {
  if (paid) return <CheckCircle2 className="h-4 w-4 text-green-600" />;
  if (gracePeriod) return <Clock className="h-4 w-4 text-muted-foreground/40" title="Dans le délai de paiement" />;
  return <XCircle className="h-4 w-4 text-red-600" />;
}

function AmountBadge({ t }: { t: OccupancyTenant }) {
  if (t.rentAmountEstimated) {
    return (
      <span className="italic text-muted-foreground/50" title="Estimation (pas de quittance ce mois)">
        {formatCurrency(t.rentAmount)}
      </span>
    );
  }
  return <span className="text-muted-foreground">{formatCurrency(t.rentAmount)}</span>;
}

function TenantRow({ t, gracePeriod }: { t: OccupancyTenant; gracePeriod: boolean }) {
  const fullName = [t.firstName, t.name].filter(Boolean).join(" ") || "(sans nom)";
  return (
    <div className="flex items-center justify-between border-t px-3 py-1.5 text-sm first:border-t-0">
      <span className="truncate">{fullName}</span>
      <span className="flex items-center gap-2">
        <AmountBadge t={t} />
        <PaymentIcon paid={t.rentPaid} gracePeriod={gracePeriod} />
      </span>
    </div>
  );
}

function VacantRow({ label }: { label: string }) {
  return (
    <div className="border-t px-3 py-1.5 text-sm italic text-muted-foreground first:border-t-0">
      {label} — vacant
    </div>
  );
}

function PlaceCard({ place, gracePeriod }: { place: OccupancyPlace; gracePeriod: boolean }) {
  const allPaid = placeAllPaid(place);
  return (
    <Card className="overflow-hidden">
      <CardHeader className={allPaid ? "bg-green-50 py-3" : "bg-muted/40 py-3"}>
        <CardTitle className="text-base">{place.placeName ?? "Sans nom"}</CardTitle>
        {place.ownerName && (
          <p className="text-xs text-muted-foreground">
            Propriétaire : {place.ownerName}
          </p>
        )}
      </CardHeader>
      <CardContent className="p-3">
        {place.units.length === 0 && (
          <p className="py-2 text-center text-sm italic text-muted-foreground">
            Aucun logement
          </p>
        )}
        <div className="flex flex-wrap gap-3">
          {place.units.map((unit) => {
            const paid = unitAllPaid(unit);
            return (
              <div
                key={unit.unitId}
                className={`min-w-[220px] flex-1 rounded-md border${paid ? " bg-green-50" : ""}`}
              >
                <div className={`flex items-center justify-between px-3 py-1.5 text-sm font-medium${paid ? "" : " bg-muted/20"}`}>
                  <span>
                    {unit.friendlyName || unit.unitName || `Logement #${unit.unitId}`}
                    {unit.level && (
                      <span className="ml-2 text-xs text-muted-foreground">
                        niveau {unit.level}
                      </span>
                    )}
                  </span>
                  {unit.flatshare && (
                    <span className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-900">
                      Coloc
                    </span>
                  )}
                </div>
                {unit.flatshare ? (
                  unit.rooms.length === 0 ? (
                    <VacantRow label="Aucune chambre" />
                  ) : (
                    unit.rooms.map((r) =>
                      r.tenants.length > 0 ? (
                        <div key={r.roomId}>
                          {r.tenants.map((t) => (
                            <div
                              key={t.tenantId}
                              className="flex items-center justify-between border-t px-3 py-1.5 text-sm first:border-t-0"
                            >
                              <span className="truncate">
                                <span className="text-muted-foreground">
                                  {r.roomName ?? `Chambre #${r.roomId}`} —
                                </span>{" "}
                                {[t.firstName, t.name].filter(Boolean).join(" ") ||
                                  "(sans nom)"}
                              </span>
                              <span className="flex items-center gap-2">
                                <AmountBadge t={t} />
                                <PaymentIcon paid={t.rentPaid} gracePeriod={gracePeriod} />
                              </span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <VacantRow
                          key={r.roomId}
                          label={r.roomName ?? `Chambre #${r.roomId}`}
                        />
                      ),
                    )
                  )
                ) : unit.tenants.length === 0 ? (
                  <VacantRow label="Logement" />
                ) : (
                  unit.tenants.map((t) => (
                    <TenantRow key={t.tenantId} t={t} gracePeriod={gracePeriod} />
                  ))
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

export function OccupancyGrid({ data, isLoading }: Props) {
  if (isLoading) {
    return (
      <div className="py-12 text-center text-muted-foreground">Chargement…</div>
    );
  }
  if (!data || !data.places || data.places.length === 0) {
    return (
      <div className="rounded-lg border bg-muted/20 py-12 text-center text-muted-foreground">
        Aucun bien enregistré.
      </div>
    );
  }
  const gracePeriod = isGracePeriodFor(data.month);
  return (
    <div className="flex flex-col gap-4">
      {data.places.map((p) => (
        <PlaceCard key={p.placeId} place={p} gracePeriod={gracePeriod} />
      ))}
    </div>
  );
}
