"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";
import { useAuth } from "@/lib/auth";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Кабинет" },
  { href: "/diagnostics", label: "Диагностика" },
  { href: "/trainer", label: "Тренажёр" },
  { href: "/assistant", label: "Ассистент" },
];

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col md:flex-row">
      <aside className="md:w-56 md:min-h-screen border-b md:border-b-0 md:border-r border-hairline bg-card">
        <div className="px-5 py-5">
          <span className="font-display font-extrabold text-lg tracking-tight text-indigo">
            AXIOM
          </span>
        </div>
        <nav className="flex md:flex-col px-3 pb-3 md:pb-0 gap-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`focus-ring rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? "bg-indigo-soft text-indigo"
                    : "text-muted hover:bg-paper hover:text-ink"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="hidden md:block mt-auto px-5 py-4 border-t border-hairline">
          <p className="text-xs text-muted truncate">{user?.email}</p>
          <button
            onClick={logout}
            className="focus-ring mt-2 text-sm font-medium text-brick hover:underline"
          >
            Выйти
          </button>
        </div>
      </aside>
      <main className="flex-1 px-4 py-6 md:px-10 md:py-10">{children}</main>
    </div>
  );
}
