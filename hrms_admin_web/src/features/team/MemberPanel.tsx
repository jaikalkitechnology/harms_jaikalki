// Side panel for one team member: where they sit, today, target, this
// month's attendance, recent daily plans and leave.
import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Mail, Phone, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { teamApi } from "@/lib/api/team";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";
import { Chip, fmtDate } from "@/features/employees/profile/ui";
import { Avatar, StatusChip, TargetBar, TeamLine, hhmm, inr } from "./shared";

const DAY_TONE: Record<string, string> = {
  present: "bg-success/70",
  wfh: "bg-info/60",
  half_day: "bg-brand-gold/70",
  leave: "bg-info/30",
  absent: "bg-error/60",
  holiday: "bg-brand-brown-100",
  week_off: "bg-brand-brown-50",
  blank: "bg-transparent border border-dashed border-brand-brown-100",
};

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-gold-dark">{title}</h3>
      {children}
    </section>
  );
}

export function MemberPanel({
  employeeId,
  day,
  onClose,
  onOpenTeam,
}: {
  employeeId: number;
  day: string;
  onClose: () => void;
  onOpenTeam: (id: number) => void;
}) {
  const canOpenProfile = useAuthStore((s) => s.hasPermission("employee.view.all"));
  const [ym, setYm] = useState(() => ({ y: Number(day.slice(0, 4)), m: Number(day.slice(5, 7)) }));
  const { data: m } = useQuery({
    queryKey: ["team-member", employeeId, day],
    queryFn: () => teamApi.member(employeeId, day),
  });
  const { data: cal } = useQuery({
    queryKey: ["team-calendar", employeeId, ym.y, ym.m],
    queryFn: () => teamApi.calendar(employeeId, ym.y, ym.m),
  });
  const { data: plans = [] } = useQuery({
    queryKey: ["team-plans", employeeId],
    queryFn: () => teamApi.dailyPlans(employeeId),
  });
  const shift = (d: number) =>
    setYm(({ y, m: mo }) => {
      const t = new Date(y, mo - 1 + d, 1);
      return { y: t.getFullYear(), m: t.getMonth() + 1 };
    });
  const monthLabel = new Date(ym.y, ym.m - 1, 1).toLocaleDateString("en-IN", { month: "long", year: "numeric" });
  const lead = cal?.days.length ? (cal.days[0].weekday + 7) % 7 : 0; // Mon = 0

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/30" onClick={onClose}>
      <aside
        className="h-full w-full max-w-lg overflow-y-auto bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
        aria-label="Team member"
      >
        <div className="sticky top-0 z-10 flex items-start gap-3 border-b border-brand-brown-50 bg-card px-5 py-4">
          {m ? <Avatar name={m.name} photo={m.photo_url} size={44} /> : <div className="size-11" />}
          <div className="min-w-0 flex-1">
            <div className="truncate text-lg font-semibold">{m?.name ?? "…"}</div>
            <div className="text-xs text-brand-brown-light">
              {m && [m.designation, m.department, m.employee_code].filter(Boolean).join(" · ")}
            </div>
            {m && m.chain.length > 0 && (
              <div className="mt-1 text-xs text-brand-brown-light">
                Reports to{" "}
                {m.chain.map((c, i) => (
                  <span key={c.employee_id}>
                    {i > 0 && " → "}
                    <span className={i === 0 ? "font-medium text-brand-brown-darker" : ""}>{c.name}</span>
                  </span>
                ))}
              </div>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            <X className="size-4" />
          </Button>
        </div>

        {!m ? (
          <p className="px-5 py-6 text-sm text-brand-brown-light">Loading…</p>
        ) : (
          <div className="space-y-6 px-5 py-4">
            <div className="flex flex-wrap items-start gap-6">
              <div>
                <div className="mb-1 text-xs text-brand-brown-light">{fmtDate(m.on_date)}</div>
                <StatusChip today={m.today} />
              </div>
              <div className="text-xs">
                <div className="mb-1 text-brand-brown-light">Daily plan</div>
                <span className={m.dwp_morning ? "text-success" : "text-brand-brown-light"}>
                  {m.dwp_morning ? "✓" : "○"} Morning
                </span>
                <span className={cn("ml-3", m.dwp_eod ? "text-success" : "text-brand-brown-light")}>
                  {m.dwp_eod ? "✓" : "○"} EOD
                </span>
              </div>
              <div>
                <div className="mb-1 text-xs text-brand-brown-light">
                  Target{m.target ? ` · ${m.target.period_type}` : ""}
                </div>
                {m.target ? (
                  <TargetBar
                    pct={m.target.achievement_pct}
                    sub={`${inr(m.target.achieved_amount)} of ${inr(m.target.target_amount)}`}
                  />
                ) : (
                  <span className="text-xs text-brand-brown-light">No target set</span>
                )}
              </div>
            </div>

            {m.team && (
              <Section title={`Their team · ${m.direct_reports} direct`}>
                <button
                  type="button"
                  onClick={() => onOpenTeam(m.employee_id)}
                  className="flex w-full items-center justify-between gap-2 rounded-lg border border-brand-brown-100 px-3 py-2 text-left hover:bg-brand-gold/10"
                >
                  <TeamLine t={m.team} />
                  <ChevronRight className="size-4 text-brand-brown-light" />
                </button>
              </Section>
            )}

            <Section title="Attendance">
              <div className="mb-2 flex items-center justify-between">
                <Button variant="ghost" size="sm" onClick={() => shift(-1)} aria-label="Previous month">
                  <ChevronLeft className="size-4" />
                </Button>
                <span className="text-sm font-medium">{monthLabel}</span>
                <Button variant="ghost" size="sm" onClick={() => shift(1)} aria-label="Next month">
                  <ChevronRight className="size-4" />
                </Button>
              </div>
              {cal ? (
                <>
                  <div className="grid max-w-sm grid-cols-7 gap-1 text-center text-[10px] text-brand-brown-light">
                    {["M", "T", "W", "T", "F", "S", "S"].map((d, i) => (
                      <span key={i}>{d}</span>
                    ))}
                    {Array.from({ length: lead }).map((_, i) => (
                      <span key={`b${i}`} />
                    ))}
                    {cal.days.map((d) => (
                      <span
                        key={d.date}
                        title={`${fmtDate(d.date)} · ${d.status.replace("_", " ")}${d.check_in ? ` · in ${hhmm(d.check_in)}` : ""}${d.leave_type ? ` · ${d.leave_type}` : ""}${d.holiday_name ? ` · ${d.holiday_name}` : ""}`}
                        className={cn(
                          "grid h-8 place-items-center rounded text-[11px] text-brand-brown-darker",
                          DAY_TONE[d.status] ?? "bg-brand-brown-50",
                        )}
                      >
                        {Number(d.date.slice(8))}
                      </span>
                    ))}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-brand-brown-light">
                    <span>Present {cal.days_present}</span>
                    <span>WFH {cal.days_wfh}</span>
                    <span>Half day {cal.days_half_day}</span>
                    <span>Leave {cal.days_leave}</span>
                    <span className={cal.days_absent ? "text-error" : ""}>Absent {cal.days_absent}</span>
                    <span>Working days {cal.working_days}</span>
                  </div>
                </>
              ) : (
                <p className="text-sm text-brand-brown-light">Loading…</p>
              )}
            </Section>

            <Section title="Recent daily plans">
              {plans.length === 0 ? (
                <p className="text-sm text-brand-brown-light">No daily plans submitted yet.</p>
              ) : (
                <ul className="space-y-2">
                  {plans.slice(0, 8).map((p) => (
                    <li key={p.id} className="rounded-lg border border-brand-brown-50 px-3 py-2 text-sm">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">
                          {fmtDate(p.date)} · {p.type === "morning" ? "Morning plan" : "End of day"}
                        </span>
                        <span className="text-xs text-brand-brown-light">
                          {p.total_hours ? `${Number(p.total_hours)} h` : ""}
                          {p.mood_rating ? ` · mood ${p.mood_rating}/5` : ""}
                        </span>
                      </div>
                      {p.fields
                        .filter((f) => f.value)
                        .slice(0, 3)
                        .map((f) => (
                          <div key={f.field_key} className="mt-0.5 line-clamp-2 text-xs text-brand-brown-light">
                            <span className="capitalize">{f.field_key.replace(/_/g, " ")}:</span> {f.value}
                          </div>
                        ))}
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            <Section title="Recent leave">
              {m.recent_leaves.length === 0 ? (
                <p className="text-sm text-brand-brown-light">No leave taken.</p>
              ) : (
                <ul className="divide-y divide-brand-brown-50 text-sm">
                  {m.recent_leaves.map((l) => (
                    <li key={l.id} className="flex items-center justify-between gap-2 py-1.5">
                      <span>
                        {l.leave_type} · {fmtDate(l.from_date)}
                        {l.to_date !== l.from_date ? ` – ${fmtDate(l.to_date)}` : ""} ({Number(l.days)} d)
                      </span>
                      <Chip
                        tone={l.status === "approved" ? "success" : l.status === "pending" ? "warning" : "neutral"}
                      >
                        {l.status}
                      </Chip>
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            <div className="flex flex-wrap items-center gap-3 border-t border-brand-brown-50 pt-4 text-sm">
              {m.phone && (
                <a href={`tel:${m.phone}`} className="flex items-center gap-1 text-brand-gold-dark hover:underline">
                  <Phone className="size-3.5" /> {m.phone}
                </a>
              )}
              {m.email && (
                <a href={`mailto:${m.email}`} className="flex items-center gap-1 text-brand-gold-dark hover:underline">
                  <Mail className="size-3.5" /> {m.email}
                </a>
              )}
              {canOpenProfile && (
                <Link to={`/employees/${m.employee_id}`} className="ml-auto text-brand-gold-dark hover:underline">
                  Full profile →
                </Link>
              )}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
