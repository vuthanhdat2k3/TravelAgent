import { apiClient } from "@/lib/api-client";
import type { Payment } from "@/types/payment";

export async function createPayment(payload: {
  booking_id: string;
  amount: number;
  currency?: string;
  provider?: string;
}): Promise<{ payment: Payment; payment_url: string | null }> {
  const { data } = await apiClient.post<{ payment: Payment; payment_url: string | null }>(
    `/bookings/${payload.booking_id}/payments`,
    payload,
  );
  return data;
}

export async function listPaymentsByBooking(
  bookingId: string,
): Promise<Payment[]> {
  const { data } = await apiClient.get<Payment[]>(
    `/bookings/${bookingId}/payments`,
  );
  return data;
}

