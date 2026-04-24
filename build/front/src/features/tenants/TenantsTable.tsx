import { Eye } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { formatCurrency } from "@/lib/formatters";
import type {
  Place,
  PlacesUnit,
  PlacesUnitsRoom,
  Rent,
  RentReceipt,
  Tenant,
} from "@/api/types";

interface Props {
  rows: Tenant[];
  isLoading: boolean;
  places: Place[];
  units: PlacesUnit[];
  rooms: PlacesUnitsRoom[];
  rents: Rent[];
  receipts: RentReceipt[];
  variant: "active" | "inactive";
  onShowReceipts?: (t: Tenant) => void;
}

export function TenantsTable({
  rows,
  isLoading,
  places,
  units,
  rooms,
  rents,
  receipts,
  variant,
  onShowReceipts,
}: Props) {
  const navigate = useNavigate();

  if (isLoading) {
    return <div className="py-8 text-center text-muted-foreground">Chargement…</div>;
  }
  if (!rows || rows.length === 0) {
    return (
      <div className="py-8 text-center text-sm italic text-muted-foreground">
        Aucun locataire {variant === "active" ? "actif" : "inactif"}.
      </div>
    );
  }

  const placesById = new Map((places ?? []).map((p) => [p.id, p]));
  const unitsById = new Map((units ?? []).map((u) => [u.id, u]));
  const roomsById = new Map((rooms ?? []).map((r) => [r.id, r]));
  const receiptsById = new Map((receipts ?? []).map((r) => [r.id, r]));

  const loyerByTenant = new Map<number, number>();
  for (const r of (rents ?? [])) {
    if (r.type === "Loyer" && r.active && r.tenantId !== null && r.price !== null) {
      loyerByTenant.set(r.tenantId, Number(r.price));
    }
  }

  function unitLabel(t: Tenant): string {
    if (t.placeUnitId === null) return "—";
    const u = unitsById.get(t.placeUnitId);
    if (!u) return `#${t.placeUnitId}`;
    const place = u.placeId !== null ? placesById.get(u.placeId) : null;
    const placeName = place?.name ?? "?";
    const unitName = u.friendlyName || u.name || `#${u.id}`;
    let label = `${placeName} — ${unitName}`;
    if (t.placeUnitRoomId !== null) {
      const r = roomsById.get(t.placeUnitRoomId);
      label += ` — ${r?.name ?? `#${t.placeUnitRoomId}`}`;
    }
    return label;
  }

  function caution(t: Tenant): number | null {
    if (t.warantyReceiptId === null) return null;
    return receiptsById.get(t.warantyReceiptId)?.amount ?? null;
  }

  return (
    <div className="overflow-hidden rounded-md border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left">
          <tr>
            <th className="px-3 py-2 font-medium">Nom</th>
            <th className="px-3 py-2 font-medium">Téléphone</th>
            <th className="px-3 py-2 font-medium">Email</th>
            <th className="px-3 py-2 font-medium">Logement</th>
            <th className="px-3 py-2 font-medium text-right">Loyer</th>
            <th className="px-3 py-2 font-medium text-right">Caution</th>
            <th className="w-[52px] px-3 py-2"></th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((t) => {
            const fullName = [t.firstName, t.name].filter(Boolean).join(" ") || "—";
            return (
              <tr
                key={t.id}
                className="cursor-pointer hover:bg-muted/30"
                onClick={() =>
                  void navigate({
                    to: "/tenants/$tenantId",
                    params: { tenantId: String(t.id) },
                  })
                }
              >
                <td className="px-3 py-2 font-medium">{fullName}</td>
                <td className="px-3 py-2 text-muted-foreground">{t.phone ?? "—"}</td>
                <td className="px-3 py-2 text-muted-foreground">{t.email ?? "—"}</td>
                <td className="px-3 py-2 text-muted-foreground">{unitLabel(t)}</td>
                <td className="px-3 py-2 text-right">
                  {formatCurrency(loyerByTenant.get(t.id) ?? null)}
                </td>
                <td className="px-3 py-2 text-right">{formatCurrency(caution(t))}</td>
                <td className="px-3 py-2">
                  {onShowReceipts && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        onShowReceipts(t);
                      }}
                      title="Voir les quittances"
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
