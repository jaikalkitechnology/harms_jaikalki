import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { fetchDashboardSummary, fetchHealth } from "@/lib/api/health";
import { useAuthStore } from "@/store/auth";
import { ROLE_LABEL, type Role } from "@/lib/constants";
import {
  Users,
  CalendarCheck,
  Wallet,
  ClipboardList,
  Cake,
  Briefcase,
} from "lucide-react";
import { fmtIstDate } from "@/lib/datetime";

const HEALTH_OK = new Set(["ok", "healthy", "available", "live"]);

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const role = useAuthStore((s) => s.role);
  const permissions = useAuthStore((s) => s.permissions);

  const { data: health, isLoading: healthLoading, isError: healthError } =
    useQuery({
      queryKey: ["health"],
      queryFn: fetchHealth,
      refetchInterval: 30_000,
    });
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: fetchDashboardSummary,
    refetchInterval: 60_000,
  });

  const stats = [
    {
      label: "Total Headcount",
      value: summary?.total_headcount ?? "—",
      hint: summary?.role
        ? "Active employees"
        : "Available to Director / HR / Super Admin",
      icon: Users,
    },
    {
      label: "Team Present Today",
      value:
        summary?.team_size && summary.team_size > 0
          ? `${summary.team_present_today}/${summary.team_size}`
          : summary?.today_attendance.checked_in
          ? "You ✓"
          : "—",
      hint:
        summary?.team_size && summary.team_size > 0
          ? `${summary.team_attendance_pct}% attendance`
          : "Manager view",
      icon: CalendarCheck,
    },
    {
      label: "Pending Approvals",
      value: summary?.pending_approvals_count ?? "—",
      hint: summary?.pending_by_type?.length
        ? summary.pending_by_type
            .map((p) => `${p.request_type}: ${p.count}`)
            .join(" · ")
        : "Across your scope",
      icon: ClipboardList,
    },
    {
      label: "Next Payday",
      value:
        summary?.next_payday_in_days != null
          ? summary.next_payday_in_days === 0
            ? "Today"
            : `${summary.next_payday_in_days}d`
          : "—",
      hint: "1st of every month",
      icon: Wallet,
    },
  ];

  return (
    <div className="space-y-6 md:space-y-8">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ {ROLE_LABEL[role as Role] ?? "Overview"}
        </div>
        <h2 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
          {user
            ? `Welcome back, ${user.full_name.split(" ")[0] || user.email}`
            : "Today, at a glance"}
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(({ label, value, hint, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                  {label}
                </span>
                <Icon className="h-4 w-4 text-brand-gold-dark" />
              </div>
              <div className="font-display text-3xl font-bold text-brand-brown-darker">
                {summaryLoading ? "…" : value}
              </div>
              <div className="mt-1 text-xs text-brand-brown-light line-clamp-2">
                {hint}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* HR / Director extras */}
      {summary &&
        (summary.birthdays_today.length > 0 ||
          summary.probation_expiring_30d.length > 0) && (
          <div className="grid lg:grid-cols-2 gap-4">
            {summary.birthdays_today.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cake className="h-5 w-5" /> Birthdays this week
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1 text-sm">
                    {summary.birthdays_today.map((b) => (
                      <li
                        key={b.employee_id}
                        className="flex justify-between border-b border-brand-brown-50 py-1.5 last:border-0"
                      >
                        <span>{b.full_name}</span>
                        <span className="text-brand-brown-light text-xs">
                          {fmtIstDate(b.date_of_birth)}
                        </span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
            {summary.probation_expiring_30d.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Briefcase className="h-5 w-5" /> Probations expiring (30d)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-1 text-sm">
                    {summary.probation_expiring_30d.map((p) => (
                      <li
                        key={p.employee_id}
                        className="flex justify-between border-b border-brand-brown-50 py-1.5 last:border-0"
                      >
                        <span>{p.full_name}</span>
                        <span className="text-brand-brown-light text-xs">
                          {p.days_remaining}d left
                        </span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>
        )}

      <div className="grid lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>
              Backend <span className="display-em">health</span>
            </CardTitle>
            <CardDescription>
              Live status from <code className="font-mono">/health</code>.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {healthLoading && (
              <div className="text-sm text-brand-brown-light">Pinging…</div>
            )}
            {healthError && (
              <div className="text-sm text-error">
                Could not reach the backend.
              </div>
            )}
            {health && (
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <Row k="App" v={health.app} />
                <Row k="Version" v={health.version} />
                <Row k="Env" v={health.environment} />
                <HealthRow k="DB" v={health.db} />
                <HealthRow k="Redis" v={health.redis} />
              </dl>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>
              Your <span className="display-em">permissions</span>
            </CardTitle>
            <CardDescription>
              {permissions.length} grant{permissions.length === 1 ? "" : "s"}.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-1.5">
              {permissions.length === 0 && (
                <span className="text-sm text-brand-brown-light">
                  No granular permissions on this account.
                </span>
              )}
              {permissions.map((p) => (
                <span
                  key={p}
                  className="text-[10px] font-mono px-2 py-1 rounded-md bg-brand-brown-50 text-brand-brown-darker"
                >
                  {p}
                </span>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
        {k}
      </dt>
      <dd className="font-medium text-brand-brown-darker">{v}</dd>
    </div>
  );
}

function HealthRow({ k, v }: { k: string; v: string }) {
  const ok = HEALTH_OK.has((v ?? "").toLowerCase());
  return (
    <div>
      <dt className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
        {k}
      </dt>
      <dd
        className={`font-medium ${
          ok ? "text-success" : "text-error"
        } break-words`}
      >
        {v}
      </dd>
    </div>
  );
}
