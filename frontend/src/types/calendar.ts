export type CalendarEvent = {
  id: string;
  booking_id: string;
  user_id: string;
  google_event_id: string;
  calendar_id?: string | null;
  synced_at: string;
  created_at: string;
};

