// Create / edit an incentive scheme: target type, slabs, rules.
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { TARGET_METRICS, type TargetMetric } from "@/lib/api/sales";
import { organizationApi } from "@/lib/api/organization";
import { lookupsApi } from "@/lib/api/employees";
import { incentivesApi, type IncentiveScheme, type SchemeInput, type Slab } from "@/lib/api/incentives";
import { Modal } from "@/features/polish/assets/AssetDialogs";
import { Field, FormActions, SELECT_CLASS, errDetail } from "@/features/employees/profile/ui";

export function slabText(s: Pick<IncentiveScheme, "payout_type">, sl: Slab) {
  return s.payout_type === "percent_of_achieved"
    ? `${sl.min_pct}% → ${sl.value}% of sales`
    : `${sl.min_pct}% → ₹${Number(sl.value).toLocaleString("en-IN")}`;
}

const BLANK: SchemeInput = {
  name: "",
  description: "",
  metric: "sales_amount",
  period_type: "monthly",
  payout_type: "fixed",
  slabs: [
    { min_pct: 80, value: 2000 },
    { min_pct: 100, value: 5000 },
  ],
  max_payout: null,
  department_ids: null,
  category_codes: null,
  designation_ids: null,
  min_attendance_pct: 90,
  confirmed_only: true,
  exclude_notice: true,
  no_warning_days: 90,
  min_tenure_days: null,
  is_active: true,
};

function Toggle({ checked, onChange, children }: { checked: boolean; onChange: (v: boolean) => void; children: React.ReactNode }) {
  return (
    <label className="flex items-center gap-2 text-sm">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      {children}
    </label>
  );
}

function Picker<T extends string | number>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T[] | null;
  onChange: (v: T[] | null) => void;
}) {
  const sel = new Set(value ?? []);
  return (
    <Field label={label} help={sel.size ? `${sel.size} selected` : "Everyone"}>
      <div className="max-h-32 overflow-y-auto rounded-md border border-brand-brown-100 p-2">
        {options.map((o) => (
          <label key={String(o.value)} className="flex items-center gap-2 py-0.5 text-sm">
            <input
              type="checkbox"
              checked={sel.has(o.value)}
              onChange={(e) => {
                const n = new Set(sel);
                if (e.target.checked) n.add(o.value);
                else n.delete(o.value);
                onChange(n.size ? [...n] : null);
              }}
            />
            {o.label}
          </label>
        ))}
      </div>
    </Field>
  );
}

export function SchemeModal({ scheme, onClose }: { scheme: IncentiveScheme | null; onClose: () => void }) {
  const qc = useQueryClient();
  const [d, setD] = useState<SchemeInput>(
    scheme ? { ...scheme, max_payout: scheme.max_payout != null ? Number(scheme.max_payout) : null } : BLANK,
  );
  const set = <K extends keyof SchemeInput>(k: K, v: SchemeInput[K]) => setD({ ...d, [k]: v });
  const { data: departments = [] } = useQuery({ queryKey: ["departments"], queryFn: organizationApi.listDepartments });
  const { data: designations = [] } = useQuery({ queryKey: ["designations"], queryFn: organizationApi.listDesignations });
  const { data: categories = [] } = useQuery({ queryKey: ["employee-categories"], queryFn: () => lookupsApi.categories() });

  const save = useMutation({
    mutationFn: () => {
      const body = { ...d, slabs: d.slabs.map((s) => ({ min_pct: Number(s.min_pct), value: Number(s.value) })) };
      return scheme ? incentivesApi.updateScheme(scheme.id, body) : incentivesApi.createScheme(body);
    },
    onSuccess: () => {
      toast.success(scheme ? "Scheme updated" : "Scheme created");
      qc.invalidateQueries({ queryKey: ["incentive-schemes"] });
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not save the scheme")),
  });

  const pct = d.payout_type === "percent_of_achieved";
  const num = (v: string) => (v === "" ? null : Number(v));

  return (
    <Modal wide title={scheme ? "Edit scheme" : "New incentive scheme"} onClose={onClose}>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Name" className="col-span-full">
          <Input value={d.name} maxLength={120} placeholder="e.g. Sales incentive" onChange={(e) => set("name", e.target.value)} />
        </Field>
        <Field label="Description (shown to employees)" className="col-span-full">
          <Input value={d.description ?? ""} maxLength={4000} onChange={(e) => set("description", e.target.value)} />
        </Field>
        <Field label="Pays on">
          <select
            className={SELECT_CLASS}
            value={d.metric}
            onChange={(e) => {
              const m = e.target.value as TargetMetric;
              setD({ ...d, metric: m, payout_type: m === "sales_amount" ? d.payout_type : "fixed" });
            }}
          >
            {TARGET_METRICS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label} target
              </option>
            ))}
          </select>
        </Field>
        <Field label="Period">
          <select className={SELECT_CLASS} value={d.period_type} onChange={(e) => set("period_type", e.target.value as SchemeInput["period_type"])}>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
          </select>
        </Field>
        <Field label="Payout" className="col-span-full">
          <select
            className={SELECT_CLASS}
            value={d.payout_type}
            onChange={(e) => set("payout_type", e.target.value as SchemeInput["payout_type"])}
          >
            <option value="fixed">Fixed ₹ amount per slab</option>
            {d.metric === "sales_amount" && <option value="percent_of_achieved">% of sales achieved</option>}
          </select>
        </Field>

        <div className="col-span-full space-y-2">
          <div className="text-sm font-medium text-brand-brown-darker">Slabs — the highest one reached pays</div>
          {d.slabs.map((s, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span className="text-brand-brown-light">At</span>
              <Input
                type="number"
                className="w-24"
                value={s.min_pct}
                onChange={(e) => set("slabs", d.slabs.map((x, j) => (j === i ? { ...x, min_pct: Number(e.target.value) } : x)))}
              />
              <span className="text-brand-brown-light">% of target, pay</span>
              {!pct && <span>₹</span>}
              <Input
                type="number"
                className="w-32"
                value={s.value}
                onChange={(e) => set("slabs", d.slabs.map((x, j) => (j === i ? { ...x, value: Number(e.target.value) } : x)))}
              />
              {pct && <span className="text-brand-brown-light">% of sales</span>}
              <Button
                variant="ghost"
                size="sm"
                aria-label="Remove slab"
                disabled={d.slabs.length === 1}
                onClick={() => set("slabs", d.slabs.filter((_, j) => j !== i))}
              >
                <Trash2 className="size-4" />
              </Button>
            </div>
          ))}
          <Button
            variant="outline"
            size="sm"
            className="gap-1"
            onClick={() => {
              const top = d.slabs[d.slabs.length - 1];
              set("slabs", [...d.slabs, { min_pct: (top?.min_pct ?? 80) + 20, value: (top?.value ?? 0) * 1.5 }]);
            }}
          >
            <Plus className="size-3.5" /> Add slab
          </Button>
        </div>
        <Field label="Maximum payout per person (optional)">
          <Input type="number" value={d.max_payout ?? ""} onChange={(e) => set("max_payout", num(e.target.value))} />
        </Field>

        <div className="col-span-full mt-2 text-sm font-medium text-brand-brown-darker">Who qualifies</div>
        <Field label="Minimum attendance % (blank = not checked)">
          <Input
            type="number"
            min={0}
            max={100}
            value={d.min_attendance_pct ?? ""}
            onChange={(e) => set("min_attendance_pct", num(e.target.value))}
          />
        </Field>
        <Field label="No warning letter in the last … days">
          <Input type="number" value={d.no_warning_days ?? ""} onChange={(e) => set("no_warning_days", num(e.target.value))} />
        </Field>
        <Field label="Minimum days with the company">
          <Input type="number" value={d.min_tenure_days ?? ""} onChange={(e) => set("min_tenure_days", num(e.target.value))} />
        </Field>
        <div className="space-y-2 pt-6">
          <Toggle checked={d.confirmed_only} onChange={(v) => set("confirmed_only", v)}>
            Confirmed staff only (not on probation)
          </Toggle>
          <Toggle checked={d.exclude_notice} onChange={(v) => set("exclude_notice", v)}>
            Not for people serving notice
          </Toggle>
        </div>
        <Picker
          label="Departments"
          options={departments.map((x) => ({ value: x.id, label: x.name }))}
          value={d.department_ids}
          onChange={(v) => set("department_ids", v)}
        />
        <Picker
          label="Employee categories"
          options={categories.map((x) => ({ value: x.code, label: x.name }))}
          value={d.category_codes}
          onChange={(v) => set("category_codes", v)}
        />
        <Picker
          label="Designations"
          options={designations.map((x) => ({ value: x.id, label: x.name }))}
          value={d.designation_ids}
          onChange={(v) => set("designation_ids", v)}
        />
        <div className="pt-6">
          <Toggle checked={d.is_active} onChange={(v) => set("is_active", v)}>
            Active — calculated automatically each period
          </Toggle>
        </div>
        <FormActions
          onCancel={onClose}
          onSave={() => save.mutate()}
          saving={save.isPending}
          disabled={d.name.trim().length < 2 || !d.slabs.length}
          saveLabel={scheme ? "Save" : "Create scheme"}
        />
      </div>
    </Modal>
  );
}
