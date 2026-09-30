// Joined → Intern → Probation → Confirmed, with the open phase's
// progress. Confirm / extend / undo live in the lifecycle dialog.
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Settings2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth";
import {
  lifecycleApi,
  type EmployeeDetail,
  type LifecyclePhase,
} from "@/lib/api/employees";
import { cn } from "@/lib/utils";
import { LifecycleDrawer } from "../LifecycleDrawer";
import { SectionCard, daysUntil, fmtDate, useCanEdit } from "./ui";

interface Step {
  key: string;
  label: string;
  detail: string;
  state: "done" | "current" | "upcoming";
}

function phaseEnd(p: LifecyclePhase): string {
  return p.extension_end_date ?? p.probation_end_date;
}

function isOpen(p: LifecyclePhase): boolean {
  return p.status === "in_progress" || p.status === "extended";
}

export function LifecycleTimeline({ employee }: { employee: EmployeeDetail }) {
  const qc = useQueryClient();
  const canEdit = useCanEdit();
  const canManage = useAuthStore((s) => s.hasPermission("employee.update"));
  const [manageOpen, setManageOpen] = useState(false);
  const { data } = useQuery({
    queryKey: ["lifecycle", employee.id],
    queryFn: () => lifecycleApi.get(employee.id),
  });

  const history = [...(data?.history ?? [])].sort((a, b) =>
    a.probation_start_date.localeCompare(b.probation_start_date),
  );
  const intern = history.filter((h) => h.phase === "intern").at(-1);
  const probation = history.filter((h) => h.phase === "probation").at(-1);
  const open = history.find(isOpen);
  const confirmedOn = data?.confirmation_date ?? employee.confirmation_date;
  const confirmed = data ? data.stage === "confirmed" : !employee.is_on_probation;

  const phaseStep = (key: string, label: string, p?: LifecyclePhase): Step | null => {
    if (!p) return null;
    const range = `${fmtDate(p.probation_start_date)} – ${fmtDate(phaseEnd(p))}`;
    return {
      key,
      label: p.is_extended ? `${label} (extended)` : label,
      detail: range,
      state: isOpen(p) ? "current" : "done",
    };
  };

  const steps: Step[] = [
    {
      key: "joined",
      label: "Joined",
      detail: fmtDate(employee.date_of_joining) || "—",
      state: "done",
    },
    phaseStep("intern", "Internship", intern),
    phaseStep("probation", "Probation", probation) ??
      (!confirmed && !intern
        ? {
            key: "probation",
            label: "Probation",
            detail: employee.probation_end_date
              ? `Ends ${fmtDate(employee.probation_end_date)}`
              : "In progress",
            state: "current" as const,
          }
        : null),
    {
      key: "confirmed",
      label: "Confirmed",
      detail: confirmed ? fmtDate(confirmedOn) || "Confirmed" : "Pending",
      state: confirmed ? "done" : "upcoming",
    },
  ].filter((s): s is Step => s !== null);

  // Progress through the open phase.
  let progress: { pct: number; left: number; end: string } | null = null;
  if (open) {
    const end = phaseEnd(open);
    const total = Math.max(1, daysUntil(end) - daysUntil(open.probation_start_date));
    const left = daysUntil(end);
    progress = {
      pct: Math.min(100, Math.max(0, Math.round(((total - left) / total) * 100))),
      left,
      end,
    };
  }

  return (
    <SectionCard
      title="Lifecycle"
      description="Intern → probation → confirmation. Leaves other than sick leave unlock on confirmation."
      action={
        canManage &&
        canEdit && (
          <Button
            variant={open ? "default" : "outline"}
            size="sm"
            className="h-8 gap-1.5"
            onClick={() => setManageOpen(true)}
          >
            <Settings2 className="h-3.5 w-3.5" />
            {open ? "Confirm / extend" : "Manage"}
          </Button>
        )
      }
    >
      <ol className="grid gap-4 sm:grid-cols-[repeat(auto-fit,minmax(9rem,1fr))]">
        {steps.map((s, i) => (
          <li key={s.key} className="relative flex gap-3 sm:flex-col sm:gap-2">
            <div className="flex items-center sm:w-full">
              <span
                className={cn(
                  "grid h-7 w-7 shrink-0 place-items-center rounded-full border-2 text-xs font-bold",
                  s.state === "done" && "border-success bg-success text-white",
                  s.state === "current" &&
                    "border-brand-gold-dark bg-brand-gold/20 text-brand-gold-dark",
                  s.state === "upcoming" &&
                    "border-brand-brown-100 bg-card text-brand-brown-light",
                )}
              >
                {s.state === "done" ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </span>
              {i < steps.length - 1 && (
                <span
                  className={cn(
                    "ml-2 hidden h-0.5 flex-1 rounded sm:block",
                    s.state === "done" ? "bg-success/60" : "bg-brand-brown-100",
                  )}
                />
              )}
            </div>
            <div className="min-w-0">
              <div
                className={cn(
                  "text-sm font-semibold",
                  s.state === "upcoming"
                    ? "text-brand-brown-light"
                    : "text-brand-brown-darker",
                )}
              >
                {s.label}
              </div>
              <div className="text-xs text-brand-brown-light">{s.detail}</div>
            </div>
          </li>
        ))}
      </ol>

      {progress && open && (
        <div className="mt-5 rounded-xl bg-brand-brown-50/40 p-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2 text-sm">
            <span className="font-medium text-brand-brown-darker">
              {open.phase === "intern" ? "Internship" : "Probation"} ·{" "}
              {progress.left > 0
                ? `${progress.left} day${progress.left === 1 ? "" : "s"} left`
                : progress.left === 0
                  ? "ends today"
                  : `overdue by ${-progress.left} day${progress.left === -1 ? "" : "s"}`}
            </span>
            <span className="text-xs text-brand-brown-light">
              Ends {fmtDate(progress.end)}
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-brand-brown-100">
            <div
              className={cn(
                "h-full rounded-full",
                progress.left < 0 ? "bg-error" : "bg-brand-gold-dark",
              )}
              style={{ width: `${progress.pct}%` }}
            />
          </div>
          {progress.left < 0 && (
            <p className="mt-2 text-xs text-error">
              The end date has passed — confirm or extend.
            </p>
          )}
          {open.extension_reason && (
            <p className="mt-2 text-xs text-brand-brown-light">
              Extended: {open.extension_reason}
            </p>
          )}
        </div>
      )}

      {manageOpen && (
        <LifecycleDrawer
          employeeId={employee.id}
          employeeName={`${employee.first_name} ${employee.last_name}`}
          onClose={() => {
            setManageOpen(false);
            qc.invalidateQueries({ queryKey: ["employee", employee.id] });
            qc.invalidateQueries({ queryKey: ["lifecycle", employee.id] });
          }}
        />
      )}
    </SectionCard>
  );
}
