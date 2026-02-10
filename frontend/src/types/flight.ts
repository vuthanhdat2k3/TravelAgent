export type FlightSegment = {
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  airline_code: string;
  flight_number: string;
};

export type FlightOffer = {
  offer_id: string;
  total_price: number;
  currency: string;
  duration_minutes: number;
  stops: number;
  segments: FlightSegment[];
};

export type FlightSearchRequest = {
  origin: string;
  destination: string;
  depart_date: string;
  return_date?: string | null;
  adults: number;
  travel_class: "ECONOMY" | "BUSINESS" | string;
  currency: string;
};

