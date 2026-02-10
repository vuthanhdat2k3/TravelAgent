export type Passenger = {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  gender?: string | null;
  dob?: string | null;
  passport_number?: string | null;
  passport_expiry?: string | null;
  nationality?: string | null;
  created_at: string;
};

