import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, RotateCcw, X } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { leavesApi, type LeaveRequest } from "@/lib/api/leaves";
import { employeesApi } from "@/lib/api/employees";
import { fmtIstDate } from "@/lib/datetime";

const STATUS_TONE: Record<string, string> = {
  pending: "bg-info/15 text-info",
  approved: "bg-success/15 text-success",
  rejected: "bg-error/15 text-error",
  cancelled: "bg-brand-brown-50 text-brand-brown-light",
};

export default function LeaveApprovalsPage() {
  const qc = useQueryClient();

  const [status, setStatus] = useState("");
  const [leaveTypeId, setLeaveTypeId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");

  const { data: pending = [], isLoading } = useQuery({
    queryKey: ["leaves-pending"],
    queryFn: leavesApi.pending,
  });
  const { data: types = [] } = useQuery({
    queryKey: ["leave-types"],
    queryFn: leavesApi.types,
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-active-att"],
    queryFn: () => employeesApi.list(),
  });
  const empById = useMemo(() => {
    const m = new Map<number, string>();
    employees.forEach((e) =>
      m.set(e.id, `${e.employee_code} · ${e.first_name} ${e.last_name}`),
    );
    return m;
  }, [employees]);

  const filters = {
    status: status || undefined,
    leave_type_id: leaveTypeId ? Number(leaveTypeId) : undefined,
    employee_id: employeeId ? Number(employeeId) : undefined,
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
  };
  const { data: all = [], isLoading: allLoading } = useQuery({
    queryKey: ["leaves-all", filters],
    queryFn: () => leavesApi.listAll(filters),
  });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["leaves-pending"] });
    qc.invalidateQueries({ queryKey: ["leaves-all"] });
  };
  const errMsg = (e: unknown, fb: string) =>
    (e as { response?: { data?: { detail?: string } } })?.response?.data
      ?.detail ?? fb;

  const approve = useMutation({
    mutationFn: (id: number) => leavesApi.approve(id, "Approved"),
    onSuccess: () => {
      toast.success("Leave approved");
      refresh();
    },
    onError: (e) => toast.error(errMsg(e, "Could not approve")),
  });
  const reject = useMutation({
    mutationFn: (id: number) => leavesApi.reject(id, "Rejected"),
    onSuccess: () => {
      toast.success("Leave rejected");
      refresh();
    },
    onError: (e) => toast.error(errMsg(e, "Could not reject")),
  });
  const undo = useMutation({
    mutationFn: (id: number) => leavesApi.undo(id),
    onSuccess: () => {
      toast.success("Decision undone — back to pending");
      refresh();
    },
    onError: (e) => toast.error(errMsg(e, "Could not undo")),
  });

  if (isLoading) return <LoadingScreen label="Loading approvals…" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Leaves
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          Leave <span className="display-em">approvals</span>
        </h2>
        <p className="mt-1 text-sm text-brand-brown-light">
          {pending.length} pending · {all.length} in the filtered list.
        </p>
      </div>

      {/* ── Pending queue ── */}
      <Card>
        <CardHeader>
          <CardTitle>Pending approvals</CardTitle>
          <CardDescription>
            Approve or reject. Decided requests move to the list below
            where they can be undone.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {pending.length === 0 ? (
            <p className="py-6 text-center text-brand-brown-light">
              All caught up.
            </p>
          ) : (
            <div className="grid md:grid-cols-2 gap-3">
              {pending.map((req) => (
                <LeaveCard
                  key={req.id}
                  request={req}
                  who={empById.get(req.employee_id)}
                  onApprove={() => approve.mutate(req.id)}
                  onReject={() => reject.mutate(req.id)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Filterable full list ── */}
      <Card>
        <CardHeader>
          <CardTitle>All leave requests</CardTitle>
          <CardDescription>
            Every request in your scope. Undo reverts an approved /
            rejected decision back to pending (an approved leave's
            balance is released).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <div>
              <Label>Status</Label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-card px-2 text-sm"
              >
                <option value="">All</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
            <div>
              <Label>Leave type</Label>
              <select
                value={leaveTypeId}
                onChange={(e) => setLeaveTypeId(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-card px-2 text-sm"
              >
                <option value="">All</option>
                {types.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.code}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Employee</Label>
              <select
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-card px-2 text-sm"
              >
                <option value="">All</option>
                {employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.employee_code}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>From</Label>
              <Input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
              />
            </div>
            <div>
              <Label>To</Label>
              <Input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
              />
            </div>
          </div>

          <div className="rounded-xl border border-brand-brown-100 overflow-x-auto">
            <table className="w-full text-sm min-w-[760px]">
              <thead className="bg-brand-brown-50/60">
                <tr>
                  {[
                    "Employee",
                    "Type",
                    "Dates",
                    "Days",
                    "Reason",
                    "Status",
                    "Action",
                  ].map((h) => (
                    <th
                      key={h}
                      className="text-left px-3 py-2 text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allLoading ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-brand-brown-light">
                      Loading…
                    </td>
                  </tr>
                ) : all.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-brand-brown-light">
                      No requests match these filters.
                    </td>
                  </tr>
                ) : (
                  all.map((r) => (
                    <tr
                      key={r.id}
                      className="border-t border-brand-brown-100/60"
                    >
                      <td className="px-3 py-2 text-xs">
                        {empById.get(r.employee_id) ??
                          `#${r.employee_id}`}
                      </td>
                      <td className="px-3 py-2">
                        {r.leave_type?.code ?? "—"}
                      </td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {r.from_date} → {r.to_date}
                      </td>
                      <td className="px-3 py-2">
                        {r.days}
                        {r.half_day ? " (½)" : ""}
                      </td>
                      <td className="px-3 py-2 text-xs text-brand-brown-light max-w-[14rem] truncate">
                        {r.reason ?? "—"}
                      </td>
                      <td className="px-3 py-2">
                        <span
                          className={`text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded ${
                            STATUS_TONE[r.status] ?? ""
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex gap-1.5">
                          {r.status === "pending" && (
                            <>
                              <Button
                                size="sm"
                                className="h-7"
                                disabled={approve.isPending}
                                onClick={() => approve.mutate(r.id)}
                              >
                                <Check className="h-3.5 w-3.5" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="h-7"
                                disabled={reject.isPending}
                                onClick={() => reject.mutate(r.id)}
                              >
                                <X className="h-3.5 w-3.5" />
                              </Button>
                            </>
                          )}
                          {(r.status === "approved" ||
                            r.status === "rejected") && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 gap-1"
                              disabled={undo.isPending}
                              onClick={() => {
                                if (
                                  confirm(
                                    `Undo this ${r.status} leave? It returns to pending${r.status === "approved" ? " and the balance is released" : ""}.`,
                                  )
                                )
                                  undo.mutate(r.id);
                              }}
                            >
                              <RotateCcw className="h-3.5 w-3.5" />
                              Undo
                            </Button>
                          )}
                          {r.status === "cancelled" && (
                            <span className="text-[11px] text-brand-brown-light">
                              —
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function LeaveCard({
  request,
  who,
  onApprove,
  onReject,
}: {
  request: LeaveRequest;
  who?: string;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle>
              {request.leave_type?.code ?? "—"} · {request.days} day
              {Number(request.days) > 1 ? "s" : ""}
            </CardTitle>
            <CardDescription>
              {who ?? `Employee #${request.employee_id}`} ·{" "}
              {fmtIstDate(request.applied_at)}
            </CardDescription>
          </div>
          {request.half_day && (
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded bg-info/15 text-info">
              Half day
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm">
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
            Dates
          </div>
          <div>
            {request.from_date} → {request.to_date}
          </div>
        </div>
        {request.reason && (
          <div className="text-sm">
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
              Reason
            </div>
            <p>{request.reason}</p>
          </div>
        )}
        <div className="flex gap-2 pt-2">
          <Button onClick={onApprove} variant="gold" size="sm" className="flex-1">
            <Check className="h-4 w-4" /> Approve
          </Button>
          <Button onClick={onReject} variant="outline" size="sm" className="flex-1">
            <X className="h-4 w-4" /> Reject
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
