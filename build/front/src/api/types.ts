// ============================================================================
// DTOs mirroring backend Pydantic schemas.
// Keep field names in camelCase, matching the API responses.
// ============================================================================

export interface User {
  id: number;
  email: string;
  username: string | null;
  name: string | null;
  avatar: string | null;
  verified: number;
  emailVisibility: number;
  isAdmin: number;
  isWithdraw: number;
  ownerId: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface Owner {
  id: number;
  name: string | null;
  email: string | null;
  address: string | null;
  zipCode: number | null;
  city: string | null;
  phoneNumber: string | null;
  iban: string | null;
  userId: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface OwnerInput {
  name?: string | null;
  email?: string | null;
  address?: string | null;
  zipCode?: number | null;
  city?: string | null;
  phoneNumber?: string | null;
  iban?: string | null;
  userId?: number | null;
}

export interface Place {
  id: number;
  name: string | null;
  address: string | null;
  zipCode: number | null;
  city: string | null;
  ownerId: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface PlaceInput {
  name?: string | null;
  address?: string | null;
  zipCode?: number | null;
  city?: string | null;
  ownerId?: number | null;
}

export interface PlacesUnit {
  id: number;
  name: string | null;
  level: string | null;
  flatshare: number;
  address: string | null;
  zipCode: number | null;
  city: string | null;
  surfaceArea: number | null;
  placeId: number | null;
  friendlyName: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface PlacesUnitsRoom {
  id: number;
  name: string | null;
  surfaceArea: number | null;
  placesUnitsId: number | null;
  createdAt: string;
  updatedAt: string;
}

export type TenantGenre = "Mlle" | "Mme" | "M" | "Societe";

export interface Tenant {
  id: number;
  genre: TenantGenre | null;
  firstName: string | null;
  name: string | null;
  email: string | null;
  phone: string | null;
  billingSameAsRental: number;
  billingAddress: string | null;
  billingZipCode: number | null;
  billingCity: string | null;
  billingPhone: string | null;
  withdrawName: string | null;
  withdrawDay: number;
  placeUnitId: number | null;
  placeUnitRoomId: number | null;
  sendNoticeOfLeaseRental: number;
  sendLeaseRental: number;
  active: number;
  dateEntrance: string | null;
  dateExit: string | null;
  warantyReceiptId: number | null;
  createdAt: string;
  updatedAt: string;
}

export type RentType = "Loyer" | "Charges" | "Garantie";

export interface Rent {
  id: number;
  tenantId: number | null;
  type: RentType | null;
  price: number | null;
  dateExpiration: string | null;
  active: number;
  createdAt: string;
  updatedAt: string;
}

export interface RentReceipt {
  id: number;
  placeUnitId: number | null;
  placeUnitRoomId: number | null;
  tenantId: number | null;
  amount: number | null;
  periodBegin: string | null;
  periodEnd: string | null;
  paid: number;
  createdAt: string;
  updatedAt: string;
}

export interface RentReceiptsDetail {
  id: number;
  rentReceiptsId: number | null;
  sortOrder: number | null;
  description: string | null;
  price: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface RentsFee {
  id: number;
  tenantId: number | null;
  applicationMonth: string | null;
  description: string | null;
  subDescription: string | null;
  price: number | null;
  hasDocument: boolean;
  createdAt: string;
  updatedAt: string;
}

// ============================================================================
// Profile (me)
// ============================================================================

export interface ProfileRead {
  user: User;
  owner: Owner | null;
}

export interface ProfileUserUpdate {
  name?: string | null;
  username?: string | null;
}

export interface ProfileOwnerUpdate {
  name?: string | null;
  email?: string | null;
  address?: string | null;
  zipCode?: number | null;
  city?: string | null;
  phoneNumber?: string | null;
  iban?: string | null;
}

export interface ProfileUpdate {
  user?: ProfileUserUpdate;
  owner?: ProfileOwnerUpdate;
}

// ============================================================================
// Owner full create (admin)
// ============================================================================

/** Mode A: new user. Mode B: existing user. Exactly one of user/existingUserId must be set. */
export interface OwnerFullInput {
  user?: {
    email: string;
    password: string;
    name?: string | null;
    username?: string | null;
    isAdmin?: number;
  } | null;
  existingUserId?: number | null;
  owner: {
    name?: string | null;
    email?: string | null;
    address?: string | null;
    zipCode?: number | null;
    city?: string | null;
    phoneNumber?: string | null;
    iban?: string | null;
  };
}

export interface OwnerFullResponse {
  user: User;
  owner: Owner;
}

// ============================================================================
// Aggregate endpoints
// ============================================================================

export interface PlaceFullInput {
  place: PlaceInput;
  units: Array<{
    name?: string | null;
    level?: string | null;
    flatshare: number;
    address?: string | null;
    zipCode?: number | null;
    city?: string | null;
    surfaceArea?: number | null;
    friendlyName?: string | null;
    rooms: Array<{ name?: string | null; surfaceArea?: number | null }>;
  }>;
}

export interface PlaceFullResponse {
  place: Place;
  units: Array<PlacesUnit & { rooms: PlacesUnitsRoom[] }>;
}

export interface TenantFullInput {
  tenant: {
    genre?: TenantGenre | null;
    firstName?: string | null;
    name?: string | null;
    email?: string | null;
    phone?: string | null;
    placeUnitId?: number | null;
    placeUnitRoomId?: number | null;
    dateEntrance?: string | null;
    withdrawDay: number;
    withdrawName?: string | null;
    billingSameAsRental?: number;
    billingAddress?: string | null;
    billingZipCode?: number | null;
    billingCity?: string | null;
    billingPhone?: string | null;
  };
  rents: {
    loyer: { price: number };
    charges: { price: number };
    garantie: { price: number };
  };
  cautionReceipt: {
    amount: number;
    periodBegin?: string | null;
    paid: number;
  } | null;
}

export interface TenantFullResponse {
  tenant: Tenant;
  rents: Rent[];
  cautionReceipt: RentReceipt | null;
}

// ============================================================================
// Dashboard
// ============================================================================

export interface OccupancyTenant {
  tenantId: number;
  firstName: string | null;
  name: string | null;
  rentAmount: number | null;
  rentAmountEstimated: boolean;
  rentPaid: boolean;
}

export interface OccupancyRoom {
  roomId: number;
  roomName: string | null;
  surfaceArea: number | null;
  tenants: OccupancyTenant[];
}

export interface OccupancyUnit {
  unitId: number;
  unitName: string | null;
  friendlyName: string | null;
  level: string | null;
  flatshare: boolean;
  rooms: OccupancyRoom[];
  tenants: OccupancyTenant[];
}

export interface OccupancyPlace {
  placeId: number;
  placeName: string | null;
  ownerId: number | null;
  ownerName: string | null;
  units: OccupancyUnit[];
}

export interface OccupancyResponse {
  month: string;
  places: OccupancyPlace[];
}
