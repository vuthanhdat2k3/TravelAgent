import { apiClient } from "@/lib/api-client";
import type { Passenger } from "@/types/passenger";

export type PassengerCreateInput = {
  user_id: string;
  first_name: string;
  last_name: string;
  gender?: string | null;
  dob?: string | null;
  passport_number?: string | null;
  passport_expiry?: string | null;
  nationality?: string | null;
};

export type PassengerUpdateInput = Partial<Omit<PassengerCreateInput, "user_id">>;

export async function listPassengers(): Promise<Passenger[]> {
  const { data } = await apiClient.get<Passenger[]>("/users/me/passengers");
  return data;
}

export async function createPassenger(
  payload: PassengerCreateInput,
): Promise<Passenger> {
  const { data } = await apiClient.post<Passenger>(
    "/users/me/passengers",
    payload,
  );
  return data;
}

export async function getPassenger(id: string): Promise<Passenger> {
  const { data } = await apiClient.get<Passenger>(
    `/users/me/passengers/${id}`,
  );
  return data;
}

export async function updatePassenger(
  id: string,
  payload: PassengerUpdateInput,
): Promise<Passenger> {
  const { data } = await apiClient.patch<Passenger>(
    `/users/me/passengers/${id}`,
    payload,
  );
  return data;
}

export async function deletePassenger(id: string): Promise<void> {
  await apiClient.delete(`/users/me/passengers/${id}`);
}

