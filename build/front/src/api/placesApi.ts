import { httpClient } from "./httpClient";
import type {
  Place,
  PlaceInput,
  PlacesUnit,
  PlacesUnitsRoom,
  PlaceFullInput,
  PlaceFullResponse,
} from "./types";

export interface PlacesListFilter {
  ownerId?: number;
  city?: string;
  name?: string;
  limit?: number;
  offset?: number;
}

export async function listPlaces(filter: PlacesListFilter = {}): Promise<Place[]> {
  const { data } = await httpClient.get<Place[]>("/api/v1/places", { params: filter });
  return data;
}

export async function listPlacesUnits(placeId?: number): Promise<PlacesUnit[]> {
  const params = placeId ? { placeId } : {};
  const { data } = await httpClient.get<PlacesUnit[]>("/api/v1/placesUnits", { params });
  return data;
}

export async function listRooms(placesUnitsId?: number): Promise<PlacesUnitsRoom[]> {
  const params = placesUnitsId ? { placesUnitsId } : {};
  const { data } = await httpClient.get<PlacesUnitsRoom[]>("/api/v1/placesUnitsRooms", {
    params,
  });
  return data;
}

export async function createPlaceFull(input: PlaceFullInput): Promise<PlaceFullResponse> {
  const { data } = await httpClient.post<PlaceFullResponse>("/api/v1/places/full", input);
  return data;
}

export async function updatePlace(id: number, input: PlaceInput): Promise<Place> {
  const { data } = await httpClient.patch<Place>(`/api/v1/places/${id}`, input);
  return data;
}

export async function deletePlace(id: number): Promise<void> {
  await httpClient.delete(`/api/v1/places/${id}`);
}

export async function deletePlacesUnit(id: number): Promise<void> {
  await httpClient.delete(`/api/v1/placesUnits/${id}`);
}

export async function deleteRoom(id: number): Promise<void> {
  await httpClient.delete(`/api/v1/placesUnitsRooms/${id}`);
}

// --- Units (create / update) ------------------------------------------------
export interface PlacesUnitInput {
  name?: string | null;
  level?: string | null;
  flatshare?: number;
  address?: string | null;
  zipCode?: number | null;
  city?: string | null;
  surfaceArea?: number | null;
  placeId?: number | null;
  friendlyName?: string | null;
}

export async function createPlacesUnit(input: PlacesUnitInput): Promise<PlacesUnit> {
  const { data } = await httpClient.post<PlacesUnit>("/api/v1/placesUnits", input);
  return data;
}

export async function updatePlacesUnit(id: number, input: PlacesUnitInput): Promise<PlacesUnit> {
  const { data } = await httpClient.patch<PlacesUnit>(`/api/v1/placesUnits/${id}`, input);
  return data;
}

// --- Rooms (create / update) ------------------------------------------------
export interface RoomInput {
  name?: string | null;
  surfaceArea?: number | null;
  placesUnitsId?: number | null;
}

export async function createRoom(input: RoomInput): Promise<PlacesUnitsRoom> {
  const { data } = await httpClient.post<PlacesUnitsRoom>("/api/v1/placesUnitsRooms", input);
  return data;
}

export async function updateRoom(id: number, input: RoomInput): Promise<PlacesUnitsRoom> {
  const { data } = await httpClient.patch<PlacesUnitsRoom>(
    `/api/v1/placesUnitsRooms/${id}`,
    input,
  );
  return data;
}
