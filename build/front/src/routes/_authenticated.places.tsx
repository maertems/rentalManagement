import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Plus, Search } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/common/PageHeader";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PlacesTree } from "@/features/places/PlacesTree";
import { PlaceFullFormDialog } from "@/features/places/PlaceFullFormDialog";
import { PlaceEditDialog } from "@/features/places/PlaceEditDialog";
import { UnitFormDialog } from "@/features/places/UnitFormDialog";
import { RoomFormDialog } from "@/features/places/RoomFormDialog";
import {
  useAllPlacesUnits,
  useAllRooms,
  useDeletePlace,
  useDeletePlacesUnit,
  useDeleteRoom,
  usePlacesList,
} from "@/hooks/usePlaces";
import { useOwnersList } from "@/hooks/useOwners";
import { getApiErrorMessage } from "@/lib/apiError";
import type { Place, PlacesUnit, PlacesUnitsRoom } from "@/api/types";

type DeleteTarget =
  | { kind: "place"; place: Place }
  | { kind: "unit"; unit: PlacesUnit }
  | { kind: "room"; room: PlacesUnitsRoom }
  | null;

function PlacesPage() {
  const [search, setSearch] = useState("");
  // Create-everything dialog (place + units + rooms in one shot)
  const [createOpen, setCreateOpen] = useState(false);
  // Place edit dialog
  const [editingPlace, setEditingPlace] = useState<Place | null>(null);
  // Unit dialog (create OR edit)
  const [unitDialogPlaceId, setUnitDialogPlaceId] = useState<number | null>(null);
  const [editingUnit, setEditingUnit] = useState<PlacesUnit | null>(null);
  const [unitDialogOpen, setUnitDialogOpen] = useState(false);
  // Room dialog (create OR edit)
  const [roomDialogUnitId, setRoomDialogUnitId] = useState<number | null>(null);
  const [editingRoom, setEditingRoom] = useState<PlacesUnitsRoom | null>(null);
  const [roomDialogOpen, setRoomDialogOpen] = useState(false);
  // Delete confirm
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [target, setTarget] = useState<DeleteTarget>(null);

  const { data: places, isLoading: loadingPlaces } = usePlacesList();
  const { data: units, isLoading: loadingUnits } = useAllPlacesUnits();
  const { data: rooms, isLoading: loadingRooms } = useAllRooms();
  const { data: ownersData } = useOwnersList();

  const deletePlaceMut = useDeletePlace();
  const deleteUnitMut = useDeletePlacesUnit();
  const deleteRoomMut = useDeleteRoom();

  const isLoading = loadingPlaces || loadingUnits || loadingRooms;

  const filteredPlaces = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q || !places) return places ?? [];
    return places.filter(
      (p) =>
        (p.name && p.name.toLowerCase().includes(q)) ||
        (p.city && p.city.toLowerCase().includes(q)) ||
        (p.address && p.address.toLowerCase().includes(q)),
    );
  }, [places, search]);

  function openAddUnit(p: Place) {
    setEditingUnit(null);
    setUnitDialogPlaceId(p.id);
    setUnitDialogOpen(true);
  }
  function openEditUnit(u: PlacesUnit) {
    setEditingUnit(u);
    setUnitDialogPlaceId(null);
    setUnitDialogOpen(true);
  }
  function openAddRoom(u: PlacesUnit) {
    setEditingRoom(null);
    setRoomDialogUnitId(u.id);
    setRoomDialogOpen(true);
  }
  function openEditRoom(r: PlacesUnitsRoom) {
    setEditingRoom(r);
    setRoomDialogUnitId(null);
    setRoomDialogOpen(true);
  }

  function askDelete(t: DeleteTarget) {
    setTarget(t);
    setConfirmOpen(true);
  }

  async function confirmDelete() {
    if (!target) return;
    try {
      if (target.kind === "place") {
        await deletePlaceMut.mutateAsync(target.place.id);
        toast.success("Bien supprimé");
      } else if (target.kind === "unit") {
        await deleteUnitMut.mutateAsync(target.unit.id);
        toast.success("Logement supprimé");
      } else {
        await deleteRoomMut.mutateAsync(target.room.id);
        toast.success("Chambre supprimée");
      }
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  }

  const desc = (() => {
    if (!target) return "";
    if (target.kind === "place")
      return `Le bien « ${target.place.name ?? "sans nom"} » sera supprimé. Si des logements y sont rattachés, la suppression sera refusée.`;
    if (target.kind === "unit")
      return `Le logement « ${target.unit.friendlyName || target.unit.name || `#${target.unit.id}`} » sera supprimé. S'il a des chambres ou des locataires, la suppression sera refusée.`;
    return `La chambre « ${target.room.name ?? `#${target.room.id}`} » sera supprimée. Si elle est occupée, la suppression sera refusée.`;
  })();

  return (
    <div className="space-y-4">
      <PageHeader
        title="Biens"
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-1 h-4 w-4" /> Nouveau
          </Button>
        }
      />

      <div className="relative max-w-sm">
        <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Rechercher par nom, ville, adresse…"
          className="pl-8"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <PlacesTree
        places={filteredPlaces}
        units={units ?? []}
        rooms={rooms ?? []}
        owners={ownersData?.rows ?? []}
        isLoading={isLoading}
        onEditPlace={(p) => setEditingPlace(p)}
        onDeletePlace={(p) => askDelete({ kind: "place", place: p })}
        onAddUnit={openAddUnit}
        onEditUnit={openEditUnit}
        onDeleteUnit={(u) => askDelete({ kind: "unit", unit: u })}
        onAddRoom={openAddRoom}
        onEditRoom={openEditRoom}
        onDeleteRoom={(r) => askDelete({ kind: "room", room: r })}
      />

      <PlaceFullFormDialog open={createOpen} onOpenChange={setCreateOpen} />

      <PlaceEditDialog
        open={editingPlace !== null}
        onOpenChange={(open) => !open && setEditingPlace(null)}
        place={editingPlace}
      />

      <UnitFormDialog
        open={unitDialogOpen}
        onOpenChange={(open) => {
          setUnitDialogOpen(open);
          if (!open) {
            setEditingUnit(null);
            setUnitDialogPlaceId(null);
          }
        }}
        placeId={unitDialogPlaceId ?? undefined}
        unit={editingUnit}
      />

      <RoomFormDialog
        open={roomDialogOpen}
        onOpenChange={(open) => {
          setRoomDialogOpen(open);
          if (!open) {
            setEditingRoom(null);
            setRoomDialogUnitId(null);
          }
        }}
        placesUnitsId={roomDialogUnitId ?? undefined}
        room={editingRoom}
      />

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Confirmer la suppression"
        description={desc}
        confirmLabel="Supprimer"
        onConfirm={confirmDelete}
      />
    </div>
  );
}

export const Route = createFileRoute("/_authenticated/places")({
  component: PlacesPage,
});
