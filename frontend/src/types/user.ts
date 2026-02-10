export type User = {
  id: string;
  email: string;
  full_name?: string | null;
  phone?: string | null;
  is_active: boolean;
  avatar_url?: string | null;
  created_at: string;
};

