export type ConversationState = {
  current_intent?: string | null;
  slots?: Record<string, string>;
  last_offer_ids?: string[];
  selected_passenger_id?: string | null;
  step?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type Conversation = {
  id: string;
  user_id?: string | null;
  channel: string;
  state?: ConversationState | null;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type Message = {
  id: string;
  role: string;
  content: string;
  intent?: string | null;
  agent_name?: string | null;
  created_at: string;
};

export type SuggestedAction = {
  label: string;
  payload?: string | null;
  type: string;
};

export type ChatResponse = {
  conversation_id: string;
  message_id: string;
  content: string;
  intent?: string | null;
  agent_name?: string | null;
  state?: ConversationState | null;
  suggested_actions: SuggestedAction[];
  attachments: Record<string, unknown>[];
  created_at: string;
};

