import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Bell, ChevronRight, Menu, Moon, Search, Sun, User } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/auth";
import { useThemeStore } from "@/store/theme";
import { useSidebarStore } from "@/store/sidebar";
import { COMPANY_NAME, ROLE_LABEL, type Role } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { useUnreadCount } from "@/hooks/useUnreadCount";

function useBreadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split("/").filter(Boolean);
  return segments.length === 0 ? ["Dashboard"] : segments;
}

export function Header() {
  const role = useAuthStore((s) => s.role);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const effective = useThemeStore((s) => s.effective);
  const toggle = useThemeStore((s) => s.toggle);
  const crumbs = useBreadcrumbs();
  const [menuOpen, setMenuOpen] = useState(false);
  const unread = useUnreadCount();
  const toggleMobileSidebar = useSidebarStore((s) => s.toggleMobile);

  return (
    <header className="h-20 border-b border-brand-brown-100 bg-card/80 backdrop-blur px-4 md:px-8 flex items-center justify-between gap-3 md:gap-4">
      <button
        onClick={toggleMobileSidebar}
        className="md:hidden h-10 w-10 grid place-items-center rounded-lg hover:bg-brand-brown-50 text-brand-brown-light"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>
      <div className="min-w-0 flex-1 md:flex-none">
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark flex items-center gap-1 truncate">
          {crumbs.map((seg, i) => (
            <span key={i} className="flex items-center gap-1">
              <span>{seg.replace(/-/g, " ")}</span>
              {i < crumbs.length - 1 && <ChevronRight className="h-3 w-3" />}
            </span>
          ))}
        </div>
        <h1 className="font-display text-lg md:text-2xl font-semibold text-brand-brown-darker truncate">
          {COMPANY_NAME}
        </h1>
      </div>

      <div className="hidden md:flex items-center gap-3 flex-1 max-w-md">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-brand-brown-light" />
          <Input
            placeholder="Search employees, modules…"
            className="pl-9"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={toggle}
          aria-label="Toggle theme"
          className="h-10 w-10 grid place-items-center rounded-lg hover:bg-brand-brown-50 text-brand-brown-light"
        >
          {effective === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </button>

        <Link
          to="/notifications"
          aria-label="Notifications"
          className="relative h-10 w-10 grid place-items-center rounded-lg hover:bg-brand-brown-50 text-brand-brown-light"
        >
          <Bell className="h-4 w-4" />
          {unread > 0 && (
            <span className="absolute -top-0.5 -right-0.5 h-5 min-w-5 px-1 rounded-full bg-brand-gold-dark text-white text-[10px] font-bold grid place-items-center">
              {unread > 99 ? "99+" : unread}
            </span>
          )}
        </Link>

        <div className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex items-center gap-2 h-10 px-3 rounded-lg hover:bg-brand-brown-50"
          >
            <span className="h-8 w-8 rounded-full bg-brand-gold/20 grid place-items-center text-brand-brown-darker">
              <User className="h-4 w-4" />
            </span>
            <span className="hidden sm:flex flex-col items-start leading-tight">
              <span className="text-sm font-medium text-brand-brown-darker">
                {user?.full_name || user?.email || "—"}
              </span>
              <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                {ROLE_LABEL[role as Role] ?? "—"}
              </span>
            </span>
          </button>

          {menuOpen && (
            <div
              className={cn(
                "absolute right-0 mt-2 w-56 rounded-xl border border-brand-brown-100 bg-card shadow-lg overflow-hidden",
              )}
            >
              <button className="w-full text-left px-4 py-2.5 text-sm hover:bg-brand-brown-50">
                Profile
              </button>
              <button className="w-full text-left px-4 py-2.5 text-sm hover:bg-brand-brown-50">
                Account settings
              </button>
              <div className="h-px bg-brand-brown-100" />
              <button
                onClick={() => logout()}
                className="w-full text-left px-4 py-2.5 text-sm text-error hover:bg-error/5"
              >
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
