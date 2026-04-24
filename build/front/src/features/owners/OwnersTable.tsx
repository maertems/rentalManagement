import { Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Owner } from "@/api/types";

interface Props {
  rows: Owner[];
  isLoading: boolean;
  onEdit: (owner: Owner) => void;
  onDelete: (owner: Owner) => void;
}

export function OwnersTable({ rows, isLoading, onEdit, onDelete }: Props) {
  if (isLoading) {
    return <div className="py-12 text-center text-muted-foreground">Chargement…</div>;
  }
  if (!rows || rows.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        Aucun propriétaire pour le moment.
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-lg border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left">
          <tr>
            <th className="px-4 py-2 font-medium">Nom</th>
            <th className="px-4 py-2 font-medium">Email</th>
            <th className="px-4 py-2 font-medium">Téléphone</th>
            <th className="px-4 py-2 font-medium">Ville</th>
            <th className="px-4 py-2 font-medium">CP</th>
            <th className="w-[120px] px-4 py-2"></th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {rows.map((o) => (
            <tr key={o.id} className="hover:bg-muted/30">
              <td className="px-4 py-2 font-medium">{o.name ?? "—"}</td>
              <td className="px-4 py-2 text-muted-foreground">{o.email ?? "—"}</td>
              <td className="px-4 py-2 text-muted-foreground">{o.phoneNumber ?? "—"}</td>
              <td className="px-4 py-2 text-muted-foreground">{o.city ?? "—"}</td>
              <td className="px-4 py-2 text-muted-foreground">{o.zipCode ?? "—"}</td>
              <td className="px-4 py-2">
                <div className="flex justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onEdit(o)}
                    title="Modifier"
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDelete(o)}
                    title="Supprimer"
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
