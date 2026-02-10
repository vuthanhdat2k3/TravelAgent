"use client";

import { ReactNode, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  PlaneTakeoffIcon,
  LayoutDashboardIcon,
  SearchIcon,
  UsersIcon,
  SlidersHorizontalIcon,
  CalendarDaysIcon,
  MessageCircleIcon,
  ShieldIcon,
  MenuIcon,
  LogOutIcon,
} from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth-store";
import { logout } from "@/services/auth-service";

type Props = {
  children: ReactNode;
};

type SidebarNavProps = {
  pathname: string | null;
  user: { full_name?: string | null; email?: string | null } | null;
  onLogout: () => void;
  onNavigate?: () => void;
};

function SidebarNav({ pathname, user, onLogout, onNavigate }: SidebarNavProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 py-4">
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <PlaneTakeoffIcon className="h-5 w-5" />
        </span>
        <div className="flex flex-col leading-tight">
          <span className="text-sm font-semibold tracking-tight text-neutral-900">
            Travel Agent
          </span>
          <span className="text-xs text-neutral-500">
            Your modern flight concierge
          </span>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-2 pb-3">
        {NAV_ITEMS.map((item) => {
          const active =
            pathname === item.href || pathname?.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={[
                "flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition",
                active
                  ? "bg-primary/10 text-primary"
                  : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900",
              ].join(" ")}
            >
              <Icon className="h-4 w-4" />
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-neutral-200 px-3 py-3">
        <div className="mb-2 px-1">
          <p className="text-xs font-medium text-neutral-700">
            {user?.full_name ?? user?.email ?? "Tài khoản"}
          </p>
          {user?.email ? (
            <p className="text-xs text-neutral-500">{user.email}</p>
          ) : null}
        </div>
        <Button
          variant="outline"
          className="w-full justify-start gap-2"
          onClick={onLogout}
        >
          <LogOutIcon className="h-4 w-4" />
          Đăng xuất
        </Button>
      </div>
    </div>
  );
}

const NAV_ITEMS: {
  href: string;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}[] = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboardIcon },
  { href: "/flights/search", label: "Tìm chuyến bay", icon: SearchIcon },
  { href: "/passengers", label: "Hành khách", icon: UsersIcon },
  { href: "/preferences", label: "Sở thích", icon: SlidersHorizontalIcon },
  { href: "/calendar", label: "Lịch", icon: CalendarDaysIcon },
  { href: "/chat", label: "Chat", icon: MessageCircleIcon },
  { href: "/admin", label: "Admin", icon: ShieldIcon },
];



export function AppShell({ children }: Props) {
  const pathname = usePathname();
  const router = useRouter();
  const clearSession = useAuthStore((s) => s.clearSession);
  const user = useAuthStore((s) => s.user);
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
       console.error("Logout API failed", error);
    }
    clearSession();
    router.push("/login");
  };

  const activeLabel = useMemo(() => {
    const match = NAV_ITEMS.find(
      (item) => pathname === item.href || pathname?.startsWith(item.href + "/"),
    );
    return match?.label ?? "Travel Agent";
  }, [pathname]);

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r border-neutral-200 bg-white/80 backdrop-blur md:block">
          <SidebarNav pathname={pathname} user={user} onLogout={handleLogout} />
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          {/* Minimal top bar (no horizontal nav) */}
          <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-neutral-200 bg-white/80 px-4 backdrop-blur md:hidden">
            <button
              type="button"
              className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-neutral-200 bg-white text-neutral-700"
              onClick={() => setMobileOpen(true)}
              aria-label="Open menu"
            >
              <MenuIcon className="h-4 w-4" />
            </button>
            <div className="text-sm font-medium text-neutral-900">
              {activeLabel}
            </div>
            <span className="h-9 w-9" />
          </header>

          <main className="flex-1 px-4 py-6 md:px-8 md:py-8">
            <div className="w-full">{children}</div>
          </main>
        </div>
      </div>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {mobileOpen ? (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/30 md:hidden"
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
              className="fixed inset-y-0 left-0 z-50 w-72 border-r border-neutral-200 bg-white md:hidden"
            >
              <SidebarNav
                pathname={pathname}
                user={user}
                onLogout={handleLogout}
                onNavigate={() => setMobileOpen(false)}
              />
            </motion.aside>
          </>
        ) : null}
      </AnimatePresence>
    </div>
  );
}

