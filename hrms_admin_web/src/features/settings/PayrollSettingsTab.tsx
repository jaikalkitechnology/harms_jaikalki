import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { BarChart3, Lock, Pencil, Plus, Save, Trash2, X } from "lucide-react";

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
import {
  pfCeilingApi,
  type DivisionBasis,
  type PfCeiling,
  type PfCeilingInput,
  type PfMidMonthMode,
} from "@/lib/api/payroll";

const inr = (v: string | number) =>
  `₹${Number(v).toLocaleString("en-IN", { maximumFractionDigits: 2 })}`;

const MODE_LABEL: Record<PfMidMonthMode, string> = {
  day_weighted: "Pro-rata by date",
  whole_month: "Whole month at new cap",
  next_month: "From next wage month",
};

const STATUS_TONE: Record<string, string> = {
  active: "bg-success/15 text-success",
  scheduled: "bg-info/15 text-info",
  past: "bg-brand-brown-50 text-brand-brown-light",
};

function errDetail(e: unknown, fallback: string): string {
  return (
    (e as { response?: { data?: { detail?: string } } })?.response?.data
      ?.detail ?? fallback
  );
}

export function PayrollSettingsTab() {
  return (
    <div className="space-y-6">
      <DivisorCard />
      <PfCeilingCard />
    </div>
  );
}

// ── Payslip divisor ───────────────────────────────────────────────────
function DivisorCard() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["payroll-policy"],
    queryFn: pfCeilingApi.getPolicy,
  });
  const [basis, setBasis] = useState<DivisionBasis>("calendar_days");
  useEffect(() => {
    if (data) setBasis(data.division_basis);
  }, [data]);

  const save = useMutation({
    mutationFn: () => pfCeilingApi.setPolicy(basis),
    onSuccess: () => {
      toast.success("Payslip divisor saved");
      qc.invalidateQueries({ queryKey: ["payroll-policy"] });
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });

  const options: { id: DivisionBasis; title: string; desc: string }[] = [
    {
      id: "calendar_days",
      title: "Calendar days of the month (recommended)",
      desc: 'Slip reads "Days Paid 28 / 30" for September, 31 for October.',
    },
    {
      id: "fixed_30",
      title: "Fixed 30 days",
      desc: "Every month is divided by 30, including February.",
    },
    {
      id: "working_days",
      title: "Working days in the attendance window",
      desc: "Legacy: excludes Sundays and holidays (e.g. 26).",
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Payslip divisor</CardTitle>
        <CardDescription>
          How a month's salary is split per day when working out pay for
          absences, joiners and leavers.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {options.map((o) => (
          <label
            key={o.id}
            className="flex cursor-pointer items-start gap-3 rounded-md border border-brand-brown-50 p-3"
          >
            <input
              type="radio"
              className="mt-1"
              checked={basis === o.id}
              onChange={() => setBasis(o.id)}
            />
            <span>
              <span className="block text-sm font-medium">{o.title}</span>
              <span className="block text-xs text-brand-brown-light">{o.desc}</span>
            </span>
          </label>
        ))}
        <div className="flex justify-end">
          <Button
            onClick={() => save.mutate()}
            disabled={save.isPending || basis === data?.division_basis}
          >
            <Save className="mr-1 h-4 w-4" /> Save
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ── PF wage ceiling register ──────────────────────────────────────────
function PfCeilingCard() {
  const qc = useQueryClient();
  const { data: rows = [], isLoading } = useQuery({
    queryKey: ["pf-ceilings"],
    queryFn: pfCeilingApi.list,
  });
  const { data: current } = useQuery({
    queryKey: ["pf-cap-current"],
    queryFn: pfCeilingApi.current,
  });
  const [editing, setEditing] = useState<PfCeiling | "new" | null>(null);
  const [impactFor, setImpactFor] = useState<PfCeiling | null>(null);

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["pf-ceilings"] });
    qc.invalidateQueries({ queryKey: ["pf-cap-current"] });
  };

  const remove = useMutation({
    mutationFn: (id: number) => pfCeilingApi.remove(id),
    onSuccess: () => {
      toast.success("Record deleted");
      refresh();
    },
    onError: (e) => toast.error(errDetail(e, "Could not delete")),
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div>
          <CardTitle>PF wage ceiling</CardTitle>
          <CardDescription>
            Dated register of the EPFO PF wage cap. Payroll uses the cap for
            each wage month (pro-rata when a change starts mid-month). Offer
            letters, salary templates and revisions use the cap in force on
            their date. An employee's own PF cap still overrides this.
          </CardDescription>
          {current && (
            <p className="mt-2 text-sm">
              Currently <strong>{inr(current.pf_cap)}</strong>
              {current.next_change && (
                <span className="text-brand-brown-light">
                  {" "}
                  · next: {inr(current.next_change.cap_amount)} from{" "}
                  {current.next_change.effective_from}
                </span>
              )}
            </p>
          )}
        </div>
        <Button onClick={() => setEditing("new")} className="shrink-0">
          <Plus className="mr-1 h-4 w-4" /> Add record
        </Button>
      </CardHeader>
      <CardContent className="overflow-x-auto p-0">
        <table className="w-full min-w-[820px] text-sm">
          <thead className="bg-brand-brown-50/40 text-left text-brand-brown-light">
            <tr>
              <th className="px-4 py-2">PF cap</th>
              <th>EPS cap</th>
              <th>Effective from</th>
              <th>Mid-month</th>
              <th>Recorded on</th>
              <th>Reference</th>
              <th>Status</th>
              <th className="pr-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={8} className="py-6 text-center text-brand-brown-light">
                  Loading…
                </td>
              </tr>
            )}
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-brand-brown-50">
                <td className="px-4 py-2 font-semibold">{inr(r.cap_amount)}</td>
                <td>{inr(r.eps_cap_amount)}</td>
                <td>{r.effective_from}</td>
                <td className="text-xs">
                  {r.effective_from.endsWith("-01") ? "—" : MODE_LABEL[r.mid_month_mode]}
                </td>
                <td className="text-xs">{r.recorded_on}</td>
                <td className="max-w-[180px] truncate text-xs" title={r.reference ?? ""}>
                  {r.reference ?? "—"}
                </td>
                <td>
                  <span
                    className={`rounded px-2 py-0.5 text-[10px] font-mono uppercase tracking-[0.15em] ${
                      STATUS_TONE[r.status ?? "past"]
                    }`}
                  >
                    {r.status}
                  </span>
                  {r.locked && (
                    <Lock
                      className="ml-1 inline h-3 w-3 text-brand-brown-light"
                      aria-label="Used by a finalized payroll"
                    />
                  )}
                </td>
                <td className="whitespace-nowrap pr-4 text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setImpactFor(r)}
                    title="Impact preview"
                    aria-label="Impact preview"
                  >
                    <BarChart3 className="h-3 w-3" />
                  </Button>{" "}
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={r.locked}
                    onClick={() => setEditing(r)}
                    title={r.locked ? "Used by a finalized payroll" : "Edit"}
                    aria-label="Edit"
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>{" "}
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={r.locked || remove.isPending}
                    onClick={() => {
                      if (window.confirm(`Delete the ${inr(r.cap_amount)} record?`)) {
                        remove.mutate(r.id);
                      }
                    }}
                    title={r.locked ? "Used by a finalized payroll" : "Delete"}
                    aria-label="Delete"
                  >
                    <Trash2 className="h-3 w-3 text-error" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>

      {editing && (
        <CeilingEditor
          record={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={(rec) => {
            refresh();
            setEditing(null);
            if (rec.status !== "past") setImpactFor(rec);
          }}
        />
      )}
      {impactFor && (
        <ImpactModal record={impactFor} onClose={() => setImpactFor(null)} />
      )}
    </Card>
  );
}

function CeilingEditor({
  record,
  onClose,
  onSaved,
}: {
  record: PfCeiling | null;
  onClose: () => void;
  onSaved: (rec: PfCeiling) => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const [form, setForm] = useState<PfCeilingInput>({
    cap_amount: record ? Number(record.cap_amount) : 25000,
    eps_cap_amount: record ? Number(record.eps_cap_amount) : 15000,
    effective_from: record?.effective_from ?? today,
    recorded_on: record?.recorded_on ?? today,
    mid_month_mode: record?.mid_month_mode ?? "day_weighted",
    reference: record?.reference ?? "",
    notes: record?.notes ?? "",
  });
  const midMonth = !form.effective_from.endsWith("-01");

  const save = useMutation({
    mutationFn: () => {
      const body = {
        ...form,
        reference: form.reference || null,
        notes: form.notes || null,
      };
      return record ? pfCeilingApi.update(record.id, body) : pfCeilingApi.create(body);
    },
    onSuccess: (rec) => {
      toast.success(record ? "Record updated" : "Record added");
      onSaved(rec);
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
    >
      <Card className="max-h-[92vh] w-full max-w-lg overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>{record ? "Edit PF ceiling" : "Add PF ceiling"}</CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>PF wage cap (₹ / month)</Label>
              <Input
                type="number"
                min={1}
                value={form.cap_amount}
                onChange={(e) => setForm({ ...form, cap_amount: Number(e.target.value) })}
              />
            </div>
            <div>
              <Label>EPS wage cap (₹ / month)</Label>
              <Input
                type="number"
                min={1}
                value={form.eps_cap_amount ?? ""}
                onChange={(e) =>
                  setForm({ ...form, eps_cap_amount: Number(e.target.value) || null })
                }
              />
            </div>
            <div>
              <Label>Effective from</Label>
              <Input
                type="date"
                value={form.effective_from}
                onChange={(e) => setForm({ ...form, effective_from: e.target.value })}
              />
            </div>
            <div>
              <Label>Recorded on</Label>
              <Input
                type="date"
                value={form.recorded_on ?? ""}
                onChange={(e) => setForm({ ...form, recorded_on: e.target.value })}
              />
            </div>
          </div>
          <p className="text-xs text-brand-brown-light">
            EPS (pension) has its own ceiling. Leave it at ₹15,000 unless the
            circular raises the pension ceiling as well.
          </p>

          {midMonth && (
            <div>
              <Label>This starts mid-month. How should that month be treated?</Label>
              <div className="mt-1 space-y-2">
                {(Object.keys(MODE_LABEL) as PfMidMonthMode[]).map((m) => (
                  <label key={m} className="flex items-center gap-2 text-sm">
                    <input
                      type="radio"
                      checked={form.mid_month_mode === m}
                      onChange={() => setForm({ ...form, mid_month_mode: m })}
                    />
                    {MODE_LABEL[m]}
                    {m === "day_weighted" && (
                      <span className="text-xs text-brand-brown-light">(recommended)</span>
                    )}
                  </label>
                ))}
              </div>
            </div>
          )}

          <div>
            <Label>Reference (circular / notification no.)</Label>
            <Input
              value={form.reference ?? ""}
              onChange={(e) => setForm({ ...form, reference: e.target.value })}
            />
          </div>
          <div>
            <Label>Notes</Label>
            <textarea
              rows={2}
              value={form.notes ?? ""}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
              className="w-full rounded-md border border-brand-brown-50 bg-transparent p-2 text-sm"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={() => save.mutate()}
              disabled={save.isPending || !form.cap_amount || !form.effective_from}
            >
              <Save className="mr-1 h-4 w-4" />
              {save.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ImpactModal({ record, onClose }: { record: PfCeiling; onClose: () => void }) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["pf-impact", record.id],
    queryFn: () => pfCeilingApi.impact(record.id),
  });
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const allIds = useMemo(() => (data?.rows ?? []).map((r) => r.employee_id), [data]);

  const absorb = useMutation({
    mutationFn: () =>
      pfCeilingApi.absorb(record.id, { employee_ids: Array.from(selected) }),
    onSuccess: (res) => {
      toast.success(
        `${res.created.length} salary revision(s) created — approve them on the Salary Revisions page` +
          (res.skipped.length ? ` · ${res.skipped.length} skipped` : ""),
      );
      res.skipped.forEach((s) => toast.message(`Employee #${s.employee_id}: ${s.reason}`));
      setSelected(new Set());
    },
    onError: (e) => toast.error(errDetail(e, "Could not create revisions")),
  });

  const toggle = (id: number) =>
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
    >
      <Card className="max-h-[92vh] w-full max-w-5xl overflow-y-auto">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>
              Impact · {data ? `${inr(data.old_cap)} → ${inr(data.new_cap)}` : inr(record.cap_amount)}
            </CardTitle>
            {data && (
              <CardDescription>
                Monthly figures under the new cap (from {data.first_full_month}).
                The wage month of the change uses a cap of{" "}
                <strong>{inr(data.effective_month_cap)}</strong>. Employees with basic
                at or below the old cap, PF opt-outs and individual caps are not affected.
              </CardDescription>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading && <p className="text-sm text-brand-brown-light">Calculating…</p>}
          {error && (
            <p className="text-sm text-error">{errDetail(error, "Could not load impact")}</p>
          )}
          {data && data.rows.length === 0 && (
            <p className="text-sm text-brand-brown-light">No employees are affected.</p>
          )}
          {data && data.rows.length > 0 && (
            <>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px] text-xs">
                  <thead className="text-left text-brand-brown-light">
                    <tr>
                      <th className="py-2">
                        <input
                          type="checkbox"
                          aria-label="Select all"
                          checked={selected.size === allIds.length && allIds.length > 0}
                          onChange={(e) =>
                            setSelected(e.target.checked ? new Set(allIds) : new Set())
                          }
                        />
                      </th>
                      <th>Employee</th>
                      <th className="text-right">Basic</th>
                      <th className="text-right">PF employee</th>
                      <th className="text-right">PF employer</th>
                      <th className="text-right">Gross</th>
                      <th className="text-right">Take-home</th>
                      <th className="text-right">Change / month</th>
                      <th className="text-right">CTC to absorb</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.rows.map((r) => (
                      <tr key={r.employee_id} className="border-t border-brand-brown-50">
                        <td className="py-1.5">
                          <input
                            type="checkbox"
                            aria-label={`Select ${r.name}`}
                            checked={selected.has(r.employee_id)}
                            onChange={() => toggle(r.employee_id)}
                          />
                        </td>
                        <td>
                          <span className="font-medium">{r.name}</span>{" "}
                          <span className="font-mono text-brand-brown-light">{r.employee_code}</span>
                        </td>
                        <td className="text-right">{inr(r.basic)}</td>
                        <td className="text-right">
                          {inr(r.old_pf_employee)} → {inr(r.new_pf_employee)}
                        </td>
                        <td className="text-right">
                          {inr(r.old_pf_employer)} → {inr(r.new_pf_employer)}
                        </td>
                        <td className="text-right">
                          {r.old_gross === r.new_gross
                            ? inr(r.old_gross)
                            : `${inr(r.old_gross)} → ${inr(r.new_gross)}`}
                        </td>
                        <td className="text-right">
                          {inr(r.old_net)} → {inr(r.new_net)}
                        </td>
                        <td
                          className={`text-right font-semibold ${
                            r.net_change < 0 ? "text-error" : "text-success"
                          }`}
                        >
                          {r.net_change > 0 ? "+" : ""}
                          {inr(r.net_change)}
                        </td>
                        <td className="text-right">{inr(r.absorb_ctc_annual)} / yr</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="rounded-md border border-brand-brown-50 p-3 text-xs text-brand-brown-light">
                <strong className="text-brand-brown-darker">Default:</strong> CTC stays
                fixed and nothing else needs doing. To have the company absorb the extra
                employer PF instead, select employees and create salary revisions. Each
                revision raises CTC to the figure shown so gross salary is unchanged, and
                goes to the Salary Revisions page for approval. Take-home still moves by
                the employee's own extra PF, which is paid into their PF account.
              </div>
              <div className="flex justify-end">
                <Button
                  onClick={() => absorb.mutate()}
                  disabled={selected.size === 0 || absorb.isPending}
                >
                  {absorb.isPending
                    ? "Creating…"
                    : `Apply as salary revision (${selected.size})`}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
