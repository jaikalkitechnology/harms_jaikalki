import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, ChevronRight, Circle } from "lucide-react";

import { employeesApi } from "@/lib/api/employees";
import { cn } from "@/lib/utils";
import { SectionCard } from "./ui";

export function useCompleteness(employeeId: number) {
  return useQuery({
    queryKey: ["employee-completeness", employeeId],
    queryFn: () => employeesApi.completeness(employeeId),
  });
}

export function completenessTone(pct: number): string {
  if (pct >= 100) return "bg-success";
  if (pct >= 70) return "bg-brand-gold-dark";
  return "bg-warning";
}

export function CompletenessCard({
  employeeId,
  onGo,
}: {
  employeeId: number;
  /** Opens the profile tab that fixes an item. */
  onGo: (section: string) => void;
}) {
  const { data } = useCompleteness(employeeId);
  if (!data) return null;

  return (
    <SectionCard
      title="Profile completeness"
      description={`${data.done} of ${data.total} done`}
    >
      <div className="flex items-center gap-3">
        <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-brand-brown-100">
          <div
            className={cn("h-full rounded-full", completenessTone(data.percent))}
            style={{ width: `${data.percent}%` }}
          />
        </div>
        <span className="w-10 text-right text-sm font-semibold tabular-nums">
          {data.percent}%
        </span>
      </div>

      {data.missing.length === 0 ? (
        <p className="mt-4 flex items-center gap-2 text-sm text-success">
          <CheckCircle2 className="h-4 w-4" /> Everything payroll and HR need is on file.
        </p>
      ) : (
        <ul className="mt-4 space-y-1">
          {data.missing.map((m) => (
            <li key={m.key}>
              <button
                type="button"
                onClick={() => onGo(m.section)}
                className="group flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm hover:bg-brand-brown-50/60"
              >
                <Circle className="h-3.5 w-3.5 shrink-0 text-warning" />
                <span className="flex-1 text-brand-brown-darker">{m.label}</span>
                <ChevronRight className="h-3.5 w-3.5 text-brand-brown-light opacity-0 transition-opacity group-hover:opacity-100" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}
