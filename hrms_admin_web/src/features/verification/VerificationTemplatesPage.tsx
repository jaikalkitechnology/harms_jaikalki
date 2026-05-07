import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ChevronLeft,
  ChevronRight,
  Pencil,
  Plus,
  Search,
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
  verificationApi,
  type TemplateField,
  type VerificationTemplate,
} from "@/lib/api/verification";

const TYPES = [
  "address",
  "employment",
  "document",
  "business",
  "education",
  "criminal",
  "bank",
  "other",
];

const FIELD_TYPES = [
  "text",
  "number",
  "date",
  "dropdown",
  "checkbox",
  "photo",
  "signature",
  "address",
  "phone",
  "email",
  "textarea",
];

const PAGE_SIZE = 8;

interface Draft {
  code: string;
  name: string;
  type: string;
  description: string;
  sla_hours: string;
  signature_required: boolean;
  is_active: boolean;
  fields: TemplateField[];
}

const EMPTY_DRAFT: Draft = {
  code: "",
  name: "",
  type: "address",
  description: "",
  sla_hours: "48",
  signature_required: false,
  is_active: true,
  fields: [
    { key: "subject_present", label: "Subject present", field_type: "checkbox", required: true },
  ],
};

export default function VerificationTemplatesPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);
  const [page, setPage] = useState(1);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<VerificationTemplate | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["verification-templates", search, typeFilter, includeInactive],
    queryFn: () =>
      verificationApi.templates({
        search: search || undefined,
        type: typeFilter || undefined,
        include_inactive: includeInactive,
      }),
  });

  const create = useMutation({
    mutationFn: () =>
      verificationApi.createTemplate({
        code: draft.code,
        name: draft.name,
        type: draft.type,
        description: draft.description || null,
        sla_hours: Number(draft.sla_hours) || 48,
        signature_required: draft.signature_required,
        fields: draft.fields,
      }),
    onSuccess: () => {
      toast.success("Template created");
      setEditorOpen(false);
      qc.invalidateQueries({ queryKey: ["verification-templates"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not create template"),
  });

  const update = useMutation({
    mutationFn: () =>
      verificationApi.updateTemplate(editing!.id, {
        name: draft.name,
        type: draft.type,
        description: draft.description || null,
        sla_hours: Number(draft.sla_hours) || 48,
        signature_required: draft.signature_required,
        is_active: draft.is_active,
        fields: draft.fields,
      }),
    onSuccess: () => {
      toast.success("Template updated");
      setEditorOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["verification-templates"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not update template"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => verificationApi.deleteTemplate(id),
    onSuccess: () => {
      toast.success("Template deactivated");
      qc.invalidateQueries({ queryKey: ["verification-templates"] });
    },
    onError: () => toast.error("Could not delete"),
  });

  const filtered = useMemo(() => templates, [templates]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageRows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const openCreate = () => {
    setEditing(null);
    setDraft(EMPTY_DRAFT);
    setEditorOpen(true);
  };

  const openEdit = (t: VerificationTemplate) => {
    setEditing(t);
    setDraft({
      code: t.code,
      name: t.name,
      type: t.type,
      description: t.description ?? "",
      sla_hours: String(t.sla_hours),
      signature_required: t.signature_required,
      is_active: t.is_active,
      fields: t.fields,
    });
    setEditorOpen(true);
  };

  if (isLoading) return <LoadingScreen label="Loading templates…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Verification Templates
          </h1>
          <p className="text-sm text-brand-brown-light">
            JSON-driven templates power the field employee's dynamic form.
            {filtered.length} template{filtered.length === 1 ? "" : "s"} match
            current filters.
          </p>
        </div>
        <Button onClick={openCreate} className="gap-2">
          <Plus className="size-4" /> New template
        </Button>
      </div>

      {/* Filter bar */}
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search code / name / description…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setPage(1);
            }}
            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="">All types</option>
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
            />
            Include inactive
          </label>
          <div className="text-xs text-brand-brown-light flex items-center">
            {filtered.length} match{filtered.length === 1 ? "" : "es"}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3 text-right">SLA</th>
                <th className="px-4 py-3 text-right">Fields</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No templates match these filters.
                  </td>
                </tr>
              ) : (
                pageRows.map((t) => (
                  <tr key={t.id} className="border-t border-brand-brown-50">
                    <td className="px-4 py-3 font-mono text-xs">{t.code}</td>
                    <td className="px-4 py-3 font-medium">
                      {t.name}
                      {t.description && (
                        <div className="text-xs text-brand-brown-light">
                          {t.description}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 capitalize">{t.type}</td>
                    <td className="px-4 py-3 text-right">{t.sla_hours}h</td>
                    <td className="px-4 py-3 text-right">{t.fields.length}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2 py-1 text-xs ${t.is_active ? "bg-success/15 text-success" : "bg-brand-brown-50 text-brand-brown-darker"}`}
                      >
                        {t.is_active ? "active" : "inactive"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        title="Edit"
                        onClick={() => openEdit(t)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        title="Deactivate"
                        onClick={() => {
                          if (confirm(`Deactivate template "${t.name}"?`))
                            remove.mutate(t.id);
                        }}
                      >
                        <Trash2 className="size-4 text-destructive" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {pageCount > 1 && (
        <Pager page={page} pageCount={pageCount} onChange={setPage} />
      )}

      {editorOpen && (
        <TemplateEditor
          mode={editing ? "edit" : "create"}
          draft={draft}
          setDraft={setDraft}
          onClose={() => {
            setEditorOpen(false);
            setEditing(null);
          }}
          onSave={() => (editing ? update.mutate() : create.mutate())}
          saving={create.isPending || update.isPending}
        />
      )}
    </div>
  );
}

function Pager({
  page,
  pageCount,
  onChange,
}: {
  page: number;
  pageCount: number;
  onChange: (n: number) => void;
}) {
  return (
    <div className="flex items-center justify-end gap-2">
      <Button
        variant="outline"
        size="sm"
        disabled={page <= 1}
        onClick={() => onChange(page - 1)}
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
        onClick={() => onChange(page + 1)}
      >
        <ChevronRight className="size-4" />
      </Button>
    </div>
  );
}

function TemplateEditor({
  mode,
  draft,
  setDraft,
  onClose,
  onSave,
  saving,
}: {
  mode: "create" | "edit";
  draft: Draft;
  setDraft: (d: Draft) => void;
  onClose: () => void;
  onSave: () => void;
  saving: boolean;
}) {
  const updateField = (i: number, patch: Partial<TemplateField>) => {
    const next = [...draft.fields];
    next[i] = { ...next[i], ...patch };
    setDraft({ ...draft, fields: next });
  };
  const addField = () =>
    setDraft({
      ...draft,
      fields: [
        ...draft.fields,
        {
          key: `field_${draft.fields.length + 1}`,
          label: "Untitled",
          field_type: "text",
          required: false,
        },
      ],
    });
  const removeField = (i: number) =>
    setDraft({
      ...draft,
      fields: draft.fields.filter((_, idx) => idx !== i),
    });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>
              {mode === "create" ? "New template" : "Edit template"}
            </CardTitle>
            <CardDescription>
              Fields define the form the field rep fills in for this
              verification type.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>Code *</Label>
            <Input
              value={draft.code}
              disabled={mode === "edit"}
              onChange={(e) => setDraft({ ...draft, code: e.target.value })}
            />
          </div>
          <div>
            <Label>Name *</Label>
            <Input
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
          </div>
          <div>
            <Label>Type *</Label>
            <select
              value={draft.type}
              onChange={(e) => setDraft({ ...draft, type: e.target.value })}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>SLA hours</Label>
            <Input
              type="number"
              value={draft.sla_hours}
              onChange={(e) => setDraft({ ...draft, sla_hours: e.target.value })}
            />
          </div>
          <div className="md:col-span-2">
            <Label>Description</Label>
            <Input
              value={draft.description}
              onChange={(e) =>
                setDraft({ ...draft, description: e.target.value })
              }
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              id="sig"
              type="checkbox"
              checked={draft.signature_required}
              onChange={(e) =>
                setDraft({ ...draft, signature_required: e.target.checked })
              }
            />
            <Label htmlFor="sig">Signature required</Label>
          </div>
          {mode === "edit" && (
            <div className="flex items-center gap-2">
              <input
                id="active"
                type="checkbox"
                checked={draft.is_active}
                onChange={(e) =>
                  setDraft({ ...draft, is_active: e.target.checked })
                }
              />
              <Label htmlFor="active">Active</Label>
            </div>
          )}

          <div className="md:col-span-2">
            <div className="flex items-center justify-between mb-2">
              <Label>Form fields ({draft.fields.length})</Label>
              <Button size="sm" variant="outline" onClick={addField}>
                <Plus className="size-3" /> Add field
              </Button>
            </div>
            <div className="space-y-2">
              {draft.fields.map((f, i) => (
                <div
                  key={i}
                  className="grid grid-cols-12 gap-2 rounded border border-brand-brown-50 p-2"
                >
                  <Input
                    className="col-span-3"
                    placeholder="key"
                    value={f.key}
                    onChange={(e) => updateField(i, { key: e.target.value })}
                  />
                  <Input
                    className="col-span-4"
                    placeholder="label"
                    value={f.label}
                    onChange={(e) => updateField(i, { label: e.target.value })}
                  />
                  <select
                    className="col-span-3 flex h-10 rounded-md border border-input bg-background px-2 py-2 text-sm"
                    value={f.field_type}
                    onChange={(e) =>
                      updateField(i, { field_type: e.target.value })
                    }
                  >
                    {FIELD_TYPES.map((ft) => (
                      <option key={ft} value={ft}>
                        {ft}
                      </option>
                    ))}
                  </select>
                  <label className="col-span-1 flex items-center justify-center text-xs">
                    <input
                      type="checkbox"
                      checked={f.required}
                      onChange={(e) =>
                        updateField(i, { required: e.target.checked })
                      }
                    />
                  </label>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="col-span-1"
                    onClick={() => removeField(i)}
                  >
                    <Trash2 className="size-3 text-destructive" />
                  </Button>
                </div>
              ))}
            </div>
          </div>

          <div className="md:col-span-2 flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              disabled={
                saving ||
                !draft.name ||
                (mode === "create" && !draft.code) ||
                draft.fields.length === 0
              }
              onClick={onSave}
            >
              {saving ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
