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
  // Metadata from DB (contains attachments, suggested_actions)
  metadata?: {
    attachments?: MessageAttachment[];
    suggested_actions?: MessageSuggestedAction[];
  } | null;
  // Rich content for card rendering (populated from SSE or parsed from metadata)
  attachments?: MessageAttachment[];
  suggested_actions?: MessageSuggestedAction[];
};

export type MessageAttachment =
  | { type: "flight_offers"; offers: FlightOfferPayload[] }
  | { type: "booking_success"; booking_id: string; booking_reference: string; status: string; flights?: FlightSegmentPayload[] };

export type FlightOfferPayload = {
  offer_id: string;
  index: number;
  total_price: number;
  currency: string;
  duration_minutes: number;
  stops: number;
  segments: FlightSegmentPayload[];
};

export type FlightSegmentPayload = {
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  airline_code: string;
  flight_number: string;
};

export type MessageSuggestedAction = {
  label: string;
  payload?: string;
  type: string;
  icon?: string;
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

