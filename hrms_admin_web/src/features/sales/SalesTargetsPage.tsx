import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil, Plus, RefreshCw, Search, Trash2, X } from "lucide-react";

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
import {
  TARGET_METRICS,
  fmtTargetValue,
  salesApi,
  type SalesTarget,
  type TargetMetric,
} from "@/lib/api/sales";
import { employeesApi } from "@/lib/api/employees";

type EditState = {
  id: number;
  period_type: "monthly" | "quarterly" | "yearly";
  period_start: string;
  period_end: string;
  target_amount: string;
  commission_pct: string;
  notes: string;
  metric: TargetMetric;
};

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
  const [metric, setMetric] = useState<TargetMetric>("sales_amount");
  const isMoney = metric === "sales_amount";

  // Filters
  const [searchTerm, setSearchTerm] = useState("");
  const [filterPeriodType, setFilterPeriodType] = useState("");
  const [filterFrom, setFilterFrom] = useState("");
  const [filterTo, setFilterTo] = useState("");

  // Edit state
  const [editing, setEditing] = useState<EditState | null>(null);

  const { data: targets = [], isLoading, isFetching } = useQuery({
    queryKey: [
      "sales-targets",
      filterPeriodType,
      filterFrom,
      filterTo,
    ],
    queryFn: () =>
      salesApi.listTargets({
        period_type: filterPeriodType || undefined,
        from_date: filterFrom || undefined,
        to_date: filterTo || undefined,
      }),
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
        commission_pct: isMoney ? Number(commissionPct) : 0,
        metric,
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

  const update = useMutation({
    mutationFn: (e: EditState) =>
      salesApi.updateTarget(e.id, {
        period_type: e.period_type,
        period_start: e.period_start,
        period_end: e.period_end,
        target_amount: Number(e.target_amount),
        commission_pct: e.metric === "sales_amount" ? Number(e.commission_pct) : 0,
        notes: e.notes || null,
        metric: e.metric,
      }),
    onSuccess: () => {
      toast.success("Target updated");
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["sales-targets"] });
    },
    onError: () => toast.error("Could not update target"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => salesApi.deleteTarget(id),
    onSuccess: () => {
      toast.success("Target deleted");
      qc.invalidateQueries({ queryKey: ["sales-targets"] });
    },
    onError: () => toast.error("Could not delete target"),
  });

  const recompute = useMutation({
    mutationFn: (id: number) => salesApi.recomputeTarget(id),
    onSuccess: () => {
      toast.success("Progress refreshed");
      qc.invalidateQueries({ queryKey: ["sales-targets"] });
    },
    onError: () => toast.error("Could not refresh progress"),
  });

  const refreshAll = useMutation({
    mutationFn: async (ids: number[]) => {
      for (const id of ids) {
        try {
          await salesApi.recomputeTarget(id);
        } catch {
          /* keep going */
        }
      }
    },
    onSuccess: () => {
      toast.success("All targets refreshed");
      qc.invalidateQueries({ queryKey: ["sales-targets"] });
    },
  });

  const empById = useMemo(
    () => new Map(employees.map((e) => [e.id, e])),
    [employees],
  );

  const filtered = useMemo(() => {
    if (!searchTerm.trim()) return targets;
    const q = searchTerm.trim().toLowerCase();
    return targets.filter((t) => {
      const emp = empById.get(t.employee_id);
      if (!emp) return String(t.employee_id).includes(q);
      const hay = `${emp.employee_code} ${emp.first_name} ${emp.last_name}`
        .toLowerCase();
      return hay.includes(q);
    });
  }, [targets, searchTerm, empById]);

  if (isLoading) return <LoadingScreen label="Loading targets…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Sales Targets
          </h1>
          <p className="text-sm text-brand-brown-light">
            Filter, edit, and refresh achievement directly from pipeline
            records.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refreshAll.mutate(filtered.map((t) => t.id))}
            disabled={refreshAll.isPending || filtered.length === 0}
            className="gap-2"
          >
            <RefreshCw
              className={`size-4 ${refreshAll.isPending ? "animate-spin" : ""}`}
            />
            Refresh all
          </Button>
          <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
            <Plus className="size-4" />
            {showForm ? "Cancel" : "New target"}
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search employee…"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          <select
            value={filterPeriodType}
            onChange={(e) => setFilterPeriodType(e.target.value)}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">All periods</option>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </select>
          <Input
            type="date"
            value={filterFrom}
            onChange={(e) => setFilterFrom(e.target.value)}
            placeholder="From"
          />
          <Input
            type="date"
            value={filterTo}
            onChange={(e) => setFilterTo(e.target.value)}
            placeholder="To"
          />
        </CardContent>
      </Card>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Assign target</CardTitle>
            <CardDescription>
              Achievement is rolled from pipeline orders + won leads.
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
              <Label>What is counted</Label>
              <select
                value={metric}
                onChange={(e) => setMetric(e.target.value as TargetMetric)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {TARGET_METRICS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-[11px] text-brand-brown-light">
                Progress updates on its own as the work is logged.
              </p>
            </div>
            <div>
              <Label>
                {isMoney ? "Target amount (₹)" : `Target (number of ${TARGET_METRICS.find((m) => m.value === metric)?.unit})`}
              </Label>
              <Input
                type="number"
                value={targetAmount}
                onChange={(e) => setTargetAmount(e.target.value)}
              />
            </div>
            {isMoney && (
              <div>
                <Label>Commission %</Label>
                <Input
                  type="number"
                  step="0.5"
                  value={commissionPct}
                  onChange={(e) => setCommissionPct(e.target.value)}
                />
              </div>
            )}
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
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Employee</th>
                <th className="px-4 py-3">Period</th>
                <th className="px-4 py-3 text-right">Target</th>
                <th className="px-4 py-3 text-right">Achieved</th>
                <th className="px-4 py-3 w-56">Progress</th>
                <th className="px-4 py-3 text-right">Commission</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    {isFetching ? "Loading…" : "No targets match these filters."}
                  </td>
                </tr>
              ) : (
                filtered.map((t) => (
                  <TargetRow
                    key={t.id}
                    target={t}
                    empLabel={(() => {
                      const emp = empById.get(t.employee_id);
                      return emp
                        ? `${emp.employee_code} · ${emp.first_name} ${emp.last_name}`
                        : `Employee #${t.employee_id}`;
                    })()}
                    onEdit={() =>
                      setEditing({
                        id: t.id,
                        period_type: t.period_type,
                        period_start: t.period_start,
                        period_end: t.period_end,
                        target_amount: t.target_amount,
                        commission_pct: t.commission_pct,
                        metric: t.metric ?? "sales_amount",
                        notes: t.notes ?? "",
                      })
                    }
                    onDelete={() => {
                      if (confirm("Delete this target?")) remove.mutate(t.id);
                    }}
                    onRefresh={() => recompute.mutate(t.id)}
                    isRefreshing={
                      recompute.isPending && recompute.variables === t.id
                    }
                  />
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {editing && (
        <EditTargetModal
          edit={editing}
          onChange={setEditing}
          onClose={() => setEditing(null)}
          onSave={() => update.mutate(editing)}
          saving={update.isPending}
        />
      )}
    </div>
  );
}

function TargetRow({
  target,
  empLabel,
  onEdit,
  onDelete,
  onRefresh,
  isRefreshing,
}: {
  target: SalesTarget;
  empLabel: string;
  onEdit: () => void;
  onDelete: () => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}) {
  const targetAmt = Number(target.target_amount);
  const achieved = Number(target.achieved_amount);
  const pct =
    typeof target.achievement_pct === "number"
      ? target.achievement_pct
      : targetAmt > 0
        ? (achieved / targetAmt) * 100
        : 0;
  const isMoney = (target.metric ?? "sales_amount") === "sales_amount";
  const commission = isMoney ? (achieved * Number(target.commission_pct)) / 100 : 0;
  const barColor =
    pct >= 100 ? "bg-success" : pct >= 70 ? "bg-brand-gold" : "bg-info";
  return (
    <tr className="border-t border-brand-brown-50">
      <td className="px-4 py-3 font-medium">{empLabel}</td>
      <td className="px-4 py-3 capitalize">
        {target.period_type} · {target.period_start} → {target.period_end}
        <div className="text-xs normal-case text-brand-brown-light">
          {TARGET_METRICS.find((m) => m.value === (target.metric ?? "sales_amount"))?.label}
        </div>
      </td>
      <td className="px-4 py-3 text-right">
        {fmtTargetValue(target.metric, targetAmt)}
      </td>
      <td className="px-4 py-3 text-right">
        {fmtTargetValue(target.metric, achieved)}
      </td>
      <td className="px-4 py-3">
        <div className="h-2 rounded-full bg-brand-brown-50">
          <div
            className={`h-2 rounded-full ${barColor}`}
            style={{ width: `${Math.min(pct, 100).toFixed(1)}%` }}
          />
        </div>
        <div className="mt-1 text-xs text-brand-brown-light">
          {pct.toFixed(1)}%
        </div>
      </td>
      <td className="px-4 py-3 text-right">
        {isMoney ? (
          <>
            ₹{commission.toLocaleString("en-IN")}{" "}
            <span className="text-xs text-brand-brown-light">
              ({target.commission_pct}%)
            </span>
          </>
        ) : (
          <span className="text-brand-brown-light">—</span>
        )}
      </td>
      <td className="px-4 py-3 text-right">
        <div className="inline-flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            title="Refresh from pipeline"
            onClick={onRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw
              className={`size-4 ${isRefreshing ? "animate-spin" : ""}`}
            />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            title="Edit"
            onClick={onEdit}
          >
            <Pencil className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            title="Delete"
            onClick={onDelete}
          >
            <Trash2 className="size-4 text-destructive" />
          </Button>
        </div>
      </td>
    </tr>
  );
}

function EditTargetModal({
  edit,
  onChange,
  onClose,
  onSave,
  saving,
}: {
  edit: EditState;
  onChange: (e: EditState) => void;
  onClose: () => void;
  onSave: () => void;
  saving: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Edit target</CardTitle>
            <CardDescription>Adjust period, value, or commission.</CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>Period</Label>
            <select
              value={edit.period_type}
              onChange={(e) =>
                onChange({
                  ...edit,
                  period_type: e.target.value as EditState["period_type"],
                })
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="monthly">Monthly</option>
              <option value="quarterly">Quarterly</option>
              <option value="yearly">Yearly</option>
            </select>
          </div>
          <div />
          <div>
            <Label>Start</Label>
            <Input
              type="date"
              value={edit.period_start}
              onChange={(e) =>
                onChange({ ...edit, period_start: e.target.value })
              }
            />
          </div>
          <div>
            <Label>End</Label>
            <Input
              type="date"
              value={edit.period_end}
              onChange={(e) =>
                onChange({ ...edit, period_end: e.target.value })
              }
            />
          </div>
          <div>
            <Label>What is counted</Label>
            <select
              value={edit.metric}
              onChange={(e) => onChange({ ...edit, metric: e.target.value as TargetMetric })}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {TARGET_METRICS.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>{edit.metric === "sales_amount" ? "Target amount (₹)" : "Target (number)"}</Label>
            <Input
              type="number"
              value={edit.target_amount}
              onChange={(e) =>
                onChange({ ...edit, target_amount: e.target.value })
              }
            />
          </div>
          {edit.metric === "sales_amount" && (
            <div>
              <Label>Commission %</Label>
              <Input
                type="number"
                step="0.5"
                value={edit.commission_pct}
                onChange={(e) =>
                  onChange({ ...edit, commission_pct: e.target.value })
                }
              />
            </div>
          )}
          <div className="md:col-span-2">
            <Label>Notes</Label>
            <Input
              value={edit.notes}
              onChange={(e) => onChange({ ...edit, notes: e.target.value })}
            />
          </div>
          <div className="md:col-span-2 flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button disabled={saving} onClick={onSave}>
              Save
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
