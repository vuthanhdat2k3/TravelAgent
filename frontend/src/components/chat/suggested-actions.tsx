"use client";

import { motion } from "framer-motion";
import { CalendarPlusIcon, MailCheckIcon, SparklesIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export type SuggestedActionData = {
  label: string;
  payload?: string;
  type: string; // "quick_reply" | "calendar" | "email"
  icon?: string; // "calendar" | "email" | "star"
};

const ICON_MAP: Record<string, React.ReactNode> = {
  calendar: <CalendarPlusIcon className="h-3.5 w-3.5" />,
  email: <MailCheckIcon className="h-3.5 w-3.5" />,
  star: <SparklesIcon className="h-3.5 w-3.5" />,
};

export function SuggestedActions({
  actions,
  onAction,
  disabled,
}: {
  actions: SuggestedActionData[];
  onAction: (action: SuggestedActionData) => void;
  disabled?: boolean;
}) {
  if (!actions.length) return null;

  return (
    <div className="mt-1.5 flex flex-wrap gap-1.5">
      {actions.map((action, i) => (
        <motion.button
          key={`${action.type}-${i}`}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: i * 0.08 }}
          onClick={() => !disabled && onAction(action)}
          disabled={disabled}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full border border-primary-200 bg-primary-50 px-3 py-1.5",
            "text-[11px] font-medium text-primary-700 transition-all",
            "hover:bg-primary-100 hover:shadow-sm",
            disabled && "pointer-events-none opacity-50",
          )}
        >
          {ICON_MAP[action.icon ?? ""] ?? <SparklesIcon className="h-3.5 w-3.5" />}
          {action.label}
        </motion.button>
      ))}
    </div>
  );
}
