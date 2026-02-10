export type NotificationLog = {
  id: string;
  user_id: string;
  type: string;
  channel: string;
  subject?: string | null;
  ref_id?: string | null;
  status: string;
  sent_at: string;
};

