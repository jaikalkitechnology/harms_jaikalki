import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil, Plus, Trash2, X } from "lucide-react";

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
  salaryTemplatesApi,
  type SalaryTemplate,
  type SalaryTemplateInput,
} from "@/lib/api/employees";
import { CategoryBadge } from "@/features/employees/CategoryBadge";
import { useAuthStore } from "@/store/auth";

const CATEGORIES: SalaryTemplate["category"][] = [
  "intern",
  "trainee",
  "permanent",
  "contract",
];

const EMPTY_DRAFT: SalaryTemplateInput = {
  template_code: "",
  template_name: "",
  category: "permanent",
  designation_level: 1,
  ctc_annual_default: "0",
  basic_amount: "0",
  basic_percentage: "50",
  hra_amount: "0",
  hra_percentage: "30",
  other_allowance: "0",
  special_allowance: "0",
  conveyance: "0",
  medical_allowance: "0",
  lta: "0",
  food_coupon: "0",
  travel_expense_max: "0",
  is_paid_internship: false,
  has_probation: true,
  probation_months: 6,
  probation_extension_months: 2,
  mediclaim_amount: "200000",
  pa_insurance_amount: "500000",
  notice_period_probation: 15,
  notice_period_confirmed: 30,
  notice_period_termination: 7,
  is_active: true,
};

export default function SalaryTemplatesPage() {
  const qc = useQueryClient();
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canManage = hasPermission("admin.users.manage");

  const [selected, setSelected] = useState<SalaryTemplate | null>(null);
  const [ctcOverride, setCtcOverride] = useState<string>("");
  const [editorOpen, setEditorOpen] = useState(false);
  const [editorMode, setEditorMode] = useState<"create" | "edit">("create");
  const [draft, setDraft] = useState<SalaryTemplateInput>(EMPTY_DRAFT);

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["salary-templates"],
    queryFn: () => salaryTemplatesApi.list(undefined, false),
  });

  useEffect(() => {
    if (!selected && templates.length > 0) {
      setSelected(
        templates.find((t) => t.template_code === "JKT-TRAINEE-L1") ??
          templates[0],
      );
    }
  }, [templates, selected]);

  const ctcParam =
    ctcOverride && Number(ctcOverride) > 0 ? Number(ctcOverride) : undefined;

  const { data: breakup } = useQuery({
    queryKey: ["salary-breakup", selected?.id, ctcParam],
    queryFn: () => salaryTemplatesApi.calculate(selected!.id, ctcParam),
    enabled: !!selected,
  });

  const create = useMutation({
    mutationFn: (b: SalaryTemplateInput) => salaryTemplatesApi.create(b),
    onSuccess: (t) => {
      toast.success("Template created");
      setEditorOpen(false);
      setSelected(t);
      qc.invalidateQueries({ queryKey: ["salary-templates"] });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(err?.response?.data?.detail ?? "Could not create"),
  });

  const update = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: number;
      body: Partial<SalaryTemplateInput>;
    }) => salaryTemplatesApi.update(id, body),
    onSuccess: (t) => {
      toast.success("Template updated");
      setEditorOpen(false);
      setSelected(t);
      qc.invalidateQueries({ queryKey: ["salary-templates"] });
      qc.invalidateQueries({ queryKey: ["salary-breakup"] });
    },
    onError: () => toast.error("Update failed"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => salaryTemplatesApi.remove(id),
    onSuccess: () => {
      toast.success("Removed");
      setSelected(null);
      qc.invalidateQueries({ queryKey: ["salary-templates"] });
    },
    onError: () => toast.error("Could not delete"),
  });

  const openCreate = () => {
    setEditorMode("create");
    setDraft(EMPTY_DRAFT);
    setEditorOpen(true);
  };
  const openEdit = (t: SalaryTemplate) => {
    setEditorMode("edit");
    const { id: _id, ...rest } = t;
    setDraft(rest as SalaryTemplateInput);
    setEditorOpen(true);
  };

  if (isLoading) return <LoadingScreen label="Loading templates…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Phase 2 · Salary Templates
          </div>
          <h2 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            Jaikalki <span className="display-em">salary library</span>
          </h2>
          <p className="mt-1 text-sm text-brand-brown-light">
            {templates.length} templates · click one to preview its breakup.
          </p>
        </div>
        {canManage && (
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4 mr-1" /> New template
          </Button>
        )}
      </div>

      <div className="grid lg:grid-cols-[20rem_1fr] gap-4">
        <div className="space-y-2">
          {templates.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelected(t)}
              className={`w-full text-left p-4 rounded-xl border transition-colors ${
                selected?.id === t.id
                  ? "bg-brand-gold/10 border-brand-gold/40"
                  : "bg-card border-brand-brown-100 hover:border-brand-gold/30"
              }`}
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-brand-brown-light">
                {t.template_code}
              </div>
              <div className="font-medium text-brand-brown-darker">
                {t.template_name}
              </div>
              <div className="mt-2 flex items-center gap-2">
                <CategoryBadge code={t.category.toUpperCase()} />
                <span className="text-[10px] text-brand-brown-light">
                  L{t.designation_level}
                </span>
                {!t.is_active && (
                  <span className="text-[10px] text-error">inactive</span>
                )}
              </div>
            </button>
          ))}
        </div>

        {selected && breakup && (
          <Card>
            <CardHeader className="flex flex-row items-start justify-between gap-4 flex-wrap">
              <div>
                <CardTitle>{breakup.template_name}</CardTitle>
                <CardDescription>
                  {breakup.template_code} · {breakup.category}
                </CardDescription>
              </div>
              <div className="flex items-end gap-2 flex-wrap">
                <div>
                  <Label htmlFor="ctc">CTC override (₹/yr)</Label>
                  <Input
                    id="ctc"
                    type="number"
                    placeholder={String(selected.ctc_annual_default)}
                    value={ctcOverride}
                    onChange={(e) => setCtcOverride(e.target.value)}
                    className="w-40"
                  />
                </div>
                {canManage && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => openEdit(selected)}
                    >
                      <Pencil className="h-3 w-3 mr-1" /> Edit
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        if (
                          confirm(
                            `Delete "${selected.template_name}"? Will soft-delete (is_active=false) if it's referenced by an employee.`,
                          )
                        )
                          remove.mutate(selected.id);
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {breakup.is_intern ? (
                <div className="space-y-2">
                  <p className="text-sm">
                    <strong>Intern</strong> — receives travel expense
                    reimbursement only, capped at{" "}
                    <strong>
                      ₹{breakup.travel_expense_max.toLocaleString()}
                    </strong>{" "}
                    per month. No salary, PF, or ESIC.
                  </p>
                  {breakup.notes.map((n, i) => (
                    <p key={i} className="text-xs text-brand-brown-light">
                      {n}
                    </p>
                  ))}
                </div>
              ) : (
                <div className="grid md:grid-cols-3 gap-6 text-sm">
                  <BreakupColumn
                    title="Earnings (monthly)"
                    rows={[
                      ["Basic", breakup.basic],
                      ["HRA", breakup.hra],
                      ["Other Allowance", breakup.other_allowance],
                      ["Special Allowance", breakup.special_allowance],
                      ["Conveyance", breakup.conveyance],
                      ["Medical Allowance", breakup.medical_allowance],
                      ["LTA", breakup.lta],
                      ["Food Coupon", breakup.food_coupon],
                    ]}
                    total={["Gross", breakup.gross]}
                  />
                  <BreakupColumn
                    title="Deductions"
                    rows={[
                      ["PF (Employee)", breakup.pf_employee],
                      ["ESIC (Employee)", breakup.esic_employee],
                      ["Professional Tax", breakup.professional_tax],
                    ]}
                    total={["Total", breakup.total_deductions]}
                    after={["Net Salary", breakup.net_salary]}
                  />
                  <BreakupColumn
                    title="Employer cost"
                    rows={[
                      ["PF (Employer)", breakup.pf_employer],
                      ["ESIC (Employer)", breakup.esic_employer],
                    ]}
                    total={["CTC / month", breakup.total_ctc_monthly]}
                    after={["CTC / year", breakup.total_ctc_annual]}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>

      {editorOpen && (
        <EditorModal
          mode={editorMode}
          draft={draft}
          setDraft={setDraft}
          editingId={editorMode === "edit" ? selected?.id : undefined}
          onClose={() => setEditorOpen(false)}
          onSubmit={() => {
            if (editorMode === "create") {
              create.mutate(draft);
            } else if (selected) {
              update.mutate({ id: selected.id, body: draft });
            }
          }}
          submitting={create.isPending || update.isPending}
        />
      )}
    </div>
  );
}

function BreakupColumn({
  title,
  rows,
  total,
  after,
}: {
  title: string;
  rows: [string, number][];
  total: [string, number];
  after?: [string, number];
}) {
  const inr = (n: number) => `₹${n.toLocaleString("en-IN")}`;
  const visibleRows = rows.filter(([, v]) => v > 0);
  return (
    <div>
      <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-2">
        {title}
      </div>
      <dl className="space-y-1.5">
        {visibleRows.map(([k, v]) => (
          <div key={k} className="flex justify-between">
            <dt className="text-brand-brown-light">{k}</dt>
            <dd className="font-medium">{inr(v)}</dd>
          </div>
        ))}
        <div className="flex justify-between pt-2 border-t border-brand-brown-100 font-semibold">
          <dt>{total[0]}</dt>
          <dd>{inr(total[1])}</dd>
        </div>
        {after && (
          <div className="flex justify-between pt-2 border-t border-brand-brown-100 text-brand-gold-dark font-semibold">
            <dt>{after[0]}</dt>
            <dd>{inr(after[1])}</dd>
          </div>
        )}
      </dl>
    </div>
  );
}

function EditorModal({
  mode,
  draft,
  setDraft,
  editingId: _editingId,
  onClose,
  onSubmit,
  submitting,
}: {
  mode: "create" | "edit";
  draft: SalaryTemplateInput;
  setDraft: (v: SalaryTemplateInput) => void;
  editingId?: number;
  onClose: () => void;
  onSubmit: () => void;
  submitting: boolean;
}) {
  const setField = <K extends keyof SalaryTemplateInput>(
    k: K,
    v: SalaryTemplateInput[K],
  ) => setDraft({ ...draft, [k]: v });

  const num = (v: string) => v.replace(/[^0-9.]/g, "");

  const sections = useMemo(
    () => [
      {
        title: "Identity",
        fields: [
          ["template_code", "Code", "text", true] as const,
          ["template_name", "Name", "text", false] as const,
          ["category", "Category", "select", false] as const,
          ["designation_level", "Level (1-10)", "int", false] as const,
        ],
      },
      {
        title: "Compensation",
        fields: [
          ["ctc_annual_default", "CTC default (annual ₹)", "decimal", false] as const,
          ["basic_amount", "Basic amount", "decimal", false] as const,
          ["basic_percentage", "Basic %", "decimal", false] as const,
          ["hra_amount", "HRA amount", "decimal", false] as const,
          ["hra_percentage", "HRA %", "decimal", false] as const,
          ["other_allowance", "Other allowance", "decimal", false] as const,
          ["special_allowance", "Special allowance", "decimal", false] as const,
          ["conveyance", "Conveyance", "decimal", false] as const,
          ["medical_allowance", "Medical allowance", "decimal", false] as const,
          ["lta", "LTA", "decimal", false] as const,
          ["food_coupon", "Food coupon", "decimal", false] as const,
          ["travel_expense_max", "Travel expense max (intern)", "decimal", false] as const,
        ],
      },
      {
        title: "Probation & notice",
        fields: [
          ["has_probation", "Has probation", "bool", false] as const,
          ["probation_months", "Probation months", "int", false] as const,
          ["probation_extension_months", "Probation extension (months)", "int", false] as const,
          ["notice_period_probation", "Notice (probation, days)", "int", false] as const,
          ["notice_period_confirmed", "Notice (confirmed, days)", "int", false] as const,
          ["notice_period_termination", "Notice (termination, days)", "int", false] as const,
        ],
      },
      {
        title: "Insurance & flags",
        fields: [
          ["mediclaim_amount", "Mediclaim cover (₹)", "decimal", false] as const,
          ["pa_insurance_amount", "PA insurance (₹)", "decimal", false] as const,
          ["is_paid_internship", "Paid internship", "bool", false] as const,
          ["is_active", "Active", "bool", false] as const,
        ],
      },
    ],
    [],
  );

  return (
    <div className="fixed inset-0 z-50 flex items-start md:items-center justify-center p-4 bg-black/40">
      <div className="bg-card rounded-xl border border-brand-brown-100 shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-brand-brown-100">
          <div className="font-display text-lg">
            {mode === "create" ? "New" : "Edit"} salary template
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 grid place-items-center rounded-lg hover:bg-brand-brown-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="overflow-y-auto p-4 space-y-6">
          {sections.map((s) => (
            <div key={s.title}>
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-2">
                {s.title}
              </div>
              <div className="grid sm:grid-cols-2 gap-3">
                {s.fields.map(([key, label, kind, codeLocked]) => {
                  if (kind === "select") {
                    return (
                      <div key={key}>
                        <Label>{label}</Label>
                        <select
                          className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
                          value={draft.category}
                          onChange={(e) =>
                            setField(
                              "category",
                              e.target.value as SalaryTemplate["category"],
                            )
                          }
                        >
                          {CATEGORIES.map((c) => (
                            <option key={c} value={c}>
                              {c}
                            </option>
                          ))}
                        </select>
                      </div>
                    );
                  }
                  if (kind === "bool") {
                    return (
                      <label
                        key={key}
                        className="flex items-center gap-2 text-sm h-10 mt-6"
                      >
                        <input
                          type="checkbox"
                          checked={Boolean(draft[key])}
                          onChange={(e) =>
                            setField(key, e.target.checked as never)
                          }
                        />
                        {label}
                      </label>
                    );
                  }
                  if (kind === "int") {
                    return (
                      <div key={key}>
                        <Label>{label}</Label>
                        <Input
                          type="number"
                          value={String(draft[key] ?? "")}
                          onChange={(e) =>
                            setField(key, Number(e.target.value) as never)
                          }
                        />
                      </div>
                    );
                  }
                  // decimal / text
                  return (
                    <div key={key}>
                      <Label>{label}</Label>
                      <Input
                        value={String(draft[key] ?? "")}
                        disabled={codeLocked && mode === "edit"}
                        onChange={(e) => {
                          const v =
                            kind === "decimal"
                              ? num(e.target.value)
                              : e.target.value;
                          setField(key, v as never);
                        }}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
        <div className="p-4 border-t border-brand-brown-100 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            disabled={
              submitting ||
              !draft.template_code ||
              !draft.template_name
            }
            onClick={onSubmit}
          >
            {submitting
              ? "Saving…"
              : mode === "create"
              ? "Create"
              : "Save changes"}
          </Button>
        </div>
      </div>
    </div>
  );
}
