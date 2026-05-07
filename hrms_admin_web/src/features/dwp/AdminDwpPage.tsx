import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ChevronLeft,
  ChevronRight,
  Pencil,
  Plus,
  Save,
  Trash2,
  X,
} from "lucide-react";

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
  dwpApi,
  type DwpSubmission,
  type DwpTemplateField,
  type DwpTemplateLite,
} from "@/lib/api/dwp";
import { employeesApi, type EmployeeListItem } from "@/lib/api/employees";
import { fmtIstDate } from "@/lib/datetime";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export default function AdminDwpPage() {
  const qc = useQueryClient();
  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [type, setType] = useState<"" | "morning" | "eod">("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(25);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<DwpSubmission | null>(null);

  const { data: employees = [] } = useQuery({
    queryKey: ["employees-active-dwp"],
    queryFn: () => employeesApi.list(),
  });
  const empById = useMemo(() => {
    const m = new Map<number, EmployeeListItem>();
    employees.forEach((e) => m.set(e.id, e));
    return m;
  }, [employees]);

  const { data: templates = [] } = useQuery({
    queryKey: ["dwp-admin-templates"],
    queryFn: () => dwpApi.adminTemplates(),
  });

  const params = {
    employee_id: employeeId === "" ? undefined : (employeeId as number),
    type: (type || undefined) as "morning" | "eod" | undefined,
    from_date: fromDate || undefined,
    to_date: toDate || undefined,
    page,
    per_page: perPage,
  };

  const { data, isLoading } = useQuery({
    queryKey: ["dwp-admin-list", params],
    queryFn: () => dwpApi.adminList(params),
    placeholderData: (prev) => prev,
  });

  const remove = useMutation({
    mutationFn: (id: number) => dwpApi.adminDelete(id),
    onSuccess: () => {
      toast.success("Removed");
      qc.invalidateQueries({ queryKey: ["dwp-admin-list"] });
    },
    onError: () => toast.error("Could not delete"),
  });

  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / perPage));

  if (isLoading && !data) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Daily Work Planning · Admin
          </div>
          <h2 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            Manage <span className="display-em">daily plans</span>
          </h2>
          <p className="text-sm text-brand-brown-light mt-1">
            File a plan on behalf of an employee, or edit / remove what's
            already there. {total} record{total === 1 ? "" : "s"} total.
          </p>
        </div>
        <Button
          onClick={() => {
            setEditing(null);
            setEditorOpen(true);
          }}
        >
          <Plus className="h-4 w-4 mr-1" /> New plan
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Combine to narrow the list.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="md:col-span-2">
            <Label>Employee</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={employeeId}
              onChange={(e) => {
                setEmployeeId(e.target.value ? Number(e.target.value) : "");
                setPage(1);
              }}
            >
              <option value="">All</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.employee_code} — {e.first_name} {e.last_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Type</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={type}
              onChange={(e) => {
                setType(e.target.value as typeof type);
                setPage(1);
              }}
            >
              <option value="">Any</option>
              <option value="morning">Morning</option>
              <option value="eod">EOD</option>
            </select>
          </div>
          <div>
            <Label>From</Label>
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => {
                setFromDate(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <div>
            <Label>To</Label>
            <Input
              type="date"
              value={toDate}
              onChange={(e) => {
                setToDate(e.target.value);
                setPage(1);
              }}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm min-w-[760px]">
            <thead className="text-left text-brand-brown-light bg-brand-brown-50">
              <tr>
                <th className="py-2 px-4">Date</th>
                <th>Employee</th>
                <th>Type</th>
                <th>Hours</th>
                <th>Mood</th>
                <th>Submitted</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {items.map((s) => {
                const e = empById.get(s.employee_id);
                return (
                  <tr
                    key={s.id}
                    className="border-t border-brand-brown-50 hover:bg-brand-brown-50/30"
                  >
                    <td className="py-2 px-4 font-mono text-xs">
                      {fmtIstDate(s.date)}
                    </td>
                    <td>
                      {e
                        ? `${e.employee_code} · ${e.first_name} ${e.last_name}`
                        : `Employee #${s.employee_id}`}
                    </td>
                    <td>
                      <span
                        className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded ${
                          s.type === "morning"
                            ? "bg-info/15 text-info"
                            : "bg-brand-gold/15 text-brand-gold-dark"
                        }`}
                      >
                        {s.type}
                      </span>
                    </td>
                    <td>{s.total_hours ?? "—"}</td>
                    <td>{s.mood_rating ?? "—"}</td>
                    <td className="text-xs text-brand-brown-light">
                      {fmtIstDate(s.submitted_at)}
                    </td>
                    <td className="text-right pr-4 whitespace-nowrap">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setEditing(s);
                          setEditorOpen(true);
                        }}
                      >
                        <Pencil className="h-3 w-3" />
                      </Button>{" "}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          if (confirm(`Delete this ${s.type} plan?`))
                            remove.mutate(s.id);
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </td>
                  </tr>
                );
              })}
              {items.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="text-center py-8 text-brand-brown-light"
                  >
                    No plans match the filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between text-sm">
        <div className="text-brand-brown-light">
          Page {page} of {totalPages} · {total} total
        </div>
        <div className="flex items-center gap-2">
          <select
            className="h-9 px-2 rounded border border-brand-brown-50 bg-card text-xs"
            value={perPage}
            onChange={(e) => {
              setPerPage(Number(e.target.value));
              setPage(1);
            }}
          >
            {[10, 25, 50, 100].map((n) => (
              <option key={n} value={n}>
                {n} / page
              </option>
            ))}
          </select>
          <Button
            size="sm"
            variant="outline"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            <ChevronLeft className="h-3 w-3" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
          >
            <ChevronRight className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {editorOpen && (
        <Editor
          mode={editing ? "edit" : "create"}
          existing={editing}
          employees={employees}
          templates={templates}
          onClose={() => {
            setEditorOpen(false);
            setEditing(null);
          }}
        />
      )}
    </div>
  );
}

function Editor({
  mode,
  existing,
  employees,
  templates,
  onClose,
}: {
  mode: "create" | "edit";
  existing: DwpSubmission | null;
  employees: EmployeeListItem[];
  templates: DwpTemplateLite[];
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [employeeId, setEmployeeId] = useState<number | "">(
    existing?.employee_id ?? "",
  );
  const [templateId, setTemplateId] = useState<number | "">(
    existing?.template_id ?? "",
  );
  const [date, setDate] = useState(existing?.date ?? todayISO());
  const [totalHours, setTotalHours] = useState<string>(
    existing?.total_hours != null ? String(existing.total_hours) : "",
  );
  const [moodRating, setMoodRating] = useState<string>(
    existing?.mood_rating != null ? String(existing.mood_rating) : "",
  );
  const [fields, setFields] = useState<Record<string, string>>(() => {
    const init: Record<string, string> = {};
    (existing?.fields ?? []).forEach((f) => {
      init[f.field_key] = f.value ?? "";
    });
    return init;
  });

  const tpl = useMemo(
    () => templates.find((t) => t.id === templateId) ?? null,
    [templates, templateId],
  );

  // When template changes (on create only), seed empty fields.
  const lastTplId = useRef<number | null>(null);
  useEffect(() => {
    if (mode !== "create") return;
    if (tpl && tpl.id !== lastTplId.current) {
      const init: Record<string, string> = {};
      tpl.fields.forEach((f) => {
        init[f.key] = "";
      });
      setFields(init);
      lastTplId.current = tpl.id;
    }
  }, [tpl, mode]);

  const create = useMutation({
    mutationFn: () =>
      dwpApi.adminSubmit({
        employee_id: employeeId as number,
        template_id: templateId as number,
        fields,
        total_hours: totalHours ? Number(totalHours) : undefined,
        mood_rating: moodRating ? Number(moodRating) : undefined,
        on_date: date || undefined,
      }),
    onSuccess: () => {
      toast.success("Plan filed");
      qc.invalidateQueries({ queryKey: ["dwp-admin-list"] });
      onClose();
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(err?.response?.data?.detail ?? "Could not file plan"),
  });

  const update = useMutation({
    mutationFn: () =>
      dwpApi.adminUpdate(existing!.id, {
        fields,
        total_hours: totalHours ? Number(totalHours) : undefined,
        mood_rating: moodRating ? Number(moodRating) : undefined,
      }),
    onSuccess: () => {
      toast.success("Saved");
      qc.invalidateQueries({ queryKey: ["dwp-admin-list"] });
      onClose();
    },
    onError: () => toast.error("Save failed"),
  });

  const submit = () => (mode === "create" ? create.mutate() : update.mutate());

  return (
    <div className="fixed inset-0 z-50 flex items-start md:items-center justify-center p-4 bg-black/40">
      <div className="bg-card rounded-xl border border-brand-brown-100 shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-brand-brown-100">
          <div className="font-display text-lg">
            {mode === "create" ? "New" : "Edit"} daily plan
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 grid place-items-center rounded-lg hover:bg-brand-brown-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="overflow-y-auto p-4 space-y-3">
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <Label>Employee</Label>
              <select
                disabled={mode === "edit"}
                className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
                value={employeeId}
                onChange={(e) =>
                  setEmployeeId(
                    e.target.value ? Number(e.target.value) : "",
                  )
                }
              >
                <option value="">Pick employee…</option>
                {employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.employee_code} — {e.first_name} {e.last_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Template</Label>
              <select
                disabled={mode === "edit"}
                className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
                value={templateId}
                onChange={(e) =>
                  setTemplateId(
                    e.target.value ? Number(e.target.value) : "",
                  )
                }
              >
                <option value="">Pick template…</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    #{t.id} · {t.type}
                    {t.department_id ? ` (dept ${t.department_id})` : ""}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Date</Label>
              <Input
                type="date"
                disabled={mode === "edit"}
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label>Total hours</Label>
                <Input
                  type="number"
                  step="0.25"
                  min={0}
                  max={24}
                  value={totalHours}
                  onChange={(e) => setTotalHours(e.target.value)}
                />
              </div>
              <div>
                <Label>Mood (1-5)</Label>
                <Input
                  type="number"
                  min={1}
                  max={5}
                  value={moodRating}
                  onChange={(e) => setMoodRating(e.target.value)}
                />
              </div>
            </div>
          </div>

          {tpl ? (
            <div className="border border-brand-brown-50 rounded p-3 space-y-3">
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                {tpl.type} fields
              </div>
              {tpl.fields.map((f) => (
                <FieldInput
                  key={f.key}
                  field={f}
                  value={fields[f.key] ?? ""}
                  onChange={(v) => setFields({ ...fields, [f.key]: v })}
                />
              ))}
            </div>
          ) : (
            mode === "create" && (
              <div className="text-sm text-brand-brown-light italic">
                Pick a template to load its fields.
              </div>
            )
          )}
        </div>
        <div className="p-4 border-t border-brand-brown-100 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            disabled={
              create.isPending ||
              update.isPending ||
              (mode === "create" && (!employeeId || !templateId))
            }
            onClick={submit}
          >
            <Save className="h-4 w-4 mr-1" />
            {mode === "create" ? "File plan" : "Save changes"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function FieldInput({
  field,
  value,
  onChange,
}: {
  field: DwpTemplateField;
  value: string;
  onChange: (v: string) => void;
}) {
  const t = field.field_type;
  if (t === "text" || t === "long_text") {
    return (
      <div>
        <Label>
          {field.label}
          {field.is_required && " *"}
        </Label>
        <textarea
          rows={t === "long_text" ? 4 : 2}
          className="w-full border border-brand-brown-50 rounded p-2 text-sm bg-card"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={field.placeholder ?? ""}
        />
      </div>
    );
  }
  if (t === "select" || t === "single_choice") {
    return (
      <div>
        <Label>
          {field.label}
          {field.is_required && " *"}
        </Label>
        <select
          className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          <option value="">—</option>
          {(field.options ?? []).map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      </div>
    );
  }
  if (t === "boolean" || t === "checkbox") {
    return (
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={value === "true" || value === "1"}
          onChange={(e) => onChange(e.target.checked ? "true" : "false")}
        />
        {field.label}
      </label>
    );
  }
  if (t === "number" || t === "rating") {
    return (
      <div>
        <Label>
          {field.label}
          {field.is_required && " *"}
        </Label>
        <Input
          type="number"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
    );
  }
  // default: plain text
  return (
    <div>
      <Label>
        {field.label}
        {field.is_required && " *"}
      </Label>
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={field.placeholder ?? ""}
      />
    </div>
  );
}
