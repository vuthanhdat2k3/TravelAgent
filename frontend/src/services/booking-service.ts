import { apiClient } from "@/lib/api-client";
import type { BookingListItem, BookingDetail } from "@/types/booking";

export async function fetchMyBookings(): Promise<BookingListItem[]> {
  const { data } = await apiClient.get<BookingListItem[]>("/bookings");
  return data;
}

export async function getBookingById(
  bookingId: string,
): Promise<BookingListItem> {
  const { data } = await apiClient.get<BookingListItem>(
    `/bookings/${bookingId}`,
  );
  return data;
}

export async function cancelBooking(
  bookingId: string,
): Promise<BookingDetail> {
  const { data } = await apiClient.post<BookingDetail>(
    `/bookings/${bookingId}/cancel`,
  );
  return data;
}

export async function createBooking(payload: {
  passenger_id: string;
  offer_id: string;
}): Promise<BookingDetail> {
  const { data } = await apiClient.post<BookingDetail>("/bookings", payload);
  return data;
}

