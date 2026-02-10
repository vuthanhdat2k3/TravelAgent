import { apiClient } from "@/lib/api-client";
import type { FlightOffer, FlightSearchRequest } from "@/types/flight";

type FlightSearchResponse = {
  offers: FlightOffer[];
  search_id?: string;
};

export async function searchFlights(
  payload: FlightSearchRequest,
): Promise<FlightSearchResponse> {
  const { data } = await apiClient.post<FlightSearchResponse>(
    "/flights/search",
    payload,
  );
  return data;
}

export type FlightSearchHistoryItem = {
  id: string;
  origin: string;
  destination: string;
  depart_date: string;
  return_date?: string | null;
  adults: number;
  travel_class?: string | null;
  created_at: string;
};

export async function getFlightSearchHistory(): Promise<
  FlightSearchHistoryItem[]
> {
  const { data } = await apiClient.get<FlightSearchHistoryItem[]>(
    "/flights/searches",
  );
  return data;
}

