"use client";

import { ReactNode } from "react";

type Props = {
  title: string;
  subtitle?: string;
  footer?: ReactNode;
  children: ReactNode;
};

export function AuthCard({ title, subtitle, footer, children }: Props) {
  return (
    <div className="mx-auto flex w-full max-w-md flex-col gap-6">
      <div className="space-y-2 text-center">
        <h1 className="text-2xl font-semibold tracking-tight text-neutral-900">
          {title}
        </h1>
        {subtitle ? (
          <p className="text-sm text-neutral-600">{subtitle}</p>
        ) : null}
      </div>

      <div className="rounded-xl border border-neutral-200 bg-white/80 p-6 shadow-sm backdrop-blur">
        {children}
      </div>

      {footer ? (
        <div className="text-center text-sm text-neutral-600">{footer}</div>
      ) : null}
    </div>
  );
}

