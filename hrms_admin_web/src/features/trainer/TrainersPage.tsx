import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Briefcase,
  ChevronLeft,
  ChevronRight,
  Pencil,
  Plus,
  Search,
  Star,
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
import { trainerApi, type Trainer } from "@/lib/api/trainer";
import { employeesApi } from "@/lib/api/employees";

const PAGE_SIZE = 12;

interface Draft {
  is_external: boolean;
  employee_id: number | "";
  full_name: string;
  headline: string;
  bio: string;
  contact_email: string;
  contact_phone: string;
  years_experience: string;
  hourly_rate: string;
  specializations: string;
  is_active: boolean;
}

const EMPTY_DRAFT: Draft = {
  is_external: false,
  employee_id: "",
  full_name: "",
  headline: "",
  bio: "",
  contact_email: "",
  contact_phone: "",
  years_experience: "0",
  hourly_rate: "",
  specializations: "",
  is_active: true,
};

export default function TrainersPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [externalFilter, setExternalFilter] = useState<"" | "true" | "false">(
    "",
  );
  const [specFilter, setSpecFilter] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);
  const [page, setPage] = useState(1);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<Trainer | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);

  const { data: trainers = [], isLoading } = useQuery({
    queryKey: ["trainers", search, externalFilter, specFilter, includeInactive],
    queryFn: () =>
      trainerApi.listTrainers({
        search: search.trim() || undefined,
        is_external:
          externalFilter === "" ? undefined : externalFilter === "true",
        specialization: specFilter.trim() || undefined,
        include_inactive: includeInactive,
      }),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });

  // Derive a list of all known specialisations for the filter dropdown.
  const specializations = useMemo(() => {
    const s = new Set<string>();
    trainers.forEach((t) =>
      t.specializations?.forEach((v) => v && s.add(v.trim())),
    );
    return Array.from(s).sort();
  }, [trainers]);

  const create = useMutation({
    mutationFn: () => trainerApi.createTrainer(draftToPayload(draft)),
    onSuccess: () => {
      toast.success("Trainer added");
      setEditorOpen(false);
      setDraft(EMPTY_DRAFT);
      qc.invalidateQueries({ queryKey: ["trainers"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not add trainer"),
  });

  const update = useMutation({
    mutationFn: () =>
      trainerApi.updateTrainer(editing!.id, draftToPayload(draft, true)),
    onSuccess: () => {
      toast.success("Trainer updated");
      setEditorOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["trainers"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not update trainer"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => trainerApi.deleteTrainer(id),
    onSuccess: () => {
      toast.success("Trainer deactivated");
      qc.invalidateQueries({ queryKey: ["trainers"] });
    },
    onError: () => toast.error("Could not deactivate"),
  });

  const openCreate = () => {
    setEditing(null);
    setDraft(EMPTY_DRAFT);
    setEditorOpen(true);
  };
  const openEdit = (t: Trainer) => {
    setEditing(t);
    setDraft({
      is_external: t.is_external,
      employee_id: t.employee_id ?? "",
      full_name: t.full_name,
      headline: t.headline ?? "",
      bio: t.bio ?? "",
      contact_email: t.contact_email ?? "",
      contact_phone: t.contact_phone ?? "",
      years_experience: String(t.years_experience),
      hourly_rate: t.hourly_rate ?? "",
      specializations: (t.specializations ?? []).join(", "),
      is_active: t.is_active,
    });
    setEditorOpen(true);
  };

  const pageCount = Math.max(1, Math.ceil(trainers.length / PAGE_SIZE));
  const pageRows = trainers.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (isLoading) return <LoadingScreen label="Loading trainers…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Trainer Marketplace
          </h1>
          <p className="text-sm text-brand-brown-light">
            {trainers.length} trainer{trainers.length === 1 ? "" : "s"} match
            current filters.
          </p>
        </div>
        <Button onClick={openCreate} className="gap-2">
          <Plus className="size-4" /> Add trainer
        </Button>
      </div>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-4">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search name / headline / bio / email…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9"
            />
          </div>
          <select
            value={externalFilter}
            onChange={(e) => {
              setExternalFilter(e.target.value as "" | "true" | "false");
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">Internal + external</option>
            <option value="false">Internal only</option>
            <option value="true">External only</option>
          </select>
          <select
            value={specFilter}
            onChange={(e) => {
              setSpecFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All specialisations</option>
            {specializations.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm md:col-span-4">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => {
                setIncludeInactive(e.target.checked);
                setPage(1);
              }}
            />
            Include inactive
          </label>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {pageRows.length === 0 ? (
          <Card className="md:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-brand-brown-light">
              No trainers match these filters.
            </CardContent>
          </Card>
        ) : (
          pageRows.map((t) => (
            <Card key={t.id} className={!t.is_active ? "opacity-60" : ""}>
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <CardTitle className="text-base truncate">
                      {t.full_name}
                    </CardTitle>
                    {t.headline && (
                      <CardDescription>{t.headline}</CardDescription>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${t.is_external ? "bg-info/15 text-info" : "bg-brand-gold/15 text-brand-gold-dark"}`}
                    >
                      {t.is_external ? "External" : "Internal"}
                    </span>
                    {!t.is_active && (
                      <span className="rounded-full bg-brand-brown-50 px-2 py-0.5 text-[10px] uppercase">
                        inactive
                      </span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex items-center gap-3 text-xs">
                  <span className="inline-flex items-center gap-1 text-brand-gold-dark">
                    <Star className="size-3 fill-current" />
                    {Number(t.rating_average).toFixed(1)}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Briefcase className="size-3" />
                    {t.sessions_completed} sessions
                  </span>
                  <span>{t.years_experience}y exp</span>
                </div>
                {t.contact_email && (
                  <div className="text-xs text-brand-brown-light truncate">
                    {t.contact_email}
                  </div>
                )}
                {t.specializations && t.specializations.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {t.specializations.map((s) => (
                      <span
                        key={s}
                        className="rounded bg-brand-brown-50 px-2 py-0.5 text-[10px]"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}
                <div className="flex items-center justify-end gap-1 pt-2">
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
                      if (confirm(`Deactivate trainer "${t.full_name}"?`))
                        remove.mutate(t.id);
                    }}
                  >
                    <Trash2 className="size-4 text-destructive" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

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

      {editorOpen && (
        <TrainerEditor
          mode={editing ? "edit" : "create"}
          draft={draft}
          setDraft={setDraft}
          employees={employees}
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

function draftToPayload(d: Draft, forUpdate = false): Record<string, unknown> {
  const specs = d.specializations
    ? d.specializations
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
    : [];
  const base: Record<string, unknown> = {
    full_name: d.full_name,
    headline: d.headline || null,
    bio: d.bio || null,
    contact_email: d.contact_email || null,
    contact_phone: d.contact_phone || null,
    years_experience: Number(d.years_experience) || 0,
    hourly_rate: d.hourly_rate ? Number(d.hourly_rate) : null,
    specializations: specs,
  };
  if (forUpdate) {
    base.is_active = d.is_active;
    return base;
  }
  return {
    ...base,
    is_external: d.is_external,
    employee_id: d.employee_id || null,
  };
}

function TrainerEditor({
  mode,
  draft,
  setDraft,
  employees,
  onClose,
  onSave,
  saving,
}: {
  mode: "create" | "edit";
  draft: Draft;
  setDraft: (d: Draft) => void;
  employees: {
    id: number;
    employee_code: string;
    first_name: string;
    last_name: string;
  }[];
  onClose: () => void;
  onSave: () => void;
  saving: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-3xl max-h-[92vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>
              {mode === "create" ? "Add trainer" : "Edit trainer"}
            </CardTitle>
            <CardDescription>
              Internal trainers must be linked to an existing employee. They
              can be marked inactive instead of deleted to keep historical
              session data intact.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          {mode === "create" && (
            <>
              <label className="md:col-span-2 flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={draft.is_external}
                  onChange={(e) =>
                    setDraft({ ...draft, is_external: e.target.checked })
                  }
                />
                External trainer
              </label>
              {!draft.is_external && (
                <div className="md:col-span-2">
                  <Label>Employee *</Label>
                  <select
                    value={draft.employee_id}
                    onChange={(e) =>
                      setDraft({
                        ...draft,
                        employee_id: e.target.value
                          ? Number(e.target.value)
                          : "",
                      })
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
              )}
            </>
          )}
          <div className="md:col-span-2">
            <Label>Full name *</Label>
            <Input
              value={draft.full_name}
              onChange={(e) => setDraft({ ...draft, full_name: e.target.value })}
            />
          </div>
          <div>
            <Label>Headline</Label>
            <Input
              value={draft.headline}
              onChange={(e) => setDraft({ ...draft, headline: e.target.value })}
            />
          </div>
          <div>
            <Label>Years experience</Label>
            <Input
              type="number"
              value={draft.years_experience}
              onChange={(e) =>
                setDraft({ ...draft, years_experience: e.target.value })
              }
            />
          </div>
          <div className="md:col-span-2">
            <Label>Bio</Label>
            <textarea
              value={draft.bio}
              onChange={(e) => setDraft({ ...draft, bio: e.target.value })}
              rows={3}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>
          <div>
            <Label>Contact email</Label>
            <Input
              value={draft.contact_email}
              onChange={(e) =>
                setDraft({ ...draft, contact_email: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Contact phone</Label>
            <Input
              value={draft.contact_phone}
              onChange={(e) =>
                setDraft({ ...draft, contact_phone: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Hourly rate (₹)</Label>
            <Input
              type="number"
              value={draft.hourly_rate}
              onChange={(e) =>
                setDraft({ ...draft, hourly_rate: e.target.value })
              }
            />
          </div>
          {mode === "edit" && (
            <label className="flex items-center gap-2 mt-7">
              <input
                type="checkbox"
                checked={draft.is_active}
                onChange={(e) =>
                  setDraft({ ...draft, is_active: e.target.checked })
                }
              />
              <span className="text-sm">Active</span>
            </label>
          )}
          <div className="md:col-span-2">
            <Label>Specialisations (comma-separated)</Label>
            <Input
              value={draft.specializations}
              onChange={(e) =>
                setDraft({ ...draft, specializations: e.target.value })
              }
              placeholder="POSH, Onboarding, Leadership"
            />
          </div>
          <div className="md:col-span-2 flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              disabled={
                saving ||
                !draft.full_name ||
                (mode === "create" && !draft.is_external && !draft.employee_id)
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
