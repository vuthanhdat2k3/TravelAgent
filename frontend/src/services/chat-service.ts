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

