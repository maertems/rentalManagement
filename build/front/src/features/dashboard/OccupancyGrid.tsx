import { CheckCircle2, XCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatCurrency } from "@/lib/formatters";
import type {
  OccupancyPlace,
  OccupancyResponse,
  OccupancyTenant,
} from "@/api/types";

interface Props {
  data: OccupancyResponse | undefined;
  isLoading: boolean;
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

function TenantRow({ t }: { t: OccupancyTenant }) {
  const fullName = [t.firstName, t.name].filter(Boolean).join(" ") || "(sans nom)";
  return (
    <div className="flex items-center justify-between border-t px-3 py-1.5 text-sm first:border-t-0">
      <span className="truncate">{fullName}</span>
      <span className="flex items-center gap-2">
        <AmountBadge t={t} />
        {t.rentPaid ? (
          <CheckCircle2 className="h-4 w-4 text-green-600" />
        ) : (
          <XCircle className="h-4 w-4 text-red-600" />
        )}
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

function PlaceCard({ place }: { place: OccupancyPlace }) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="bg-muted/40 py-3">
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
        {place.units.map((unit) => (
          <div key={unit.unitId} className="min-w-[220px] flex-1 rounded-md border">
            <div className="flex items-center justify-between bg-muted/20 px-3 py-1.5 text-sm font-medium">
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
                            {t.rentPaid ? (
                              <CheckCircle2 className="h-4 w-4 text-green-600" />
                            ) : (
                              <XCircle className="h-4 w-4 text-red-600" />
                            )}
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
              unit.tenants.map((t) => <TenantRow key={t.tenantId} t={t} />)
            )}
          </div>
        ))}
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
  return (
    <div className="flex flex-col gap-4">
      {data.places.map((p) => (
        <PlaceCard key={p.placeId} place={p} />
      ))}
    </div>
  );
}
