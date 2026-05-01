import { NavLink } from "react-router-dom";
import {
  Activity,
  BadgeCheck,
  Building,
  Calendar,
  ClipboardList,
  Clock,
  Map as MapIcon,
  Briefcase,
  Contact,
  TrendingUp,
  Target,
  Sparkles,
  ClipboardCheck,
  ShieldQuestion,
  FileSignature,
  GraduationCap,
  Trophy,
  BookOpen,
  Award,
  BadgeCheck as BadgeCheckIcon,
  Mic,
  CalendarDays,
  Goal as GoalIcon,
  Coins,
  FileText,
  Gavel,
  Scale,
  LayoutDashboard,
  LogOut,
  Package,
  Palette,
  Plane,
  Receipt,
  Settings,
  Shield,
  ShieldCheck,
  UserCog,
  Users,
  Wallet,
  type LucideIcon,
} from "lucide-react";
import { Logo } from "@/components/shared/Logo";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth";
import type { Role } from "@/lib/constants";

interface NavItem {
  label: string;
  to: string;
  icon: LucideIcon;
  permission?: string;
  roles?: Role[];
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const SECTIONS: NavSection[] = [
  {
    label: "Workspace",
    items: [
      { label: "Dashboard", to: "/dashboard", icon: LayoutDashboard },
      {
        label: "Employees",
        to: "/employees",
        icon: Users,
        permission: "employee.view.all",
      },
      {
        label: "Departments",
        to: "/departments",
        icon: Building,
        permission: "employee.view.all",
      },
      {
        label: "Designations",
        to: "/designations",
        icon: BadgeCheck,
        permission: "employee.view.all",
      },
      {
        label: "Holidays",
        to: "/holidays",
        icon: Calendar,
        permission: "employee.view.all",
      },
      {
        label: "Shifts",
        to: "/shifts",
        icon: Clock,
        permission: "attendance.view.all",
      },
      {
        label: "Salary Templates",
        to: "/salary-templates",
        icon: Coins,
      },
      {
        label: "Intern Expenses",
        to: "/intern-expenses",
        icon: Plane,
        permission: "approval.act",
      },
    ],
  },
  {
    label: "Operations",
    items: [
      {
        label: "Attendance",
        to: "/attendance",
        icon: Clock,
        permission: "attendance.view.all",
      },
      {
        label: "Leaves",
        to: "/leaves",
        icon: Calendar,
        permission: "leave.approve.team",
      },
      {
        label: "Approvals",
        to: "/approvals",
        icon: FileText,
        permission: "approval.act",
      },
      {
        label: "Daily Plans",
        to: "/dwp",
        icon: ClipboardList,
        permission: "approval.act",
      },
      {
        label: "Payroll",
        to: "/payroll",
        icon: Wallet,
        permission: "payroll.run",
      },
      {
        label: "Reimbursements",
        to: "/reimbursements",
        icon: Receipt,
        permission: "approval.act",
      },
      {
        label: "Justice Portal",
        to: "/justice",
        icon: Gavel,
        permission: "approval.act",
      },
      {
        label: "ICC (POSH)",
        to: "/icc",
        icon: Scale,
        permission: "approval.act",
      },
      {
        label: "Customers",
        to: "/field/customers",
        icon: Contact,
        permission: "approval.act",
      },
      {
        label: "Field Jobs",
        to: "/field/jobs",
        icon: Briefcase,
        permission: "approval.act",
      },
      {
        label: "Live Team Map",
        to: "/field/live-map",
        icon: MapIcon,
        permission: "approval.act",
      },
      {
        label: "Leads",
        to: "/sales/leads",
        icon: Sparkles,
        permission: "approval.act",
      },
      {
        label: "Pipeline",
        to: "/sales/pipeline",
        icon: TrendingUp,
        permission: "approval.act",
      },
      {
        label: "Sales Targets",
        to: "/sales/targets",
        icon: Target,
        permission: "approval.act",
      },
      {
        label: "Verifications",
        to: "/verification",
        icon: ClipboardCheck,
        permission: "approval.act",
      },
      {
        label: "Verification Audit",
        to: "/verification/audit",
        icon: ShieldQuestion,
        permission: "approval.act",
      },
      {
        label: "Verif. Templates",
        to: "/verification/templates",
        icon: FileSignature,
        permission: "approval.act",
      },
      {
        label: "Courses",
        to: "/lms/courses",
        icon: GraduationCap,
      },
      {
        label: "Leaderboard",
        to: "/lms/leaderboard",
        icon: Trophy,
      },
      {
        label: "Question Bank",
        to: "/exams/questions",
        icon: BookOpen,
        permission: "admin.users.manage",
      },
      {
        label: "Exams",
        to: "/exams",
        icon: Award,
      },
      {
        label: "Verify Certificate",
        to: "/exams/verify",
        icon: BadgeCheckIcon,
      },
      {
        label: "Trainers",
        to: "/trainers",
        icon: Mic,
      },
      {
        label: "Training Sessions",
        to: "/trainers/sessions",
        icon: CalendarDays,
      },
      {
        label: "Performance Cycles",
        to: "/performance/cycles",
        icon: GoalIcon,
        permission: "approval.act",
      },
      {
        label: "Reports",
        to: "/reports",
        icon: FileText,
        permission: "report.view.all",
      },
    ],
  },
  {
    label: "Super Admin",
    items: [
      { label: "Modules", to: "/super-admin/modules", icon: Package, roles: ["super_admin"] },
      { label: "Roles", to: "/super-admin/roles", icon: UserCog, roles: ["super_admin"] },
      { label: "Permissions", to: "/super-admin/permissions", icon: Shield, roles: ["super_admin"] },
      { label: "Branding", to: "/super-admin/branding", icon: Palette, roles: ["super_admin"] },
      { label: "Audit Logs", to: "/super-admin/audit", icon: Activity, roles: ["super_admin"] },
      { label: "System", to: "/super-admin/system", icon: ShieldCheck, roles: ["super_admin"] },
    ],
  },
  {
    label: "Account",
    items: [{ label: "Settings", to: "/settings", icon: Settings }],
  },
];

export function Sidebar() {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const hasAnyRole = useAuthStore((s) => s.hasAnyRole);
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);
  const role = useAuthStore((s) => s.role);

  const visibleSections = SECTIONS.map((section) => ({
    ...section,
    items: section.items.filter((item) => {
      if (item.roles && !hasAnyRole(item.roles)) return false;
      if (item.permission && !hasPermission(item.permission)) return false;
      return true;
    }),
  })).filter((s) => s.items.length > 0);

  return (
    <aside className="w-64 shrink-0 border-r border-brand-brown-100 bg-card flex flex-col">
      <div className="h-20 flex items-center px-6 border-b border-brand-brown-100">
        <Logo variant="horizontal-light" className="h-10 w-auto" />
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {visibleSections.map((section) => (
          <div key={section.label} className="mb-6">
            <div className="px-3 pb-2 text-[10px] font-mono uppercase tracking-[0.25em] text-brand-brown-light">
              {section.label}
            </div>
            <div className="space-y-1">
              {section.items.map(({ to, label, icon: Icon }) => (
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
            </div>
          </div>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-brand-brown-100">
        {user && (
          <div className="mb-3">
            <div className="text-sm font-semibold text-brand-brown-darker truncate">
              {user.full_name || user.email}
            </div>
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
              {role ?? "—"}
            </div>
          </div>
        )}
        <button
          onClick={() => logout()}
          className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.2em] text-brand-brown-light hover:text-brand-brown-darker"
        >
          <LogOut className="h-3.5 w-3.5" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
