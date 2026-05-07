import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Check,
  ChevronLeft,
  ChevronRight,
  Info,
  Receipt,
  Search,
  X,
} from "lucide-react";

import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { payrollApi, type Reimbursement } from "@/lib/api/payroll";
import { employeesApi } from "@/lib/api/employees";
import { fmtIstDate } from "@/lib/datetime";

function inr(n: string) {
  return `₹${Math.round(Number(n)).toLocaleString("en-IN")}`;
}

const PAGE_SIZE = 12;

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  approved: "Approved",
  rejected: "Rejected",
  paid: "Paid",
};
const STATUS_COLOR: Record<string, string> = {
  pending: "bg-info/15 text-info",
  approved: "bg-success/15 text-success",
  rejected: "bg-error/15 text-error",
  paid: "bg-brand-gold/15 text-brand-gold-dark",
};

export default function ReimbursementsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [search, setSearch] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [page, setPage] = useState(1);

  const { data: list = [], isLoading } = useQuery({
    queryKey: [
      "reimbursements",
      statusFilter,
      employeeId,
      search,
      fromDate,
      toDate,
    ],
    queryFn: () =>
      payrollApi.listReimbursements({
        status: (statusFilter || undefined) as
          | "pending"
          | "approved"
          | "rejected"
          | "paid"
          | undefined,
        employee_id: employeeId === "" ? undefined : Number(employeeId),
        search: search || undefined,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        limit: 500,
      }),
  });

  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });
  const empById = useMemo(
    () => new Map(employees.map((e) => [e.id, e])),
    [employees],
  );

  const approve = useMutation({
    mutationFn: (id: number) => payrollApi.approveReimbursement(id),
    onSuccess: () => {
      toast.success("Reimbursement approved");
      queryClient.invalidateQueries({ queryKey: ["reimbursements"] });
      queryClient.invalidateQueries({ queryKey: ["reimbursements-pending"] });
    },
  });
  const reject = useMutation({
    mutationFn: (args: { id: number; reason: string }) =>
      payrollApi.rejectReimbursement(args.id, args.reason),
    onSuccess: () => {
      toast.success("Reimbursement rejected");
      queryClient.invalidateQueries({ queryKey: ["reimbursements"] });
      queryClient.invalidateQueries({ queryKey: ["reimbursements-pending"] });
    },
  });

  const counts = useMemo(() => {
    const c = { pending: 0, approved: 0, rejected: 0, paid: 0, total_amount: 0 };
    list.forEach((r) => {
      c[r.status as keyof typeof c] = (c[r.status as keyof typeof c] as number) + 1;
      if (r.status === "approved" || r.status === "paid") {
        c.total_amount += Number(r.amount);
      }
    });
    return c;
  }, [list]);

  const pageCount = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
  const pageRows = list.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (isLoading) return <LoadingScreen label="Loading reimbursements…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Phase 7 · Reimbursements
          </div>
          <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
            Claim <span className="display-em">ledger</span>
          </h2>
          <p className="mt-1 text-sm text-brand-brown-light">
            {list.length} claim{list.length === 1 ? "" : "s"} matching the
            current filters.
          </p>
        </div>
      </div>

      {/* Brief: how it lands on payslip */}
      <Card className="border-info/40 bg-info/5">
        <CardContent className="flex items-start gap-3 p-4">
          <Info className="size-5 text-info shrink-0 mt-0.5" />
          <div className="text-sm">
            <div className="font-semibold text-brand-brown-darker mb-1">
              How reimbursements affect salary
            </div>
            <ul className="space-y-1 text-brand-brown-light list-disc pl-4">
              <li>
                <span className="font-medium text-brand-brown-darker">Pending / Rejected</span>{" "}
                claims do <em>not</em> touch the payslip.
              </li>
              <li>
                <span className="font-medium text-success">Approved</span>{" "}
                claims are picked up by the next payroll run and{" "}
                <span className="font-medium">added to net pay as a non-taxable add-back</span> —
                they are not part of gross / taxable income.
              </li>
              <li>
                Once a payroll run includes them, status flips to{" "}
                <span className="font-medium text-brand-gold-dark">Paid</span>{" "}
                and the row links to <span className="font-mono">paid_in_run_id</span>.
              </li>
              <li>
                For the company books these are <em>employee expenses</em>{" "}
                (separate from CTC / employer cost), so they don't inflate
                gross or PF / ESIC bases.
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Status counters */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatTile label="Pending" value={counts.pending} color="text-info" />
        <StatTile label="Approved" value={counts.approved} color="text-success" />
        <StatTile label="Rejected" value={counts.rejected} color="text-error" />
        <StatTile label="Paid" value={counts.paid} color="text-brand-gold-dark" />
        <StatTile
          label="Approved + Paid total"
          value={`₹${Math.round(counts.total_amount).toLocaleString("en-IN")}`}
          color="text-brand-brown-darker"
        />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-5">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search description / category / reason…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved (not yet paid)</option>
            <option value="rejected">Rejected</option>
            <option value="paid">Paid</option>
          </select>
          <select
            value={employeeId}
            onChange={(e) => {
              setEmployeeId(e.target.value ? Number(e.target.value) : "");
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All employees</option>
            {employees.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.employee_code} — {emp.first_name} {emp.last_name}
              </option>
            ))}
          </select>
          <div className="flex gap-2">
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => {
                setFromDate(e.target.value);
                setPage(1);
              }}
              placeholder="From"
            />
            <Input
              type="date"
              value={toDate}
              onChange={(e) => {
                setToDate(e.target.value);
                setPage(1);
              }}
              placeholder="To"
            />
          </div>
        </CardContent>
      </Card>

      {pageRows.length === 0 ? (
        <Card>
          <CardContent className="py-12 flex flex-col items-center gap-3 text-brand-brown-light">
            <Receipt className="h-10 w-10" />
            <div>No claims match these filters.</div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-brand-brown-50/40 text-left">
                <tr>
                  <th className="px-4 py-3">Employee</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Bill date</th>
                  <th className="px-4 py-3 text-right">Amount</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Run #</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {pageRows.map((r) => {
                  const emp = empById.get(r.employee_id);
                  return (
                    <ReimRow
                      key={r.id}
                      r={r}
                      empLabel={
                        emp
                          ? `${emp.employee_code} · ${emp.first_name} ${emp.last_name}`
                          : `Employee #${r.employee_id}`
                      }
                      onApprove={() => approve.mutate(r.id)}
                      onReject={() => {
                        const reason = prompt("Rejection reason?", "");
                        if (reason === null) return;
                        reject.mutate({ id: r.id, reason: reason || "Rejected" });
                      }}
                      busy={approve.isPending || reject.isPending}
                    />
                  );
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      {pageCount > 1 && (
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <div className="text-sm text-brand-brown-light">
            Page {page} of {pageCount}
          </div>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= pageCount}
            onClick={() => setPage(page + 1)}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}
    </div>
  );
}

function ReimRow({
  r,
  empLabel,
  onApprove,
  onReject,
  busy,
}: {
  r: Reimbursement;
  empLabel: string;
  onApprove: () => void;
  onReject: () => void;
  busy: boolean;
}) {
  return (
    <tr className="border-t border-brand-brown-50">
      <td className="px-4 py-3 font-medium">{empLabel}</td>
      <td className="px-4 py-3 capitalize">{r.category}</td>
      <td className="px-4 py-3">{fmtIstDate(r.bill_date)}</td>
      <td className="px-4 py-3 text-right font-semibold">{inr(r.amount)}</td>
      <td className="px-4 py-3 text-brand-brown-light max-w-[260px] truncate">
        {r.description ?? "—"}
        {r.bill_url && (
          <>
            {" · "}
            <a
              href={r.bill_url}
              target="_blank"
              rel="noreferrer"
              className="text-brand-gold-dark hover:underline"
            >
              bill
            </a>
          </>
        )}
        {r.status === "rejected" && r.rejection_reason && (
          <div className="text-xs text-error">
            Reason: {r.rejection_reason}
          </div>
        )}
      </td>
      <td className="px-4 py-3">
        <span
          className={`rounded-full px-2 py-1 text-xs ${STATUS_COLOR[r.status] ?? ""}`}
        >
          {STATUS_LABELS[r.status] ?? r.status}
        </span>
      </td>
      <td className="px-4 py-3 text-xs text-brand-brown-light">
        {r.paid_in_run_id ? `#${r.paid_in_run_id}` : "—"}
      </td>
      <td className="px-4 py-3 text-right whitespace-nowrap">
        {r.status === "pending" && (
          <>
            <Button
              size="sm"
              variant="outline"
              className="border-success/40 text-success hover:bg-success/10"
              onClick={onApprove}
              disabled={busy}
              title="Approve"
            >
              <Check className="size-3" />
            </Button>{" "}
            <Button
              size="sm"
              variant="outline"
              className="border-error/40 text-error hover:bg-error/10"
              onClick={onReject}
              disabled={busy}
              title="Reject"
            >
              <X className="size-3" />
            </Button>
          </>
        )}
      </td>
    </tr>
  );
}

function StatTile({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="text-xs text-brand-brown-light">{label}</div>
        <div
          className={`text-2xl font-semibold ${color ?? "text-brand-brown-darker"}`}
        >
          {value}
        </div>
      </CardContent>
    </Card>
  );
}
