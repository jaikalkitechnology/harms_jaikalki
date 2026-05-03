import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Award,
  BookOpen,
  CheckCircle2,
  Pencil,
  Plus,
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
import { lmsApi, type CourseRich } from "@/lib/api/lms";
import { lookupsApi } from "@/lib/api/employees";
import { organizationApi } from "@/lib/api/organization";

const CATEGORY_COLOR: Record<string, string> = {
  onboarding: "bg-info/15 text-info",
  compliance: "bg-error/15 text-error",
  technical: "bg-brand-gold/15 text-brand-gold-dark",
  leadership: "bg-warning/15 text-warning",
  soft_skills: "bg-success/15 text-success",
  product: "bg-info/25 text-info",
  other: "bg-brand-brown-50 text-brand-brown-darker",
};

const CATEGORIES = [
  "onboarding",
  "compliance",
  "technical",
  "leadership",
  "soft_skills",
  "product",
  "other",
];

const DIFFICULTIES = ["beginner", "intermediate", "advanced"];

interface CourseDraft {
  code: string;
  title: string;
  description: string;
  category: string;
  department_id: number | null;
  difficulty: string;
  estimated_hours: number;
  thumbnail_url: string;
  is_mandatory: boolean;
  validity_months: number | null;
  points: number;
}

const EMPTY_DRAFT: CourseDraft = {
  code: "",
  title: "",
  description: "",
  category: "other",
  department_id: null,
  difficulty: "beginner",
  estimated_hours: 1,
  thumbnail_url: "",
  is_mandatory: false,
  validity_months: null,
  points: 10,
};

export default function CoursesPage() {
  const qc = useQueryClient();
  const [category, setCategory] = useState("");
  const [departmentId, setDepartmentId] = useState<number | "">("");
  const [showDrafts, setShowDrafts] = useState(true);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<CourseRich | null>(null);
  const [draft, setDraft] = useState<CourseDraft>(EMPTY_DRAFT);

  const { data: courses = [], isLoading } = useQuery({
    queryKey: ["lms-courses", category, departmentId, showDrafts],
    queryFn: () =>
      lmsApi.listCourses({
        category: category || undefined,
        department_id: departmentId === "" ? undefined : departmentId,
        include_unpublished: showDrafts,
      }),
  });

  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: () => organizationApi.listDepartments(),
  });

  // Suppress lint via empty side-effect — we only need departments cached.
  useEffect(() => undefined, [departments]);

  const filtered = useMemo(() => courses, [courses]);

  const publish = useMutation({
    mutationFn: ({ id, on }: { id: number; on: boolean }) =>
      lmsApi.publish(id, on),
    onSuccess: (_, vars) => {
      toast.success(vars.on ? "Published" : "Unpublished");
      qc.invalidateQueries({ queryKey: ["lms-courses"] });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(err?.response?.data?.detail ?? "Publish failed"),
  });

  const create = useMutation({
    mutationFn: () =>
      lmsApi.createCourse({
        ...draft,
        description: draft.description || undefined,
        thumbnail_url: draft.thumbnail_url || undefined,
        validity_months: draft.validity_months || undefined,
      }),
    onSuccess: () => {
      toast.success("Course created");
      setEditorOpen(false);
      setDraft(EMPTY_DRAFT);
      qc.invalidateQueries({ queryKey: ["lms-courses"] });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(err?.response?.data?.detail ?? "Create failed"),
  });

  const update = useMutation({
    mutationFn: () =>
      lmsApi.updateCourse(editing!.id, {
        title: draft.title,
        description: draft.description || null,
        category: draft.category,
        department_id: draft.department_id,
        difficulty: draft.difficulty,
        estimated_hours: draft.estimated_hours,
        thumbnail_url: draft.thumbnail_url || null,
        is_mandatory: draft.is_mandatory,
        validity_months: draft.validity_months,
        points: draft.points,
      }),
    onSuccess: () => {
      toast.success("Saved");
      setEditorOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["lms-courses"] });
    },
    onError: () => toast.error("Save failed"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => lmsApi.deleteCourse(id),
    onSuccess: () => {
      toast.success("Removed");
      qc.invalidateQueries({ queryKey: ["lms-courses"] });
    },
    onError: () => toast.error("Could not delete (course may have enrollments)"),
  });

  const openCreate = () => {
    setEditing(null);
    setDraft(EMPTY_DRAFT);
    setEditorOpen(true);
  };
  const openEdit = (c: CourseRich) => {
    setEditing(c);
    setDraft({
      code: c.code,
      title: c.title,
      description: c.description ?? "",
      category: c.category,
      department_id: c.department_id ?? null,
      difficulty: c.difficulty,
      estimated_hours: c.estimated_hours,
      thumbnail_url: c.thumbnail_url ?? "",
      is_mandatory: c.is_mandatory,
      validity_months: c.validity_months ?? null,
      points: c.points,
    });
    setEditorOpen(true);
  };

  if (isLoading) return <LoadingScreen label="Loading courses…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ LMS · Course Catalog
          </div>
          <h1 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            Course <span className="display-em">library</span>
          </h1>
          <p className="text-sm text-brand-brown-light mt-1">
            {filtered.length} course{filtered.length === 1 ? "" : "s"} ·
            mobile app shows only published courses, filtered by department.
          </p>
        </div>
        <div className="flex gap-2 flex-wrap items-end">
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="h-10 rounded-md border border-input bg-card px-3 text-sm"
          >
            <option value="">All categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c.replace("_", " ")}
              </option>
            ))}
          </select>
          <select
            value={departmentId}
            onChange={(e) =>
              setDepartmentId(
                e.target.value === "" ? "" : Number(e.target.value),
              )
            }
            className="h-10 rounded-md border border-input bg-card px-3 text-sm"
          >
            <option value="">All departments</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm h-10">
            <input
              type="checkbox"
              checked={showDrafts}
              onChange={(e) => setShowDrafts(e.target.checked)}
            />
            Drafts
          </label>
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4 mr-1" /> New course
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filtered.length === 0 ? (
          <Card className="md:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-brand-brown-light">
              <BookOpen className="mx-auto mb-3 size-10 text-brand-gold-dark" />
              No courses yet. Click "New course" to add one.
            </CardContent>
          </Card>
        ) : (
          filtered.map((c) => (
            <CourseCard
              key={c.id}
              course={c}
              departmentName={
                departments.find((d) => d.id === c.department_id)?.name ?? null
              }
              onTogglePublish={() =>
                publish.mutate({ id: c.id, on: !c.is_published })
              }
              onEdit={() => openEdit(c)}
              onDelete={() => {
                if (confirm(`Delete "${c.title}"?`)) remove.mutate(c.id);
              }}
            />
          ))
        )}
      </div>

      {editorOpen && (
        <Editor
          mode={editing ? "edit" : "create"}
          draft={draft}
          setDraft={setDraft}
          departments={departments}
          onClose={() => setEditorOpen(false)}
          onSubmit={() => (editing ? update.mutate() : create.mutate())}
          submitting={create.isPending || update.isPending}
        />
      )}
    </div>
  );
}

function CourseCard({
  course,
  departmentName,
  onTogglePublish,
  onEdit,
  onDelete,
}: {
  course: CourseRich;
  departmentName: string | null;
  onTogglePublish: () => void;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{course.title}</CardTitle>
          <div className="flex gap-1 flex-shrink-0">
            {course.is_mandatory && (
              <span className="rounded-full bg-error/15 px-2 py-0.5 text-[10px] uppercase text-error">
                Mandatory
              </span>
            )}
            {course.is_published ? (
              <span className="rounded-full bg-success/15 px-2 py-0.5 text-[10px] uppercase text-success">
                Published
              </span>
            ) : (
              <span className="rounded-full bg-warning/15 px-2 py-0.5 text-[10px] uppercase text-warning">
                Draft
              </span>
            )}
          </div>
        </div>
        <CardDescription className="font-mono text-xs">
          {course.code} · {course.estimated_hours}h · {course.difficulty}
          {departmentName && ` · ${departmentName}`}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 flex-1 flex flex-col">
        <div>
          <span
            className={`rounded-full px-2 py-0.5 text-xs ${
              CATEGORY_COLOR[course.category] ?? ""
            }`}
          >
            {course.category.replace("_", " ")}
          </span>
        </div>
        {course.description && (
          <p className="text-sm text-brand-brown-light flex-1">
            {course.description}
          </p>
        )}
        <div className="flex items-center justify-between text-sm pt-2 border-t border-brand-brown-50 mt-auto">
          <span className="inline-flex items-center gap-1 text-brand-gold-dark">
            <Award className="size-4" />
            {course.points} pts
          </span>
          <div className="flex gap-1">
            <Button
              size="sm"
              variant={course.is_published ? "outline" : "default"}
              onClick={onTogglePublish}
            >
              <CheckCircle2 className="size-3 mr-1" />
              {course.is_published ? "Unpublish" : "Publish"}
            </Button>
            <Button size="sm" variant="outline" onClick={onEdit}>
              <Pencil className="size-3" />
            </Button>
            <Button size="sm" variant="ghost" onClick={onDelete}>
              <Trash2 className="size-3" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function Editor({
  mode,
  draft,
  setDraft,
  departments,
  onClose,
  onSubmit,
  submitting,
}: {
  mode: "create" | "edit";
  draft: CourseDraft;
  setDraft: (v: CourseDraft) => void;
  departments: { id: number; name: string }[];
  onClose: () => void;
  onSubmit: () => void;
  submitting: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-start md:items-center justify-center p-4 bg-black/40">
      <div className="bg-card rounded-xl border border-brand-brown-100 shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-brand-brown-100">
          <div className="font-display text-lg">
            {mode === "create" ? "New" : "Edit"} course
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 grid place-items-center rounded-lg hover:bg-brand-brown-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="overflow-y-auto p-4 grid sm:grid-cols-2 gap-3">
          <div>
            <Label>Code</Label>
            <Input
              value={draft.code}
              disabled={mode === "edit"}
              onChange={(e) =>
                setDraft({ ...draft, code: e.target.value.toUpperCase() })
              }
            />
          </div>
          <div>
            <Label>Title</Label>
            <Input
              value={draft.title}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            />
          </div>
          <div className="sm:col-span-2">
            <Label>Description</Label>
            <textarea
              rows={3}
              className="w-full border border-brand-brown-50 rounded p-2 text-sm bg-card"
              value={draft.description}
              onChange={(e) =>
                setDraft({ ...draft, description: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Category</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.category}
              onChange={(e) => setDraft({ ...draft, category: e.target.value })}
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Department</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.department_id ?? ""}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  department_id: e.target.value ? Number(e.target.value) : null,
                })
              }
            >
              <option value="">All departments</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Difficulty</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.difficulty}
              onChange={(e) =>
                setDraft({ ...draft, difficulty: e.target.value })
              }
            >
              {DIFFICULTIES.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Estimated hours</Label>
            <Input
              type="number"
              min={1}
              max={200}
              value={draft.estimated_hours}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  estimated_hours: Number(e.target.value),
                })
              }
            />
          </div>
          <div>
            <Label>Points</Label>
            <Input
              type="number"
              min={0}
              value={draft.points}
              onChange={(e) =>
                setDraft({ ...draft, points: Number(e.target.value) })
              }
            />
          </div>
          <div>
            <Label>Validity (months)</Label>
            <Input
              type="number"
              value={draft.validity_months ?? ""}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  validity_months: e.target.value
                    ? Number(e.target.value)
                    : null,
                })
              }
            />
          </div>
          <div className="sm:col-span-2">
            <Label>Thumbnail URL</Label>
            <Input
              value={draft.thumbnail_url}
              onChange={(e) =>
                setDraft({ ...draft, thumbnail_url: e.target.value })
              }
            />
          </div>
          <label className="flex items-center gap-2 text-sm sm:col-span-2">
            <input
              type="checkbox"
              checked={draft.is_mandatory}
              onChange={(e) =>
                setDraft({ ...draft, is_mandatory: e.target.checked })
              }
            />
            Mandatory for assigned employees
          </label>
        </div>
        <div className="p-4 border-t border-brand-brown-100 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            disabled={submitting || !draft.code || !draft.title}
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

// silence unused-import warning
void lookupsApi;
