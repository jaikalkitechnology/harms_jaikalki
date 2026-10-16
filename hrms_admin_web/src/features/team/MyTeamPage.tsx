// My Team: today's picture of everyone below the signed-in manager —
// attendance, daily plans, target progress — with each sub-team rolled
// up so you can open it and go a level down. Director / HR / Admin start
// from the top of the company.
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ChevronRight, Network, Users } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { teamApi, type TeamMemberRow, type TeamRollup } from "@/lib/api/team";
import { cn } from "@/lib/utils";
import { todayIso } from "@/features/employees/profile/ui";
import { MemberPanel } from "./MemberPanel";
import { Avatar, StatusChip, TargetBar, TeamLine, inr } from "./shared";

export default function MyTeamPage() {
  const [params, setParams] = useSearchParams();
  const scope = params.get("scope") === "all" ? "all" : "direct";
  const rootId = params.get("root") ? Number(params.get("root")) : undefined;
  const day = params.get("date") || todayIso();
  const [open, setOpen] = useState<number | null>(null);
  const [filter, setFilter] = useState<"all" | "attention">("all");

  const set = (k: string, v: string | null) =>
    setParams(
      (p) => {
        if (v === null) p.delete(k);
        else p.set(k, v);
        return p;
      },
      { replace: k === "date" },
    );

  const { data, isLoading, isError } = useQuery({
    queryKey: ["team-overview", scope, rootId ?? null, day],
    queryFn: () => teamApi.overview({ scope, root_id: rootId, date: day }),
  });
  const { data: info } = useQuery({ queryKey: ["team-info"], queryFn: teamApi.me });
  // Breadcrumb from the opened person back up to you.
  const { data: rootInfo } = useQuery({
    queryKey: ["team-member", rootId, day],
    queryFn: () => teamApi.member(rootId!, day),
    enabled: !!rootId,
  });

  if (isLoading) return <LoadingScreen label="Loading your team…" />;
  if (isError || !data)
    return <p className="p-6 text-sm text-brand-brown-light">Could not load the team. Please refresh.</p>;

  const s = data.summary;
  const needsAttention = (m: TeamMemberRow) =>
    ["absent", "late", "not_in"].includes(m.today.status) ||
    (!m.dwp_morning && !["on_leave", "off"].includes(m.today.status));
  const rows = filter === "attention" ? data.members.filter(needsAttention) : data.members;
  const title = rootId
    ? `${data.root?.name ?? "Team"}'s team`
    : data.root
      ? "My team"
      : "Whole company";

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <nav className={cn("mb-1 flex flex-wrap items-center gap-1 text-xs text-brand-brown-light", !rootId && "hidden")}>
            <button className="hover:text-brand-brown-darker" onClick={() => set("root", null)}>
              My team
            </button>
            {rootInfo &&
              [...rootInfo.chain]
                .reverse()
                .filter((c) => c.employee_id !== info?.employee_id)
                .map((c) => (
                  <span key={c.employee_id} className="flex items-center gap-1">
                    <ChevronRight className="size-3" />
                    <button className="hover:text-brand-brown-darker" onClick={() => set("root", String(c.employee_id))}>
                      {c.name}
                    </button>
                  </span>
                ))}
            {rootId && data.root && (
              <span className="flex items-center gap-1 text-brand-brown-darker">
                <ChevronRight className="size-3" /> {data.root.name}
              </span>
            )}
          </nav>
          <h1 className="font-display text-2xl font-bold text-brand-brown-darker">{title}</h1>
          <p className="text-sm text-brand-brown-light">
            {s.size} {s.size === 1 ? "person" : "people"}
            {data.direct_count !== s.size && ` · ${data.direct_count} reporting directly`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Input
            type="date"
            value={day}
            max={todayIso()}
            onChange={(e) => set("date", e.target.value || null)}
            className="w-40"
            aria-label="Day"
          />
          <div className="inline-flex rounded-lg border border-brand-brown-100 bg-card p-1">
            {(
              [
                ["direct", "Direct reports"],
                ["all", "Everyone below"],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                type="button"
                onClick={() => set("scope", k === "direct" ? null : k)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm",
                  scope === k ? "bg-brand-gold/15 text-brand-brown-darker" : "text-brand-brown-light",
                )}
              >
                {label}
              </button>
            ))}
          </div>
          <Button asChild variant="outline" className="gap-2">
            <Link to="/org-chart">
              <Network className="size-4" /> Org chart
            </Link>
          </Button>
        </div>
      </div>

      <SummaryTiles s={s} />

      <Card>
        <CardContent className="p-0">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-brand-brown-50 px-5 py-3">
            <div className="inline-flex rounded-lg border border-brand-brown-50 p-1 text-sm">
              {(
                [
                  ["all", `Everyone (${data.members.length})`],
                  ["attention", `Needs attention (${data.members.filter(needsAttention).length})`],
                ] as const
              ).map(([k, label]) => (
                <button
                  key={k}
                  type="button"
                  onClick={() => setFilter(k)}
                  className={cn(
                    "rounded-md px-3 py-1",
                    filter === k ? "bg-brand-gold/15 text-brand-brown-darker" : "text-brand-brown-light",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
            <span className="text-xs text-brand-brown-light">
              Needs attention: absent, late, not in yet, or no morning plan.
            </span>
          </div>
          {rows.length === 0 ? (
            <div className="flex flex-col items-center gap-2 px-6 py-12 text-center text-sm text-brand-brown-light">
              <Users className="size-8 text-brand-gold-dark" />
              {data.members.length === 0
                ? "Nobody reports to you yet."
                : "Everyone is on track today."}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[920px] text-sm">
                <thead className="text-left text-xs uppercase tracking-wide text-brand-brown-light">
                  <tr className="border-b border-brand-brown-50">
                    <th className="px-5 py-2 font-medium">Person</th>
                    <th className="px-3 py-2 font-medium">Today</th>
                    <th className="px-3 py-2 font-medium">Daily plan</th>
                    <th className="px-3 py-2 font-medium">Target</th>
                    <th className="px-3 py-2 font-medium">Their team</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((m) => (
                    <tr
                      key={m.employee_id}
                      className="cursor-pointer border-b border-brand-brown-50 last:border-0 hover:bg-brand-brown-50/40"
                      onClick={() => setOpen(m.employee_id)}
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3" style={{ paddingLeft: scope === "all" ? (m.level - 1) * 18 : 0 }}>
                          <Avatar name={m.name} photo={m.photo_url} />
                          <div className="min-w-0">
                            <div className="font-medium text-brand-brown-darker">{m.name}</div>
                            <div className="truncate text-xs text-brand-brown-light">
                              {[m.designation, m.department].filter(Boolean).join(" · ") || m.employee_code}
                              {scope === "all" && m.level > 1 && m.manager_name ? ` · under ${m.manager_name}` : ""}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-3">
                        <StatusChip today={m.today} />
                      </td>
                      <td className="px-3 py-3 text-xs">
                        <PlanDots morning={m.dwp_morning} eod={m.dwp_eod} />
                      </td>
                      <td className="px-3 py-3">
                        {m.target ? (
                          <TargetBar pct={m.target.achievement_pct} sub={`${inr(m.target.achieved_amount)} of ${inr(m.target.target_amount)}`} />
                        ) : (
                          <span className="text-xs text-brand-brown-light">—</span>
                        )}
                      </td>
                      <td className="px-3 py-3" onClick={(e) => e.stopPropagation()}>
                        {m.team ? (
                          <button
                            type="button"
                            className="group flex items-center gap-2 rounded-lg px-2 py-1 text-left hover:bg-brand-gold/10"
                            onClick={() => set("root", String(m.employee_id))}
                          >
                            <TeamLine t={m.team} />
                            <ChevronRight className="size-4 text-brand-brown-light group-hover:text-brand-gold-dark" />
                          </button>
                        ) : (
                          <span className="text-xs text-brand-brown-light">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {open && (
        <MemberPanel
          employeeId={open}
          day={day}
          onClose={() => setOpen(null)}
          onOpenTeam={(id) => {
            setOpen(null);
            set("root", String(id));
          }}
        />
      )}
    </div>
  );
}

function SummaryTiles({ s }: { s: TeamRollup }) {
  const tiles = [
    {
      label: "Present",
      value: `${s.present_total}`,
      sub: s.attendance_pct != null ? `${s.attendance_pct}% of those working` : "—",
      tone: "text-success",
    },
    { label: "Late", value: `${s.late}`, sub: "checked in late", tone: s.late ? "text-warning" : "" },
    { label: "On leave", value: `${s.on_leave}`, sub: `${s.off} off today`, tone: "" },
    {
      label: "Absent / not in",
      value: `${s.absent + s.not_in}`,
      sub: `${s.absent} absent · ${s.not_in} not in yet`,
      tone: s.absent ? "text-error" : "",
    },
    {
      label: "Daily plans",
      value: `${s.dwp_morning}/${s.size}`,
      sub: `${s.dwp_eod} end-of-day reports`,
      tone: "",
    },
    {
      label: "Target",
      value: s.target_pct != null ? `${s.target_pct}%` : "—",
      sub: s.with_target ? `${inr(s.achieved_amount)} of ${inr(s.target_amount)} · ${s.with_target} with targets` : "No targets set",
      tone: "",
    },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
      {tiles.map((t) => (
        <div key={t.label} className="rounded-xl border border-brand-brown-100 bg-card px-4 py-3">
          <div className="text-xs uppercase tracking-wide text-brand-brown-light">{t.label}</div>
          <div className={cn("mt-1 font-display text-2xl font-bold text-brand-brown-darker", t.tone)}>{t.value}</div>
          <div className="truncate text-xs text-brand-brown-light">{t.sub}</div>
        </div>
      ))}
    </div>
  );
}

function PlanDots({ morning, eod }: { morning: boolean; eod: boolean }) {
  return (
    <span className="flex items-center gap-3">
      <span className={morning ? "text-success" : "text-brand-brown-light"}>{morning ? "✓" : "○"} Morning</span>
      <span className={eod ? "text-success" : "text-brand-brown-light"}>{eod ? "✓" : "○"} EOD</span>
    </span>
  );
}
