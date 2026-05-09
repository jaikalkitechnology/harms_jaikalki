import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Lock, Play, RotateCcw } from "lucide-react";

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
import { payrollApi, type PayrollRun } from "@/lib/api/payroll";

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function inr(n: string | number): string {
  return `₹${Math.round(Number(n)).toLocaleString("en-IN")}`;
}

export default function PayrollRunsPage() {
  const queryClient = useQueryClient();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [selected, setSelected] = useState<PayrollRun | null>(null);

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ["payroll-runs"],
    queryFn: payrollApi.listRuns,
  });

  const { data: detail } = useQuery({
    queryKey: ["payroll-run", selected?.id],
    queryFn: () => payrollApi.getRun(selected!.id),
    enabled: !!selected,
  });

  const runMut = useMutation({
    mutationFn: () => payrollApi.runPayroll(year, month),
    onSuccess: (run) => {
      toast.success(`Run for ${MONTHS[run.month - 1]} ${run.year} processed`);
      queryClient.invalidateQueries({ queryKey: ["payroll-runs"] });
      setSelected(run);
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not run payroll";
      toast.error(detail);
    },
  });

  const finalizeMut = useMutation({
    mutationFn: (id: number) => payrollApi.finalize(id),
    onSuccess: () => {
      toast.success("Payroll finalized");
      queryClient.invalidateQueries({ queryKey: ["payroll-runs"] });
      queryClient.invalidateQueries({ queryKey: ["payroll-run"] });
    },
  });
  const revertMut = useMutation({
    mutationFn: (id: number) => payrollApi.revert(id),
    onSuccess: () => {
      toast.success("Payroll reverted");
      queryClient.invalidateQueries({ queryKey: ["payroll-runs"] });
      setSelected(null);
    },
  });

  if (isLoading) return <LoadingScreen label="Loading payroll runs…" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Phase 7 · Payroll
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          Payroll <span className="display-em">runs</span>
        </h2>
        <p className="mt-1 text-sm text-brand-brown-light">
          {runs.length} run{runs.length === 1 ? "" : "s"} on record. Process
          a month, review payslips, then finalize to lock.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Run a new payroll</CardTitle>
          <CardDescription>
            Re-running an existing draft replaces its payslips. Finalized runs
            are locked.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="year">Year</Label>
              <Input
                id="year"
                type="number"
                value={year}
                onChange={(e) => setYear(Number(e.target.value))}
                className="w-28"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="month">Month</Label>
              <select
                id="month"
                value={month}
                onChange={(e) => setMonth(Number(e.target.value))}
                className="flex h-10 w-44 rounded-md border border-input bg-card px-3 py-2 text-sm"
              >
                {MONTHS.map((m, i) => (
                  <option key={m} value={i + 1}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
            <Button onClick={() => runMut.mutate()} disabled={runMut.isPending}>
              <Play className="h-4 w-4" /> Run payroll
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid lg:grid-cols-[18rem_1fr] gap-4">
        <Card>
          <CardHeader>
            <CardTitle>History</CardTitle>
            <CardDescription>{runs.length} runs</CardDescription>
          </CardHeader>
          <CardContent className="space-y-1">
            {runs.length === 0 ? (
              <p className="text-sm text-brand-brown-light">No runs yet.</p>
            ) : (
              runs.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSelected(r)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selected?.id === r.id
                      ? "bg-brand-gold/10 border-brand-gold/40"
                      : "bg-card border-brand-brown-100 hover:border-brand-gold/30"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="font-medium">
                      {MONTHS[r.month - 1]} {r.year}
                    </div>
                    <StatusPill status={r.status} />
                  </div>
                  <div className="text-xs text-brand-brown-light mt-1">
                    {r.total_employees} employees · {inr(r.total_net)} net
                  </div>
                </button>
              ))
            )}
          </CardContent>
        </Card>

        {selected && detail && (
          <Card>
            <CardHeader className="flex flex-row items-start justify-between">
              <div>
                <CardTitle>
                  {MONTHS[detail.run.month - 1]} {detail.run.year}
                </CardTitle>
                <CardDescription>
                  {detail.run.total_employees} employees ·{" "}
                  {inr(detail.run.total_gross)} gross ·{" "}
                  {inr(detail.run.total_employer_cost)} employer cost
                </CardDescription>
              </div>
              <div className="flex gap-2">
                {detail.run.status === "processed" && (
                  <Button
                    size="sm"
                    onClick={() => finalizeMut.mutate(detail.run.id)}
                  >
                    <Lock className="h-4 w-4" /> Finalize
                  </Button>
                )}
                {detail.run.status !== "finalized" && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => revertMut.mutate(detail.run.id)}
                  >
                    <RotateCcw className="h-4 w-4" /> Revert
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="rounded-xl border border-brand-brown-100 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-brand-brown-50/60">
                    <tr>
                      {["Employee", "Days", "Gross", "Deductions", "Net Pay", ""].map(
                        (h) => (
                          <th
                            key={h}
                            className="text-left px-4 py-2 text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light"
                          >
                            {h}
                          </th>
                        ),
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {detail.payslips.map((p) => (
                      <tr key={p.id} className="border-t border-brand-brown-100/60">
                        <td className="px-4 py-2 font-mono text-xs">
                          #{p.employee_id}
                        </td>
                        <td className="px-4 py-2 text-xs text-brand-brown-light whitespace-nowrap">
                          <span className="font-semibold text-brand-brown-darker">
                            {Number(p.days_paid).toFixed(1)}
                          </span>
                          {" / "}
                          {Number(p.working_days).toFixed(0)}
                          {Number(p.days_unpaid_leave) > 0 && (
                            <span className="ml-1 text-error">
                              · LWP {Number(p.days_unpaid_leave).toFixed(1)}
                              {Number(p.days_sandwich) > 0 &&
                                ` (${Number(p.days_sandwich).toFixed(1)} sw)`}
                            </span>
                          )}
                          {Number(p.days_absent) > 0 && (
                            <span className="ml-1 text-error">
                              · Abs {Number(p.days_absent).toFixed(1)}
                            </span>
                          )}
                          {Number(p.days_paid_leave) > 0 && (
                            <span className="ml-1 text-success">
                              · PL {Number(p.days_paid_leave).toFixed(1)}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2">{inr(p.gross)}</td>
                        <td className="px-4 py-2 text-error">
                          - {inr(p.total_deductions)}
                        </td>
                        <td className="px-4 py-2 font-semibold text-brand-gold-dark">
                          {inr(p.net_pay)}
                        </td>
                        <td className="px-4 py-2 text-right">
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
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: PayrollRun["status"] }) {
  const map = {
    draft: "bg-brand-brown-100 text-brand-brown-darker",
    processed: "bg-info/15 text-info",
    finalized: "bg-success/15 text-success",
    reverted: "bg-error/15 text-error",
  };
  return (
    <span
      className={`text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-0.5 rounded ${map[status]}`}
    >
      {status}
    </span>
  );
}
