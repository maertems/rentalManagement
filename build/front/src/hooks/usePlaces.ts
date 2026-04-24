import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";
import * as placesApi from "@/api/placesApi";
import type { PlaceFullInput, PlaceInput } from "@/api/types";

function invalidatePlacesTree(qc: QueryClient) {
  qc.invalidateQueries({ queryKey: ["places"] });
  qc.invalidateQueries({ queryKey: ["placesUnits"] });
  qc.invalidateQueries({ queryKey: ["placesUnitsRooms"] });
  qc.invalidateQueries({ queryKey: ["occupancy"] });
}

export function usePlacesList(filter: placesApi.PlacesListFilter = {}) {
  return useQuery({
    queryKey: ["places", filter],
    queryFn: () => placesApi.listPlaces(filter),
    select: (d) => Array.isArray(d) ? d : [],
  });
}

export function useAllPlacesUnits() {
  return useQuery({
    queryKey: ["placesUnits"],
    queryFn: () => placesApi.listPlacesUnits(),
    select: (d) => Array.isArray(d) ? d : [],
  });
}

export function useAllRooms() {
  return useQuery({
    queryKey: ["placesUnitsRooms"],
    queryFn: () => placesApi.listRooms(),
    select: (d) => Array.isArray(d) ? d : [],
  });
}

export function useCreatePlaceFull() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: PlaceFullInput) => placesApi.createPlaceFull(input),
    onSuccess: () => invalidatePlacesTree(qc),
  });
}

export function useUpdatePlace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: PlaceInput }) =>
      placesApi.updatePlace(id, input),
    onSuccess: () => invalidatePlacesTree(qc),
  });
}

export function useDeletePlace() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => placesApi.deletePlace(id),
    onSuccess: () => invalidatePlacesTree(qc),
  });
}

export function useCreatePlacesUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: placesApi.PlacesUnitInput) => placesApi.createPlacesUnit(input),
    onSuccess: () => invalidatePlacesTree(qc),
  });
}

export function useUpdatePlacesUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: placesApi.PlacesUnitInput }) =>
      placesApi.updatePlacesUnit(id, input),
    onSuccess: () => invalidatePlacesTree(qc),
  });
}

export function useDeletePlacesUnit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => placesApi.deletePlacesUnit(id),
    onSuccess: () => invalidatePlacesTree(qc),
  });
}

export function useCreateRoom() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: placesApi.RoomInput) => placesApi.createRoom(input),
    onSuccess: () => invalidatePlacesTree(qc),
  });
}

export function useUpdateRoom() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: placesApi.RoomInput }) =>
      placesApi.updateRoom(id, input),
    onSuccess: () => invalidatePlacesTree(qc),
  });
}

export function useDeleteRoom() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => placesApi.deleteRoom(id),
    onSuccess: () => invalidatePlacesTree(qc),
  });
}
