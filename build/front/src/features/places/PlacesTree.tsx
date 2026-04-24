import { Pencil, Plus, Trash2, Building, Home, DoorOpen } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { Owner, Place, PlacesUnit, PlacesUnitsRoom } from "@/api/types";

interface Props {
  places: Place[];
  units: PlacesUnit[];
  rooms: PlacesUnitsRoom[];
  owners: Owner[];
  isLoading: boolean;
  onEditPlace: (place: Place) => void;
  onDeletePlace: (place: Place) => void;
  onAddUnit: (place: Place) => void;
  onEditUnit: (unit: PlacesUnit) => void;
  onDeleteUnit: (unit: PlacesUnit) => void;
  onAddRoom: (unit: PlacesUnit) => void;
  onEditRoom: (room: PlacesUnitsRoom) => void;
  onDeleteRoom: (room: PlacesUnitsRoom) => void;
}

export function PlacesTree({
  places,
  units,
  rooms,
  owners,
  isLoading,
  onEditPlace,
  onDeletePlace,
  onAddUnit,
  onEditUnit,
  onDeleteUnit,
  onAddRoom,
  onEditRoom,
  onDeleteRoom,
}: Props) {
  if (isLoading) {
    return <div className="py-12 text-center text-muted-foreground">Chargement…</div>;
  }
  if (!places || places.length === 0) {
    return (
      <div className="rounded-lg border bg-muted/20 py-12 text-center text-muted-foreground">
        Aucun bien enregistré.
      </div>
    );
  }

  const ownerById = new Map((owners ?? []).map((o) => [o.id, o]));
  const unitsByPlaceId = new Map<number, PlacesUnit[]>();
  for (const u of (units ?? [])) {
    if (u.placeId !== null) {
      const list = unitsByPlaceId.get(u.placeId) ?? [];
      list.push(u);
      unitsByPlaceId.set(u.placeId, list);
    }
  }
  const roomsByUnitId = new Map<number, PlacesUnitsRoom[]>();
  for (const r of (rooms ?? [])) {
    if (r.placesUnitsId !== null) {
      const list = roomsByUnitId.get(r.placesUnitsId) ?? [];
      list.push(r);
      roomsByUnitId.set(r.placesUnitsId, list);
    }
  }

  return (
    <div className="space-y-4">
      {places.map((p) => {
        const owner = p.ownerId !== null ? ownerById.get(p.ownerId) : undefined;
        const placeUnits = unitsByPlaceId.get(p.id) ?? [];
        return (
          <Card key={p.id}>
            <CardHeader className="flex flex-row items-start justify-between space-y-0 bg-muted/30 py-3">
              <div className="flex items-start gap-2">
                <Building className="mt-0.5 h-5 w-5 text-muted-foreground" />
                <div>
                  <CardTitle className="text-base">{p.name ?? "Sans nom"}</CardTitle>
                  <p className="text-xs text-muted-foreground">
                    {[p.address, p.city, p.zipCode].filter(Boolean).join(", ") ||
                      "Pas d'adresse"}
                    {owner && (
                      <span className="ml-2">
                        · Propriétaire :{" "}
                        <strong>{owner.name ?? `#${owner.id}`}</strong>
                      </span>
                    )}
                  </p>
                </div>
              </div>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onEditPlace(p)}
                  title="Modifier le bien"
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => onDeletePlace(p)}
                  title="Supprimer le bien"
                >
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-2 p-3">
              {placeUnits.length === 0 && (
                <p className="py-2 text-center text-sm italic text-muted-foreground">
                  Aucun logement
                </p>
              )}
              {placeUnits.map((u) => {
                const isFlatshare = !!u.flatshare;
                const unitRooms = roomsByUnitId.get(u.id) ?? [];
                return (
                  <div key={u.id} className="rounded-md border">
                    <div className="flex items-center justify-between bg-muted/10 px-3 py-2">
                      <div className="flex items-center gap-2">
                        <Home className="h-4 w-4 text-muted-foreground" />
                        <div className="text-sm">
                          <span className="font-medium">
                            {u.friendlyName || u.name || `Logement #${u.id}`}
                          </span>
                          <span className="ml-2 text-xs text-muted-foreground">
                            {u.level && `niveau ${u.level}`}
                            {u.surfaceArea !== null && <> · {u.surfaceArea} m²</>}
                          </span>
                          {isFlatshare && (
                            <span className="ml-2 rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-900">
                              Coloc
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-1">
                        {isFlatshare && (
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onAddRoom(u)}
                            title="Ajouter une chambre"
                          >
                            <Plus className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => onEditUnit(u)}
                          title="Modifier ce logement"
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => onDeleteUnit(u)}
                          title="Supprimer ce logement"
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                    {isFlatshare && unitRooms.length > 0 && (
                      <div className="divide-y border-t bg-muted/5">
                        {unitRooms.map((r) => (
                          <div
                            key={r.id}
                            className="flex items-center justify-between py-1.5 pl-8 pr-3"
                          >
                            <div className="flex items-center gap-2 text-sm">
                              <DoorOpen className="h-4 w-4 text-muted-foreground" />
                              <span>{r.name ?? `Chambre #${r.id}`}</span>
                              {r.surfaceArea !== null && (
                                <span className="text-xs text-muted-foreground">
                                  {r.surfaceArea} m²
                                </span>
                              )}
                            </div>
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => onEditRoom(r)}
                                title="Modifier cette chambre"
                              >
                                <Pencil className="h-4 w-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => onDeleteRoom(r)}
                                title="Supprimer cette chambre"
                              >
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
              <div className="flex justify-end pt-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onAddUnit(p)}
                >
                  <Plus className="mr-1 h-4 w-4" /> Ajouter un logement
                </Button>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
