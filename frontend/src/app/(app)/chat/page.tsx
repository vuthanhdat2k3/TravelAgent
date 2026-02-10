"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircleIcon, SendHorizonalIcon, Loader2Icon, Trash2Icon, XCircleIcon } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FlightCardList } from "@/components/chat/flight-card";
import { BookingSuccessCard } from "@/components/chat/booking-success-card";
import { SuggestedActions } from "@/components/chat/suggested-actions";
import type { FlightOffer } from "@/components/chat/flight-card";
import type { SuggestedActionData } from "@/components/chat/suggested-actions";
import {
  createConversation,
  listConversations,
  getConversationWithMessages,
  sendMessageStream,
  deleteConversation,
  deleteAllConversations,
} from "@/services/chat-service";
import type { ChatAttachment, ChatSuggestedAction } from "@/services/chat-service";
import { useRequireAuth } from "@/hooks/use-auth";
import type { Conversation, Message, MessageAttachment, MessageSuggestedAction } from "@/types/chat";

export default function ChatPage() {
  useRequireAuth();
  const queryClient = useQueryClient();
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    null,
  );
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [optimisticMessages, setOptimisticMessages] = useState<Message[]>([]);
  const [pendingAttachments, setPendingAttachments] = useState<MessageAttachment[]>([]);
  const [pendingSuggestedActions, setPendingSuggestedActions] = useState<MessageSuggestedAction[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  // Persist SSE extras (attachments, actions) across query refetches
  const messageExtrasRef = useRef<
    Record<string, { attachments?: MessageAttachment[]; suggested_actions?: MessageSuggestedAction[] }>
  >({});

  // ── Queries ──────────────────────────────────────────────────────────

  const conversationsQuery = useQuery<Conversation[]>({
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

  const messagesQuery = useQuery<{
    conversation: Conversation | null;
    messages: Message[];
  }>({
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
      setOptimisticMessages([]);
    },
  });

  const deleteConversationMutation = useMutation({
    mutationFn: (id: string) => deleteConversation(id),
    onSuccess: (_data, deletedId) => {
      if (effectiveConversationId === deletedId) {
        setActiveConversationId(null);
        setOptimisticMessages([]);
        setStreamingContent("");
      }
      queryClient.invalidateQueries({ queryKey: ["chat", "conversations"] });
    },
  });

  const deleteAllConversationsMutation = useMutation({
    mutationFn: () => deleteAllConversations(),
    onSuccess: () => {
      setActiveConversationId(null);
      setOptimisticMessages([]);
      setStreamingContent("");
      messageExtrasRef.current = {};
      queryClient.invalidateQueries({ queryKey: ["chat", "conversations"] });
    },
  });

  // ── Merged messages ──────────────────────────────────────────────────

  const allMessages = useMemo(() => {
    const serverMsgs = (messagesQuery.data?.messages as Message[]) ?? [];
    // Enrich server messages with attachments from metadata or SSE extras
    const enriched = serverMsgs.map((m) => {
      const sseExtras = messageExtrasRef.current[m.id];
      const metaAttachments = m.metadata?.attachments;
      const metaActions = m.metadata?.suggested_actions;
      if (sseExtras || metaAttachments || metaActions) {
        return {
          ...m,
          attachments: sseExtras?.attachments ?? metaAttachments ?? m.attachments,
          suggested_actions: sseExtras?.suggested_actions ?? metaActions ?? m.suggested_actions,
        };
      }
      return m;
    });
    const serverIds = new Set(enriched.map((m) => m.id));
    const uniqueOptimistic = optimisticMessages.filter(
      (m) => !serverIds.has(m.id),
    );
    return [...enriched, ...uniqueOptimistic];
  }, [messagesQuery.data?.messages, optimisticMessages]);

  // ── Auto-scroll ──────────────────────────────────────────────────────

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [allMessages.length, streamingContent, scrollToBottom]);

  // ── Streaming send ───────────────────────────────────────────────────

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    const userMsg: Message = {
      id: `opt-${Date.now()}`,
      role: "user",
      content: trimmed,
      created_at: new Date().toISOString(),
    };

    setOptimisticMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsStreaming(true);
    setStreamingContent("");
    setPendingAttachments([]);
    setPendingSuggestedActions([]);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let resolvedConvId = effectiveConversationId;
    let capturedAttachments: MessageAttachment[] = [];
    let capturedActions: MessageSuggestedAction[] = [];

    try {
      await sendMessageStream(
        {
          message: trimmed,
          conversation_id: effectiveConversationId ?? undefined,
          channel: "web",
        },
        (event) => {
          switch (event.type) {
            case "meta":
              resolvedConvId = event.conversation_id;
              if (!effectiveConversationId) {
                setActiveConversationId(event.conversation_id);
              }
              break;
            case "token":
              setStreamingContent((prev) => prev + event.content);
              break;
            case "attachments":
              capturedAttachments = event.data as MessageAttachment[];
              setPendingAttachments(capturedAttachments);
              break;
            case "suggested_actions":
              capturedActions = event.data as MessageSuggestedAction[];
              setPendingSuggestedActions(capturedActions);
              break;
            case "done": {
              // Persist extras in ref so they survive query refetches
              if (capturedAttachments.length > 0 || capturedActions.length > 0) {
                messageExtrasRef.current[event.message_id] = {
                  attachments: capturedAttachments.length > 0 ? capturedAttachments : undefined,
                  suggested_actions: capturedActions.length > 0 ? capturedActions : undefined,
                };
              }
              const assistantMsg: Message = {
                id: event.message_id,
                role: "assistant",
                content: event.full_content,
                created_at: new Date().toISOString(),
                attachments: capturedAttachments.length > 0 ? capturedAttachments : undefined,
                suggested_actions: capturedActions.length > 0 ? capturedActions : undefined,
              };
              setStreamingContent("");
              setIsStreaming(false);
              setOptimisticMessages([assistantMsg]);
              setPendingAttachments([]);
              setPendingSuggestedActions([]);
              if (resolvedConvId) {
                queryClient.invalidateQueries({
                  queryKey: ["chat", "conversation", resolvedConvId],
                });
              }
              queryClient.invalidateQueries({
                queryKey: ["chat", "conversations"],
              });
              break;
            }
            case "error":
              setStreamingContent(event.content);
              setIsStreaming(false);
              break;
          }
        },
        controller.signal,
      );
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setStreamingContent("⚠️ Lỗi kết nối. Vui lòng thử lại.");
        setIsStreaming(false);
      }
    }
  }, [input, isStreaming, effectiveConversationId, queryClient]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  // ── Flight card selection ────────────────────────────────────────────

  const handleFlightSelect = useCallback(
    (offer: FlightOffer) => {
      const seg = offer.segments[0];
      const flightCode = `${seg?.airline_code ?? ""}${seg?.flight_number ?? ""}`;
      const message = `Đặt chuyến ${flightCode}`;
      setInput(message);
      // Auto send
      setTimeout(() => {
        const fakeEvent = { key: "Enter", shiftKey: false, preventDefault: () => {} } as React.KeyboardEvent;
        // Directly trigger send
        setInput("");
        const userMsg: Message = {
          id: `opt-${Date.now()}`,
          role: "user",
          content: message,
          created_at: new Date().toISOString(),
        };
        setOptimisticMessages((prev) => [...prev, userMsg]);
        setIsStreaming(true);
        setStreamingContent("");
        setPendingAttachments([]);
        setPendingSuggestedActions([]);

        const controller = new AbortController();
        abortControllerRef.current = controller;
        let resolvedConvId = effectiveConversationId;
        let capturedAttachments: MessageAttachment[] = [];
        let capturedActions: MessageSuggestedAction[] = [];

        sendMessageStream(
          {
            message,
            conversation_id: effectiveConversationId ?? undefined,
            channel: "web",
          },
          (event) => {
            switch (event.type) {
              case "meta":
                resolvedConvId = event.conversation_id;
                if (!effectiveConversationId) setActiveConversationId(event.conversation_id);
                break;
              case "token":
                setStreamingContent((prev) => prev + event.content);
                break;
              case "attachments":
                capturedAttachments = event.data as MessageAttachment[];
                setPendingAttachments(capturedAttachments);
                break;
              case "suggested_actions":
                capturedActions = event.data as MessageSuggestedAction[];
                setPendingSuggestedActions(capturedActions);
                break;
              case "done": {
                // Persist extras in ref so they survive query refetches
                if (capturedAttachments.length > 0 || capturedActions.length > 0) {
                  messageExtrasRef.current[event.message_id] = {
                    attachments: capturedAttachments.length > 0 ? capturedAttachments : undefined,
                    suggested_actions: capturedActions.length > 0 ? capturedActions : undefined,
                  };
                }
                const assistantMsg: Message = {
                  id: event.message_id,
                  role: "assistant",
                  content: event.full_content,
                  created_at: new Date().toISOString(),
                  attachments: capturedAttachments.length > 0 ? capturedAttachments : undefined,
                  suggested_actions: capturedActions.length > 0 ? capturedActions : undefined,
                };
                setStreamingContent("");
                setIsStreaming(false);
                setOptimisticMessages([assistantMsg]);
                setPendingAttachments([]);
                setPendingSuggestedActions([]);
                if (resolvedConvId) {
                  queryClient.invalidateQueries({ queryKey: ["chat", "conversation", resolvedConvId] });
                }
                queryClient.invalidateQueries({ queryKey: ["chat", "conversations"] });
                break;
              }
              case "error":
                setStreamingContent(event.content);
                setIsStreaming(false);
                break;
            }
          },
          controller.signal,
        ).catch((err) => {
          if ((err as Error).name !== "AbortError") {
            setStreamingContent("⚠️ Lỗi kết nối. Vui lòng thử lại.");
            setIsStreaming(false);
          }
        });
      }, 0);
    },
    [effectiveConversationId, queryClient],
  );

  // ── Suggested action handler ─────────────────────────────────────────

  const handleSuggestedAction = useCallback(
    (action: SuggestedActionData) => {
      if (action.payload) {
        setInput(action.payload);
        // Trigger send on next tick
        setTimeout(() => {
          const syntheticInput = action.payload!;
          setInput("");
          const userMsg: Message = {
            id: `opt-${Date.now()}`,
            role: "user",
            content: syntheticInput,
            created_at: new Date().toISOString(),
          };
          setOptimisticMessages((prev) => [...prev, userMsg]);
          setIsStreaming(true);
          setStreamingContent("");
          setPendingAttachments([]);
          setPendingSuggestedActions([]);

          const controller = new AbortController();
          abortControllerRef.current = controller;
          let resolvedConvId = effectiveConversationId;
          let capturedAttachments: MessageAttachment[] = [];
          let capturedActions: MessageSuggestedAction[] = [];

          sendMessageStream(
            {
              message: syntheticInput,
              conversation_id: effectiveConversationId ?? undefined,
              channel: "web",
            },
            (event) => {
              switch (event.type) {
                case "meta":
                  resolvedConvId = event.conversation_id;
                  if (!effectiveConversationId) setActiveConversationId(event.conversation_id);
                  break;
                case "token":
                  setStreamingContent((prev) => prev + event.content);
                  break;
                case "attachments":
                  capturedAttachments = event.data as MessageAttachment[];
                  setPendingAttachments(capturedAttachments);
                  break;
                case "suggested_actions":
                  capturedActions = event.data as MessageSuggestedAction[];
                  setPendingSuggestedActions(capturedActions);
                  break;
                case "done": {
                  // Persist extras in ref so they survive query refetches
                  if (capturedAttachments.length > 0 || capturedActions.length > 0) {
                    messageExtrasRef.current[event.message_id] = {
                      attachments: capturedAttachments.length > 0 ? capturedAttachments : undefined,
                      suggested_actions: capturedActions.length > 0 ? capturedActions : undefined,
                    };
                  }
                  const assistantMsg: Message = {
                    id: event.message_id,
                    role: "assistant",
                    content: event.full_content,
                    created_at: new Date().toISOString(),
                    attachments: capturedAttachments.length > 0 ? capturedAttachments : undefined,
                    suggested_actions: capturedActions.length > 0 ? capturedActions : undefined,
                  };
                  setStreamingContent("");
                  setIsStreaming(false);
                  setOptimisticMessages([assistantMsg]);
                  setPendingAttachments([]);
                  setPendingSuggestedActions([]);
                  if (resolvedConvId) {
                    queryClient.invalidateQueries({ queryKey: ["chat", "conversation", resolvedConvId] });
                  }
                  queryClient.invalidateQueries({ queryKey: ["chat", "conversations"] });
                  break;
                }
                case "error":
                  setStreamingContent(event.content);
                  setIsStreaming(false);
                  break;
              }
            },
            controller.signal,
          ).catch((err) => {
            if ((err as Error).name !== "AbortError") {
              setStreamingContent("⚠️ Lỗi kết nối. Vui lòng thử lại.");
              setIsStreaming(false);
            }
          });
        }, 0);
      }
    },
    [effectiveConversationId, queryClient],
  );

  return (
    <AppShell>
      <div className="grid h-[calc(100vh-5rem)] gap-4 md:grid-cols-[260px_minmax(0,1fr)]">
        {/* ── Conversations sidebar ── */}
        <aside className="flex flex-col rounded-xl border border-neutral-200 bg-white/80 p-3 shadow-sm">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-medium text-neutral-900">Cuộc hội thoại</h2>
            <div className="flex items-center gap-1">
              {conversationsQuery.data && conversationsQuery.data.length > 0 && (
                <Button
                  size="xs"
                  variant="ghost"
                  className="h-7 w-7 p-0 text-neutral-400 hover:text-red-500"
                  title="Xóa tất cả"
                  onClick={() => {
                    if (confirm("Xóa tất cả cuộc hội thoại?")) {
                      deleteAllConversationsMutation.mutate();
                    }
                  }}
                >
                  <XCircleIcon className="h-3.5 w-3.5" />
                </Button>
              )}
              <Button
                size="xs"
                variant="outline"
                onClick={() => createConversationMutation.mutate()}
              >
                Mới
              </Button>
            </div>
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
                <div
                  key={conv.id}
                  className={`group flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-xs ${
                    conv.id === effectiveConversationId
                      ? "bg-primary-50 text-primary-700"
                      : "hover:bg-neutral-100"
                  }`}
                >
                  <button
                    className="flex min-w-0 flex-1 items-center gap-2"
                    onClick={() => {
                      setActiveConversationId(conv.id);
                      setOptimisticMessages([]);
                      setStreamingContent("");
                    }}
                  >
                    <MessageCircleIcon className="h-3.5 w-3.5 shrink-0" />
                    <span className="line-clamp-1">
                      {conv.state?.current_intent ?? "Cuộc hội thoại"}
                    </span>
                  </button>
                  <button
                    className="shrink-0 rounded p-0.5 text-neutral-300 opacity-0 transition-opacity hover:text-red-500 group-hover:opacity-100"
                    title="Xóa"
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteConversationMutation.mutate(conv.id);
                    }}
                  >
                    <Trash2Icon className="h-3 w-3" />
                  </button>
                </div>
              ))
            ) : (
              <p className="text-xs text-neutral-500">
                Chưa có cuộc hội thoại nào. Bắt đầu bằng cách gửi một tin nhắn.
              </p>
            )}
          </div>
        </aside>

        {/* ── Chat area ── */}
        <section className="flex min-h-0 flex-col rounded-xl border border-neutral-200 bg-white/80 shadow-sm">
          {/* Header */}
          <div className="flex items-center gap-2 border-b border-neutral-100 px-4 py-2.5">
            <MessageCircleIcon className="h-4 w-4 text-primary-600" />
            <div className="flex flex-col">
              <span className="text-sm font-medium text-neutral-900">
                Travel Agent Chat
              </span>
              <span className="text-xs text-neutral-500">
                {isStreaming ? (
                  <span className="flex items-center gap-1 text-primary-600">
                    <Loader2Icon className="h-3 w-3 animate-spin" />
                    Đang trả lời...
                  </span>
                ) : (
                  "Đặt câu hỏi, tìm chuyến bay, quản lý bookings."
                )}
              </span>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 space-y-2 overflow-auto px-4 py-3 text-sm">
            <AnimatePresence initial={false}>
              {allMessages.map((m) => (
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
                    className={`max-w-[80%] ${
                      m.role === "user"
                        ? "rounded-2xl bg-primary-600 px-3 py-2 text-xs leading-relaxed text-white"
                        : "space-y-2"
                    }`}
                  >
                    {/* Text content */}
                    {m.role === "user" ? (
                      <div className="whitespace-pre-wrap">{m.content}</div>
                    ) : (
                      <div className="rounded-2xl bg-neutral-100 px-3 py-2 text-xs leading-relaxed text-neutral-900">
                        <div className="whitespace-pre-wrap">{m.content}</div>
                      </div>
                    )}

                    {/* Render flight offer cards */}
                    {m.role === "assistant" &&
                      m.attachments?.map((att, i) => {
                        if (att.type === "flight_offers") {
                          return (
                            <FlightCardList
                              key={`flights-${i}`}
                              offers={att.offers}
                              onSelect={handleFlightSelect}
                              disabled={isStreaming}
                            />
                          );
                        }
                        if (att.type === "booking_success") {
                          return (
                            <BookingSuccessCard
                              key={`booking-${i}`}
                              booking={att}
                              onAction={handleSuggestedAction}
                              disabled={isStreaming}
                            />
                          );
                        }
                        return null;
                      })}

                    {/* Render suggested actions */}
                    {m.role === "assistant" && m.suggested_actions && m.suggested_actions.length > 0 && (
                      <SuggestedActions
                        actions={m.suggested_actions}
                        onAction={handleSuggestedAction}
                        disabled={isStreaming}
                      />
                    )}
                  </div>
                </motion.div>
              ))}

              {/* Streaming bubble */}
              {isStreaming && streamingContent && (
                <motion.div
                  key="streaming"
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="max-w-[80%] space-y-2">
                    <div className="rounded-2xl bg-neutral-100 px-3 py-2 text-xs leading-relaxed text-neutral-900">
                      <div className="whitespace-pre-wrap">
                        {streamingContent}
                        <span className="ml-0.5 inline-block h-3.5 w-0.5 animate-pulse bg-primary-500" />
                      </div>
                    </div>
                    {/* Show flight cards while still streaming */}
                    {pendingAttachments.map((att, i) => {
                      if (att.type === "flight_offers") {
                        return (
                          <FlightCardList
                            key={`pending-flights-${i}`}
                            offers={att.offers}
                            onSelect={handleFlightSelect}
                            disabled={isStreaming}
                          />
                        );
                      }
                      if (att.type === "booking_success") {
                        return (
                          <BookingSuccessCard
                            key={`pending-booking-${i}`}
                            booking={att}
                            onAction={handleSuggestedAction}
                            disabled
                          />
                        );
                      }
                      return null;
                    })}
                  </div>
                </motion.div>
              )}

              {/* Typing dots */}
              {isStreaming && !streamingContent && (
                <motion.div
                  key="typing"
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex justify-start"
                >
                  <div className="rounded-2xl bg-neutral-100 px-4 py-2.5">
                    <div className="flex gap-1">
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-400 [animation-delay:0s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-400 [animation-delay:0.15s]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-neutral-400 [animation-delay:0.3s]" />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {!allMessages.length && !isStreaming && (
              <p className="mt-4 text-center text-xs text-neutral-500">
                Hãy bắt đầu cuộc hội thoại bằng cách nhập tin nhắn bên dưới.
              </p>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
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
                disabled={isStreaming}
              />
              <Button
                size="icon-sm"
                disabled={isStreaming || !input.trim()}
                onClick={handleSend}
              >
                {isStreaming ? (
                  <Loader2Icon className="h-4 w-4 animate-spin" />
                ) : (
                  <SendHorizonalIcon className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
