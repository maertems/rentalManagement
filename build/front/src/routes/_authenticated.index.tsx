import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight } from "lucide-react";

import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { StatCards } from "@/features/dashboard/StatCards";
import { OccupancyGrid } from "@/features/dashboard/OccupancyGrid";
import { useOccupancy } from "@/hooks/useOccupancy";
import { formatMonth, monthKey } from "@/lib/formatters";

function DashboardPage() {
  const [cursor, setCursor] = useState<Date>(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });

  const month = monthKey(cursor);
  const { data, isLoading } = useOccupancy(month);

  function shift(deltaMonths: number) {
    setCursor(
      (prev) => new Date(prev.getFullYear(), prev.getMonth() + deltaMonths, 1),
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tableau de bord"
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={() => shift(-1)}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="min-w-[150px] text-center text-sm font-medium">
              {formatMonth(cursor.getFullYear(), cursor.getMonth() + 1)}
            </div>
            <Button variant="outline" size="icon" onClick={() => shift(1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        }
      />

      <StatCards data={data} />

      <OccupancyGrid data={data} isLoading={isLoading} />
    </div>
  );
}

export const Route = createFileRoute("/_authenticated/")({
  component: DashboardPage,
});
