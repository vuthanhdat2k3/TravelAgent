export type UserPreference = {
  id: string;
  user_id: string;
  cabin_class?: string | null;
  preferred_airlines?: string[] | null;
  seat_preference?: string | null;
  default_passenger_id?: string | null;
  created_at: string;
  updated_at: string;
};

