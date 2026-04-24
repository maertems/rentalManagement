import { Users, CheckCircle2, XCircle, Building } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { OccupancyResponse } from "@/api/types";

interface Props {
  data: OccupancyResponse | undefined;
}

export function StatCards({ data }: Props) {
  let totalTenants = 0;
  let paid = 0;
  let unpaid = 0;
  let totalSlots = 0; // units (non-coloc) + rooms (coloc)
  let occupiedSlots = 0;

  if (data?.places) {
    for (const place of data.places) {
      for (const unit of place.units) {
        if (unit.flatshare) {
          for (const room of unit.rooms) {
            totalSlots += 1;
            if (room.tenants.length > 0) occupiedSlots += 1;
            for (const t of room.tenants) {
              totalTenants += 1;
              if (t.rentPaid) paid += 1;
              else unpaid += 1;
            }
          }
        } else {
          totalSlots += 1;
          if (unit.tenants.length > 0) occupiedSlots += 1;
          for (const t of unit.tenants) {
            totalTenants += 1;
            if (t.rentPaid) paid += 1;
            else unpaid += 1;
          }
        }
      }
    }
  }

  const occupancy =
    totalSlots > 0 ? Math.round((occupiedSlots / totalSlots) * 100) : 0;

  const cards = [
    {
      label: "Locataires actifs",
      value: totalTenants,
      icon: Users,
      tone: "text-foreground",
    },
    {
      label: "Loyer payé ce mois",
      value: paid,
      icon: CheckCircle2,
      tone: "text-green-600",
    },
    {
      label: "Loyer impayé",
      value: unpaid,
      icon: XCircle,
      tone: unpaid > 0 ? "text-red-600" : "text-muted-foreground",
    },
    {
      label: "Taux d'occupation",
      value: `${occupancy}%`,
      icon: Building,
      tone: "text-foreground",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {cards.map(({ label, value, icon: Icon, tone }) => (
        <Card key={label}>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <div className="text-xs uppercase text-muted-foreground">{label}</div>
              <div className={`mt-1 text-2xl font-semibold ${tone}`}>{value}</div>
            </div>
            <Icon className={`h-8 w-8 opacity-30`} />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
