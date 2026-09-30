// Shown for resigned / terminated / exited employees: last working day,
// notice left, final settlement state, and the switch that unlocks
// editing once they have left.
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { DoorOpen, Lock, Unlock } from "lucide-react";

import { Button } from "@/components/ui/button";
import { launchApi } from "@/lib/api/launch";
import type { EmployeeDetail } from "@/lib/api/employees";
import { daysUntil, fmtDate, titleCase } from "./ui";

export const SEPARATED_STATUSES = [
  "resigned",
  "terminated",
  "exited",
  "separated",
  "inactive",
  "absconded",
];

export function isSeparated(e: Pick<EmployeeDetail, "status">): boolean {
  return SEPARATED_STATUSES.includes(e.status);
}

/** Left the company: separated and the last working day has passed. */
export function hasLeft(e: Pick<EmployeeDetail, "status" | "exit_date">): boolean {
  return isSeparated(e) && !!e.exit_date && daysUntil(e.exit_date) < 0;
}

export function ExitBanner({
  employee,
  editUnlocked,
  onToggleEdit,
}: {
  employee: EmployeeDetail;
  editUnlocked: boolean;
  onToggleEdit: () => void;
}) {
  const { data: separations = [] } = useQuery({
    queryKey: ["resignations", { employee_id: employee.id }],
    queryFn: () => launchApi.listResignations({ employee_id: employee.id }),
  });
  const sep = [...separations].sort((a, b) =>
    b.requested_at.localeCompare(a.requested_at),
  )[0];

  const lwd =
    employee.exit_date ??
    sep?.actual_last_working_day ??
    sep?.proposed_last_working_day ??
    null;
  const left = lwd ? daysUntil(lwd) : null;
  const gone = hasLeft(employee);
  const kind =
    employee.status === "terminated" || sep?.separation_type === "termination"
      ? "Terminated"
      : titleCase(employee.status);

  const settlement = sep?.final_settled_at
    ? `Final settlement paid ${fmtDate(sep.final_settled_at)}`
    : sep?.hr_cleared_at
      ? "HR clearance done · final settlement pending"
      : "Final settlement pending";

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-error/30 bg-error/5 px-5 py-4 sm:flex-row sm:items-center">
      <DoorOpen className="hidden h-6 w-6 shrink-0 text-error sm:block" />
      <div className="min-w-0 flex-1">
        <div className="font-semibold text-brand-brown-darker">
          {kind}
          {lwd &&
            (gone
              ? ` · left on ${fmtDate(lwd)}`
              : ` · last working day ${fmtDate(lwd)}${
                  left !== null ? ` (${left === 0 ? "today" : `${left} days left`})` : ""
                }`)}
        </div>
        <div className="text-sm text-brand-brown-light">
          {settlement}
          {gone && !editUnlocked && " · profile is read-only"}
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button asChild variant="outline" size="sm">
          <Link to="/separations">Open separation</Link>
        </Button>
        {gone && (
          <Button variant="outline" size="sm" className="gap-1.5" onClick={onToggleEdit}>
            {editUnlocked ? (
              <>
                <Lock className="h-3.5 w-3.5" /> Lock editing
              </>
            ) : (
              <>
                <Unlock className="h-3.5 w-3.5" /> Unlock editing
              </>
            )}
          </Button>
        )}
      </div>
    </div>
  );
}
