import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  BadgeCheck,
  Download,
  FileSpreadsheet,
  Landmark,
  Lock,
  Play,
  RotateCcw,
  Trash2,
} from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { payrollApi, type PayrollRun } from "@/lib/api/payroll";
import { employeesApi } from "@/lib/api/employees";
import { attendanceCyclesApi } from "@/lib/api/employeeProfile";
import { API_BASE_URL } from "@/lib/constants";
import { apiClient } from "@/lib/api/client";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function inr(n: string | number): string {
  return `₹${Math.round(Number(n)).toLocaleString("en-IN")}`;
}

const STATUS_TONE: Record<string, string> = {
  draft: "bg-brand-brown-50 text-brand-brown-darker",
  processed: "bg-info/15 text-info",
  finalized: "bg-brand-gold/15 text-brand-gold-dark",
  reverted: "bg-error/15 text-error",
};

async function download(url: string, filename: string) {
  try {
    const res = await apiClient.get(url.replace(API_BASE_URL, ""), {
      responseType: "blob",
    });
    const blob = new Blob([res.data]);
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(a.href);
  } catch {
    toast.error("Download failed");
  }
}

export default function PayrollRunsPage() {
  const qc = useQueryClient();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [cycle, setCycle] = useState<number>(0); // 0 = per-employee
  const [selected, setSelected] = useState<PayrollRun | null>(null);

  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });
  const empById = useMemo(
    () => new Map(employees.map((e) => [e.id, e])),
    [employees],
  );

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ["payroll-runs"],
    queryFn: payrollApi.listRuns,
  });
  const { data: cycles = [] } = useQuery({
    queryKey: ["attendance-cycles"],
    queryFn: () => attendanceCyclesApi.list(),
  });
  const { data: detail } = useQuery({
    queryKey: ["payroll-run", selected?.id],
    queryFn: () => payrollApi.getRun(selected!.id),
    enabled: !!selected,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["payroll-runs"] });
    qc.invalidateQueries({ queryKey: ["payroll-run"] });
  };
  const errMsg = (err: unknown, fallback: string) =>
    (err as { response?: { data?: { detail?: string } } })?.response?.data
      ?.detail ?? fallback;

  const runMut = useMutation({
    mutationFn: () =>
      payrollApi.runPayroll(year, month, cycle === 0 ? null : cycle),
    onSuccess: (run) => {
      toast.success(`${MONTHS[run.month - 1]} ${run.year} processed`);
      invalidate();
      setSelected(run);
    },
    onError: (e) => toast.error(errMsg(e, "Could not run payroll")),
  });
  const finalizeMut = useMutation({
    mutationFn: (id: number) => payrollApi.finalize(id),
    onSuccess: () => {
      toast.success("Payroll finalized");
      invalidate();
    },
    onError: (e) => toast.error(errMsg(e, "Could not finalize")),
  });
  const revertMut = useMutation({
    mutationFn: (id: number) => payrollApi.revert(id),
    onSuccess: () => {
      toast.success("Payroll reverted");
      invalidate();
      setSelected(null);
    },
    onError: (e) => toast.error(errMsg(e, "Could not revert")),
  });
  const deleteMut = useMutation({
    mutationFn: (id: number) => payrollApi.deleteRun(id),
    onSuccess: () => {
      toast.success("Run deleted");
      invalidate();
      setSelected(null);
    },
    onError: (e) => toast.error(errMsg(e, "Could not delete")),
  });
  const disburseMut = useMutation({
    mutationFn: (id: number) => payrollApi.disburse(id),
    onSuccess: () => {
      toast.success("Salary marked distributed");
      invalidate();
    },
    onError: (e) => toast.error(errMsg(e, "Could not mark distributed")),
  });
  const undoDisburseMut = useMutation({
    mutationFn: (id: number) => payrollApi.undoDisburse(id),
    onSuccess: () => {
      toast.success("Disbursement undone");
      invalidate();
    },
    onError: (e) => toast.error(errMsg(e, "Could not undo")),
  });

  if (isLoading) return <LoadingScreen label="Loading payroll…" />;

  const cycleLabel = (n: number) =>
    n === 1
      ? "Calendar month"
      : cycles.find((c) => c.start_day === n)?.name ?? `Day ${n}`;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Payroll
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          Payroll <span className="display-em">runs</span>
        </h2>
        <p className="mt-1 text-sm text-brand-brown-light">
          Attendance-based salary processing. {runs.length} run
          {runs.length === 1 ? "" : "s"} on record.
        </p>
      </div>

      {/* ── Run a new payroll ── */}
      <Card>
        <CardHeader>
          <CardTitle>Run payroll</CardTitle>
          <CardDescription>
            Net pay is scaled by attendance for the chosen cycle —
            unpaid leave &amp; absents become loss-of-pay.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1.5">
              <Label>Month</Label>
              <select
                value={month}
                onChange={(e) => setMonth(Number(e.target.value))}
                className="flex h-10 rounded-md border border-input bg-card px-3 text-sm"
              >
                {MONTHS.map((m, i) => (
                  <option key={m} value={i + 1}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label>Year</Label>
              <select
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
                className="flex h-10 rounded-md border border-input bg-card px-3 text-sm"
              >
                {[year - 1, year, year + 1].map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label>Attendance cycle</Label>
              <select
                value={cycle}
                onChange={(e) => setCycle(Number(e.target.value))}
                className="flex h-10 rounded-md border border-input bg-card px-3 text-sm min-w-[16rem]"
              >
                <option value={0}>Each employee's own cycle</option>
                <option value={1}>1st → last day (calendar month)</option>
                {cycles
                  .filter((c) => c.start_day !== 1)
                  .map((c) => (
                    <option key={c.id} value={c.start_day}>
                      {c.name}
                    </option>
                  ))}
              </select>
            </div>
            <Button
              onClick={() => runMut.mutate()}
              disabled={runMut.isPending}
              variant="gold"
              className="gap-2"
            >
              <Play className="h-4 w-4" />
              {runMut.isPending ? "Processing…" : "Run payroll"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* ── Runs list ── */}
      <Card>
        <CardHeader>
          <CardTitle>All runs</CardTitle>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm min-w-[900px]">
            <thead className="text-left text-brand-brown-light bg-brand-brown-50">
              <tr>
                <th className="py-2 px-4">Period</th>
                <th>Cycle</th>
                <th>Status</th>
                <th>Employees</th>
                <th>Gross</th>
                <th>Net</th>
                <th>Employer cost</th>
                <th className="px-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr
                  key={r.id}
                  className={`border-t border-brand-brown-50 hover:bg-brand-brown-50/30 cursor-pointer ${
                    selected?.id === r.id ? "bg-brand-gold/5" : ""
                  }`}
                  onClick={() => setSelected(r)}
                >
                  <td className="py-2 px-4 font-medium">
                    {MONTHS[r.month - 1]} {r.year}
                  </td>
                  <td className="text-xs text-brand-brown-light">
                    {cycleLabel(r.cycle_start_day)}
                  </td>
                  <td>
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded ${
                          STATUS_TONE[r.status] ?? ""
                        }`}
                      >
                        {r.status}
                      </span>
                      {r.disbursed && (
                        <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-success/15 text-success">
                          paid
                        </span>
                      )}
                    </div>
                  </td>
                  <td>{r.total_employees}</td>
                  <td>{inr(r.total_gross)}</td>
                  <td className="font-semibold text-brand-gold-dark">
                    {inr(r.total_net)}
                  </td>
                  <td>{inr(r.total_employer_cost)}</td>
                  <td
                    className="px-4 py-2"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="flex flex-wrap gap-1.5">
                      {r.status === "processed" && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 gap-1"
                          disabled={finalizeMut.isPending}
                          onClick={() => finalizeMut.mutate(r.id)}
                        >
                          <Lock className="h-3.5 w-3.5" /> Finalize
                        </Button>
                      )}
                      {r.status !== "finalized" &&
                        r.status !== "reverted" && (
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-8 gap-1"
                            disabled={revertMut.isPending}
                            onClick={() => revertMut.mutate(r.id)}
                          >
                            <RotateCcw className="h-3.5 w-3.5" /> Revert
                          </Button>
                        )}
                      {r.status === "finalized" && !r.disbursed && (
                        <Button
                          size="sm"
                          className="h-8 gap-1"
                          disabled={disburseMut.isPending}
                          onClick={() => disburseMut.mutate(r.id)}
                        >
                          <BadgeCheck className="h-3.5 w-3.5" />
                          Mark distributed
                        </Button>
                      )}
                      {r.disbursed && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 gap-1"
                          disabled={undoDisburseMut.isPending}
                          onClick={() => undoDisburseMut.mutate(r.id)}
                        >
                          <RotateCcw className="h-3.5 w-3.5" /> Undo paid
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 gap-1"
                        onClick={() =>
                          download(
                            payrollApi.runCsvUrl(r.id),
                            `payroll-${r.year}-${String(r.month).padStart(2, "0")}.csv`,
                          )
                        }
                      >
                        <FileSpreadsheet className="h-3.5 w-3.5" /> CSV
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 gap-1"
                        onClick={() =>
                          download(
                            payrollApi.pfChallanUrl(r.id),
                            `pf-ecr-${r.year}-${String(r.month).padStart(2, "0")}.txt`,
                          )
                        }
                      >
                        <Landmark className="h-3.5 w-3.5" /> PF challan
                      </Button>
                      {!r.disbursed && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 gap-1 text-destructive"
                          disabled={deleteMut.isPending}
                          onClick={() => {
                            if (
                              confirm(
                                `Delete the ${MONTHS[r.month - 1]} ${r.year} run? Payslips are removed and paid reimbursements released.`,
                              )
                            )
                              deleteMut.mutate(r.id);
                          }}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {runs.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    className="py-10 text-center text-brand-brown-light"
                  >
                    No payroll runs yet. Pick a period above and run one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* ── Run detail ── */}
      {selected && detail && (
        <Card>
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <CardTitle>
                {MONTHS[detail.run.month - 1]} {detail.run.year} ·{" "}
                {detail.payslips.length} payslips
              </CardTitle>
              <CardDescription>
                Cycle: {cycleLabel(detail.run.cycle_start_day)}
                {detail.run.disbursed && " · salary distributed"}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() =>
                  download(
                    payrollApi.runCsvUrl(detail.run.id),
                    `payroll-${detail.run.year}-${String(
                      detail.run.month,
                    ).padStart(2, "0")}.csv`,
                  )
                }
              >
                <Download className="h-4 w-4" /> Export
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0 overflow-x-auto">
            <table className="w-full text-sm min-w-[820px]">
              <thead className="text-left text-brand-brown-light bg-brand-brown-50">
                <tr>
                  <th className="py-2 px-4">Employee</th>
                  <th>Days (paid / work)</th>
                  <th>Gross</th>
                  <th>Deductions</th>
                  <th>Net</th>
                  <th className="px-4">PDF</th>
                </tr>
              </thead>
              <tbody>
                {detail.payslips.map((p) => {
                  const emp = empById.get(p.employee_id);
                  return (
                  <tr
                    key={p.id}
                    className="border-t border-brand-brown-50"
                  >
                    <td className="py-2 px-4 text-xs">
                      {emp ? (
                        <>
                          <span className="font-semibold text-brand-brown-darker">
                            {emp.first_name} {emp.last_name}
                          </span>
                          <span className="ml-1 font-mono text-brand-brown-light">
                            · {emp.employee_code}
                          </span>
                        </>
                      ) : (
                        <span className="font-mono">#{p.employee_id}</span>
                      )}
                      {p.is_final_settlement && (
                        <span
                          className={
                            "ml-2 rounded px-1.5 py-0.5 text-[9px] font-mono uppercase tracking-[0.15em] " +
                            (p.on_hold
                              ? "bg-error/15 text-error"
                              : "bg-success/15 text-success")
                          }
                          title={
                            p.on_hold
                              ? "Final salary — held until the resignation is marked settled. Excluded from the bank file and the employee's app."
                              : "Final salary — released after settlement."
                          }
                        >
                          {p.on_hold ? "Final · On hold" : "Final · Released"}
                        </span>
                      )}
                    </td>
                    <td className="text-xs">
                      <span className="font-semibold text-brand-brown-darker">
                        {Number(p.days_paid).toFixed(1)}
                      </span>{" "}
                      / {Number(p.working_days).toFixed(0)}
                      {Number(p.days_paid_leave) > 0 && (
                        <span className="ml-1 text-brand-gold-dark">
                          · Lv {Number(p.days_paid_leave).toFixed(1)}
                        </span>
                      )}
                      {Number(p.days_unpaid_leave) > 0 && (
                        <span className="ml-1 text-error">
                          · LWP {Number(p.days_unpaid_leave).toFixed(1)}
                        </span>
                      )}
                      {Number(p.days_absent) > 0 && (
                        <span className="ml-1 text-error">
                          · Abs {Number(p.days_absent).toFixed(1)}
                        </span>
                      )}
                    </td>
                    <td>{inr(p.gross)}</td>
                    <td className="text-error">
                      - {inr(p.total_deductions)}
                    </td>
                    <td className="font-semibold text-brand-gold-dark">
                      {inr(p.net_pay)}
                    </td>
                    <td className="px-4">
                      <a
                        href={payrollApi.payslipPdfUrl(p.id)}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs font-mono uppercase tracking-[0.2em] text-brand-gold-dark hover:text-brand-brown-darker"
                      >
                        PDF →
                      </a>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
