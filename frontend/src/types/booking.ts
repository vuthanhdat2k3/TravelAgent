export type BookingFlight = {
  id: string;
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  airline_code: string;
  flight_number: string;
  duration_minutes: number;
  stops: number;
  cabin_class?: string | null;
};

export type BookingListItem = {
  id: string;
  user_id: string;
  passenger_id: string;
  status: string;
  provider: string;
  booking_reference?: string | null;
  total_price?: number | null;
  currency?: string | null;
  created_at: string;
  confirmed_at?: string | null;
  flights: BookingFlight[];
};

export type BookingDetail = {
  booking_id: string;
  status: string;
  provider: string;
  booking_reference?: string | null;
  total_price?: number | null;
  currency?: string | null;
  flights: import("./flight").FlightSegment[];
  created_at?: string | null;
  confirmed_at?: string | null;
};

