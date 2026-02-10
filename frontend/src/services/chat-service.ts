import { apiClient } from "@/lib/api-client";
import type {
  Conversation,
  Message,
  ChatResponse,
} from "@/types/chat";

export async function createConversation(
  channel: string = "web",
): Promise<Conversation> {
  const { data } = await apiClient.post<Conversation>("/chat/conversations", {
    channel,
  });
  return data;
}

export async function listConversations(): Promise<Conversation[]> {
  const { data } = await apiClient.get<Conversation[]>("/chat/conversations");
  return data;
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await apiClient.delete(`/chat/conversations/${conversationId}`);
}

export async function deleteAllConversations(): Promise<{ deleted: number }> {
  const { data } = await apiClient.delete<{ deleted: number }>("/chat/conversations");
  return data;
}

export async function getConversationWithMessages(conversationId: string): Promise<{
  conversation: Conversation;
  messages: Message[];
}> {
  const { data } = await apiClient.get<{
    conversation: Conversation;
    messages: Message[];
  }>(`/chat/conversations/${conversationId}`);
  return data;
}

export async function sendMessage(payload: {
  message: string;
  conversation_id?: string;
  user_id?: string;
  channel?: string;
}): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>("/chat/messages", payload);
  return data;
}

export async function sendMessageToConversation(params: {
  conversationId: string;
  message: string;
  user_id?: string;
  channel?: string;
}): Promise<ChatResponse> {
  const { conversationId, ...body } = params;
  const { data } = await apiClient.post<ChatResponse>(
    `/chat/conversations/${conversationId}/messages`,
    body,
  );
  return data;
}

// ── SSE Streaming ─────────────────────────────────────────────────────────

export type StreamEvent =
  | { type: "meta"; conversation_id: string; user_message_id: string }
  | { type: "token"; content: string }
  | { type: "attachments"; data: ChatAttachment[] }
  | { type: "suggested_actions"; data: ChatSuggestedAction[] }
  | { type: "done"; message_id: string; full_content: string }
  | { type: "error"; content: string };

export type ChatAttachment =
  | { type: "flight_offers"; offers: FlightOfferData[] }
  | { type: "booking_success"; booking_id: string; booking_reference: string; status: string; flights?: FlightSegmentData[] };

export type FlightOfferData = {
  offer_id: string;
  index: number;
  total_price: number;
  currency: string;
  duration_minutes: number;
  stops: number;
  segments: FlightSegmentData[];
};

export type FlightSegmentData = {
  origin: string;
  destination: string;
  departure_time: string;
  arrival_time: string;
  airline_code: string;
  flight_number: string;
};

export type ChatSuggestedAction = {
  label: string;
  payload?: string;
  type: string;
  icon?: string;
};

/**
 * Send a message and receive the AI response via SSE streaming.
 *
 * @param payload - Essentially the same as sendMessage
 * @param onEvent - Called for each SSE event (meta, token, done, error)
 * @param signal  - Optional AbortSignal to cancel the stream
 */
export async function sendMessageStream(
  payload: {
    message: string;
    conversation_id?: string;
    channel?: string;
  },
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

  const token =
    typeof window !== "undefined"
      ? window.localStorage.getItem("ta_access_token")
      : null;

  const response = await fetch(`${API_BASE_URL}/chat/messages/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    onEvent({
      type: "error",
      content: `HTTP ${response.status}: ${response.statusText}`,
    });
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    onEvent({ type: "error", content: "No response body" });
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE lines (data: {...}\n\n)
    const lines = buffer.split("\n\n");
    buffer = lines.pop() ?? ""; // Keep incomplete chunk

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data: ")) continue;

      const jsonStr = trimmed.slice(6); // Remove "data: " prefix
      try {
        const event = JSON.parse(jsonStr) as StreamEvent;
        onEvent(event);
      } catch {
        // Ignore malformed events
      }
    }
  }
}
