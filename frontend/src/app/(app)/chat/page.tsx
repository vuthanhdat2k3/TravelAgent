"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircleIcon, SendHorizonalIcon } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  createConversation,
  listConversations,
  getConversationWithMessages,
  sendMessage,
} from "@/services/chat-service";
import { useRequireAuth } from "@/hooks/use-auth";
import type { Conversation, Message } from "@/types/chat";

export default function ChatPage() {
  useRequireAuth();
  const queryClient = useQueryClient();
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    null,
  );
  const [input, setInput] = useState("");

  const conversationsQuery = useQuery({
    queryKey: ["chat", "conversations"],
    queryFn: listConversations,
  });

  const effectiveConversationId = useMemo(() => {
    return (
      activeConversationId ??
      conversationsQuery.data?.[0]?.id ??
      null
    );
  }, [activeConversationId, conversationsQuery.data]);

  const messagesQuery = useQuery({
    queryKey: ["chat", "conversation", effectiveConversationId],
    queryFn: () =>
      effectiveConversationId
        ? getConversationWithMessages(effectiveConversationId)
        : Promise.resolve({ conversation: null, messages: [] }),
    enabled: !!effectiveConversationId,
  });

  const createConversationMutation = useMutation({
    mutationFn: () => createConversation("web"),
    onSuccess: (conv) => {
      queryClient.invalidateQueries({ queryKey: ["chat", "conversations"] });
      setActiveConversationId(conv.id);
    },
  });

  const sendMessageMutation = useMutation({
    mutationFn: (payload: { message: string }) =>
      sendMessage({
        message: payload.message,
        conversation_id: effectiveConversationId ?? undefined,
        channel: "web",
      }),
    onSuccess: (resp) => {
      setInput("");
      setActiveConversationId(resp.conversation_id);
      queryClient.invalidateQueries({
        queryKey: ["chat", "conversation", resp.conversation_id],
      });
      queryClient.invalidateQueries({ queryKey: ["chat", "conversations"] });
    },
  });

  const handleSend = () => {
    if (!input.trim()) return;
    if (!effectiveConversationId && !conversationsQuery.data?.length) {
      createConversationMutation.mutate();
    }
    sendMessageMutation.mutate({ message: input.trim() });
  };

  const activeMessages: Message[] =
    (messagesQuery.data?.messages as Message[]) ?? [];

  return (
    <AppShell>
      <div className="grid min-h-[60vh] gap-4 md:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="flex flex-col rounded-xl border border-neutral-200 bg-white/80 p-3 shadow-sm">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-medium text-neutral-900">Cuộc hội thoại</h2>
            <Button
              size="xs"
              variant="outline"
              onClick={() => createConversationMutation.mutate()}
            >
              Mới
            </Button>
          </div>
          <div className="flex-1 space-y-1 overflow-auto text-sm">
            {conversationsQuery.isLoading ? (
              Array.from({ length: 3 }).map((_, idx) => (
                <div
                  key={idx}
                  className="h-8 animate-pulse rounded-md bg-neutral-100"
                />
              ))
            ) : conversationsQuery.data && conversationsQuery.data.length > 0 ? (
              conversationsQuery.data.map((conv: Conversation) => (
                <button
                  key={conv.id}
                  onClick={() => setActiveConversationId(conv.id)}
                  className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs ${
                    conv.id === effectiveConversationId
                      ? "bg-primary-50 text-primary-700"
                      : "hover:bg-neutral-100"
                  }`}
                >
                  <MessageCircleIcon className="h-3.5 w-3.5" />
                  <span className="line-clamp-1">
                    {conv.state?.current_intent ?? "Cuộc hội thoại"}
                  </span>
                </button>
              ))
            ) : (
              <p className="text-xs text-neutral-500">
                Chưa có cuộc hội thoại nào. Bắt đầu bằng cách gửi một tin nhắn.
              </p>
            )}
          </div>
        </aside>

        <section className="flex flex-col rounded-xl border border-neutral-200 bg-white/80 shadow-sm">
          <div className="flex items-center gap-2 border-b border-neutral-100 px-4 py-2.5">
            <MessageCircleIcon className="h-4 w-4 text-primary-600" />
            <div className="flex flex-col">
              <span className="text-sm font-medium text-neutral-900">
                Travel Agent Chat
              </span>
              <span className="text-xs text-neutral-500">
                Đặt câu hỏi, tìm chuyến bay, quản lý bookings.
              </span>
            </div>
          </div>
          <div className="flex-1 space-y-2 overflow-auto px-4 py-3 text-sm">
            <AnimatePresence initial={false}>
              {activeMessages.map((m) => (
                <motion.div
                  key={m.id}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  className={`flex ${
                    m.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[70%] rounded-2xl px-3 py-2 text-xs leading-relaxed ${
                      m.role === "user"
                        ? "bg-primary-600 text-white"
                        : "bg-neutral-100 text-neutral-900"
                    }`}
                  >
                    {m.content}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {!activeMessages.length && (
              <p className="mt-4 text-center text-xs text-neutral-500">
                Hãy bắt đầu cuộc hội thoại bằng cách nhập tin nhắn bên dưới.
              </p>
            )}
          </div>
          <div className="border-t border-neutral-100 px-3 py-2.5">
            <div className="flex items-center gap-2">
              <Input
                placeholder="Nhập tin nhắn..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
              />
              <Button
                size="icon-sm"
                disabled={sendMessageMutation.isPending}
                onClick={handleSend}
              >
                <SendHorizonalIcon className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

