import { apiClient } from "@/lib/api-client";
import type { CalendarEvent } from "@/types/calendar";

export async function addBookingToCalendar(params: {
  bookingId: string;
  calendar_id?: string;
}): Promise<CalendarEvent> {
  const { bookingId, calendar_id } = params;
  const { data } = await apiClient.post<CalendarEvent>(
    `/bookings/${bookingId}/calendar`,
    null,
    {
      params: calendar_id ? { calendar_id } : undefined,
    },
  );
  return data;
}

export async function listMyCalendarEvents(): Promise<CalendarEvent[]> {
  const { data } = await apiClient.get<CalendarEvent[]>(
    "/users/me/calendar-events",
  );
  return data;
}

export async function listBookingCalendarEvents(
  bookingId: string,
): Promise<CalendarEvent[]> {
  const { data } = await apiClient.get<CalendarEvent[]>(
    `/bookings/${bookingId}/calendar`,
  );
  return data;
}

