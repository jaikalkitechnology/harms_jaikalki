import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus } from "lucide-react";

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
import { salesApi } from "@/lib/api/sales";
import { employeesApi } from "@/lib/api/employees";

export default function SalesTargetsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const today = new Date();
  const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
    .toISOString()
    .slice(0, 10);
  const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0)
    .toISOString()
    .slice(0, 10);

  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [periodType, setPeriodType] = useState("monthly");
  const [periodStart, setPeriodStart] = useState(monthStart);
  const [periodEnd, setPeriodEnd] = useState(monthEnd);
  const [targetAmount, setTargetAmount] = useState("");
  const [commissionPct, setCommissionPct] = useState("3");

  const { data: targets = [], isLoading } = useQuery({
    queryKey: ["sales-targets"],
    queryFn: () => salesApi.listTargets(),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });

  const create = useMutation({
    mutationFn: () =>
      salesApi.createTarget({
        employee_id: Number(employeeId),
        period_type: periodType,
        period_start: periodStart,
        period_end: periodEnd,
        target_amount: Number(targetAmount),
        commission_pct: Number(commissionPct),
      }),
    onSuccess: () => {
      toast.success("Target created");
      setShowForm(false);
      setEmployeeId("");
      setTargetAmount("");
      qc.invalidateQueries({ queryKey: ["sales-targets"] });
    },
    onError: () => toast.error("Could not create target"),
  });

  if (isLoading) return <LoadingScreen label="Loading targets…" />;

  const empById = new Map(employees.map((e) => [e.id, e]));

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Sales Targets
          </h1>
          <p className="text-sm text-brand-brown-light">
            Set monthly/quarterly targets and track commission accruals.
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
          <Plus className="size-4" />
          {showForm ? "Cancel" : "New target"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Assign target</CardTitle>
            <CardDescription>
              Achievement is auto-rolled when an order is marked delivered.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Employee *</Label>
              <select
                value={employeeId}
                onChange={(e) =>
                  setEmployeeId(e.target.value ? Number(e.target.value) : "")
                }
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">— Select —</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.employee_code} — {emp.first_name} {emp.last_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Period</Label>
              <select
                value={periodType}
                onChange={(e) => setPeriodType(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="yearly">Yearly</option>
              </select>
            </div>
            <div>
              <Label>Start</Label>
              <Input
                type="date"
                value={periodStart}
                onChange={(e) => setPeriodStart(e.target.value)}
              />
            </div>
            <div>
              <Label>End</Label>
              <Input
                type="date"
                value={periodEnd}
                onChange={(e) => setPeriodEnd(e.target.value)}
              />
            </div>
            <div>
              <Label>Target amount (₹)</Label>
              <Input
                type="number"
                value={targetAmount}
                onChange={(e) => setTargetAmount(e.target.value)}
              />
            </div>
            <div>
              <Label>Commission %</Label>
              <Input
                type="number"
                step="0.5"
                value={commissionPct}
                onChange={(e) => setCommissionPct(e.target.value)}
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                disabled={!employeeId || !targetAmount || create.isPending}
                onClick={() => create.mutate()}
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Employee</th>
                <th className="px-4 py-3">Period</th>
                <th className="px-4 py-3 text-right">Target</th>
                <th className="px-4 py-3 text-right">Achieved</th>
                <th className="px-4 py-3">Progress</th>
                <th className="px-4 py-3 text-right">Commission</th>
              </tr>
            </thead>
            <tbody>
              {targets.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No targets configured.
                  </td>
                </tr>
              ) : (
                targets.map((t) => {
                  const emp = empById.get(t.employee_id);
                  const target = Number(t.target_amount);
                  const achieved = Number(t.achieved_amount);
                  const pct = target > 0 ? (achieved / target) * 100 : 0;
                  const commission = (achieved * Number(t.commission_pct)) / 100;
                  const barColor =
                    pct >= 100
                      ? "bg-success"
                      : pct >= 70
                        ? "bg-brand-gold"
                        : "bg-info";
                  return (
                    <tr key={t.id} className="border-t border-brand-brown-50">
                      <td className="px-4 py-3 font-medium">
                        {emp
                          ? `${emp.employee_code} · ${emp.first_name} ${emp.last_name}`
                          : `Employee #${t.employee_id}`}
                      </td>
                      <td className="px-4 py-3 capitalize">
                        {t.period_type} · {t.period_start} → {t.period_end}
                      </td>
                      <td className="px-4 py-3 text-right">
                        ₹{target.toLocaleString("en-IN")}
                      </td>
                      <td className="px-4 py-3 text-right">
                        ₹{achieved.toLocaleString("en-IN")}
                      </td>
                      <td className="px-4 py-3 w-48">
                        <div className="h-2 rounded-full bg-brand-brown-50">
                          <div
                            className={`h-2 rounded-full ${barColor}`}
                            style={{
                              width: `${Math.min(pct, 100).toFixed(1)}%`,
                            }}
                          />
                        </div>
                        <div className="mt-1 text-xs text-brand-brown-light">
                          {pct.toFixed(1)}%
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        ₹{commission.toLocaleString("en-IN")}{" "}
                        <span className="text-xs text-brand-brown-light">
                          ({t.commission_pct}%)
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
