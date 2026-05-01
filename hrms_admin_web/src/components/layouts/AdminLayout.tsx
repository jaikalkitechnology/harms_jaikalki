import { NavLink, Outlet } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  CalendarCheck,
  ClipboardList,
  Wallet,
  ShieldCheck,
  Settings,
  LogOut,
} from "lucide-react";
import { Logo } from "@/components/shared/Logo";
import { cn } from "@/lib/utils";
import { COMPANY_NAME } from "@/lib/constants";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/employees", label: "Employees", icon: Users },
  { to: "/attendance", label: "Attendance", icon: CalendarCheck },
  { to: "/approvals", label: "Approvals", icon: ClipboardList },
  { to: "/payroll", label: "Payroll", icon: Wallet },
  { to: "/super-admin", label: "Super Admin", icon: ShieldCheck },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function AdminLayout() {
  return (
    <div className="min-h-screen flex bg-surface-cream">
      <aside className="w-64 shrink-0 border-r border-brand-brown-100 bg-card flex flex-col">
        <div className="h-20 flex items-center px-6 border-b border-brand-brown-100">
          <Logo variant="horizontal-light" className="h-10 w-auto" />
        </div>

        <nav className="flex-1 px-3 py-6 space-y-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-gold/15 text-brand-brown-darker"
                    : "text-brand-brown-light hover:bg-brand-brown-50 hover:text-brand-brown-darker",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-6 py-4 border-t border-brand-brown-100">
          <button className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.2em] text-brand-brown-light hover:text-brand-brown-darker">
            <LogOut className="h-3.5 w-3.5" />
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col">
        <header className="h-20 border-b border-brand-brown-100 bg-card/80 backdrop-blur px-8 flex items-center justify-between">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
              ★ Admin Console
            </div>
            <h1 className="font-display text-2xl font-semibold text-brand-brown-darker">
              {COMPANY_NAME}
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-gold/15 border border-brand-gold/40 text-xs font-mono uppercase tracking-[0.2em] text-brand-brown">
              <span className="h-2 w-2 rounded-full bg-brand-gold shadow-[0_0_8px] shadow-brand-gold" />
              Phase 0 · Foundation
            </span>
          </div>
        </header>

        <main className="flex-1 px-8 py-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
