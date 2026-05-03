import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Award,
  CheckCircle2,
  Clock,
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
import { examApi, type ExamSummary, type Question } from "@/lib/api/exam";
import { lmsApi } from "@/lib/api/lms";

const TYPE_COLOR: Record<string, string> = {
  practice: "bg-info/15 text-info",
  assessment: "bg-warning/15 text-warning",
  certification: "bg-brand-gold/15 text-brand-gold-dark",
  mandatory: "bg-error/15 text-error",
};

const EXAM_TYPES = ["practice", "assessment", "certification", "mandatory"];

interface ExamDraft {
  code: string;
  title: string;
  description: string;
  course_id: number | null;
  exam_type: string;
  total_questions: number;
  time_limit_minutes: number;
  passing_percentage: number;
  attempts_allowed: number;
  cooldown_hours: number;
  shuffle_questions: boolean;
  shuffle_options: boolean;
  negative_marking: boolean;
}

const EMPTY_DRAFT: ExamDraft = {
  code: "",
  title: "",
  description: "",
  course_id: null,
  exam_type: "assessment",
  total_questions: 10,
  time_limit_minutes: 30,
  passing_percentage: 60,
  attempts_allowed: 3,
  cooldown_hours: 24,
  shuffle_questions: true,
  shuffle_options: true,
  negative_marking: false,
};

export default function ExamsPage() {
  const qc = useQueryClient();
  const [showDrafts, setShowDrafts] = useState(true);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<ExamSummary | null>(null);
  const [draft, setDraft] = useState<ExamDraft>(EMPTY_DRAFT);
  const [pickedQuestionIds, setPickedQuestionIds] = useState<number[]>([]);
  const [autoFillEnabled, setAutoFillEnabled] = useState(true);
  const [questionsTouched, setQuestionsTouched] = useState(false);

  const { data: exams = [], isLoading } = useQuery({
    queryKey: ["exams", showDrafts],
    queryFn: () => examApi.listExams({ include_unpublished: showDrafts }),
  });
  const { data: courses = [] } = useQuery({
    queryKey: ["courses-for-exams"],
    queryFn: () => lmsApi.listCourses({ include_unpublished: true }),
  });
  // Bank questions filtered to the currently-selected course (if any),
  // used by the editor's question picker.
  const { data: bankQuestions = [] } = useQuery({
    queryKey: ["bank-questions", draft.course_id],
    queryFn: () =>
      examApi.listQuestions({
        course_id: draft.course_id ?? undefined,
        status: "active",
      }),
    enabled: editorOpen,
  });

  const filtered = useMemo(() => exams, [exams]);

  const publish = useMutation({
    mutationFn: ({ id, on }: { id: number; on: boolean }) =>
      examApi.publish(id, on),
    onSuccess: (_, vars) => {
      toast.success(vars.on ? "Published" : "Unpublished");
      qc.invalidateQueries({ queryKey: ["exams"] });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(err?.response?.data?.detail ?? "Could not update"),
  });

  const create = useMutation({
    mutationFn: async () => {
      const created = await examApi.createExam({
        ...draft,
        question_ids: pickedQuestionIds,
      });
      // If a course is set and the user didn't manually pick yet,
      // auto-fill from the course's question bank.
      if (
        draft.course_id != null &&
        pickedQuestionIds.length === 0 &&
        autoFillEnabled
      ) {
        const bank = await examApi.listQuestions({
          course_id: draft.course_id,
        });
        const ids = bank.map((q) => q.id);
        if (ids.length > 0) {
          await examApi.setExamQuestions(created.id, ids);
        }
      }
      return created;
    },
    onSuccess: () => {
      toast.success("Exam created");
      setEditorOpen(false);
      setDraft(EMPTY_DRAFT);
      setPickedQuestionIds([]);
      qc.invalidateQueries({ queryKey: ["exams"] });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(err?.response?.data?.detail ?? "Create failed"),
  });

  const update = useMutation({
    mutationFn: async () => {
      await examApi.updateExam(editing!.id, {
        title: draft.title,
        description: draft.description || null,
        course_id: draft.course_id,
        exam_type: draft.exam_type,
        total_questions: draft.total_questions,
        time_limit_minutes: draft.time_limit_minutes,
        passing_percentage: draft.passing_percentage,
        attempts_allowed: draft.attempts_allowed,
        cooldown_hours: draft.cooldown_hours,
        shuffle_questions: draft.shuffle_questions,
        shuffle_options: draft.shuffle_options,
        negative_marking: draft.negative_marking,
      });
      // Sync question selection if the user touched it.
      if (questionsTouched) {
        await examApi.setExamQuestions(editing!.id, pickedQuestionIds);
      }
      return editing!;
    },
    onSuccess: () => {
      toast.success("Saved");
      setEditorOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["exams"] });
    },
    onError: () => toast.error("Save failed"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => examApi.deleteExam(id),
    onSuccess: () => {
      toast.success("Removed");
      qc.invalidateQueries({ queryKey: ["exams"] });
    },
    onError: () =>
      toast.error("Could not delete (exam may have past attempts)"),
  });

  const openCreate = () => {
    setEditing(null);
    setDraft(EMPTY_DRAFT);
    setPickedQuestionIds([]);
    setAutoFillEnabled(true);
    setQuestionsTouched(false);
    setEditorOpen(true);
  };
  const openEdit = (e: ExamSummary) => {
    setEditing(e);
    setDraft({
      code: e.code,
      title: e.title,
      description: e.description ?? "",
      course_id: e.course_id ?? null,
      exam_type: e.exam_type,
      total_questions: e.total_questions,
      time_limit_minutes: e.time_limit_minutes,
      passing_percentage: e.passing_percentage,
      attempts_allowed: e.attempts_allowed,
      // these aren't on the summary type — sensible defaults
      cooldown_hours: 24,
      shuffle_questions: true,
      shuffle_options: true,
      negative_marking: false,
    });
    setPickedQuestionIds([]);
    setAutoFillEnabled(false);
    setQuestionsTouched(false);
    setEditorOpen(true);
  };

  if (isLoading) return <LoadingScreen label="Loading exams…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Exams · Configuration
          </div>
          <h1 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            Examination <span className="display-em">setup</span>
          </h1>
          <p className="text-sm text-brand-brown-light mt-1">
            {filtered.length} exam{filtered.length === 1 ? "" : "s"} ·
            mobile app only sees published exams.
          </p>
        </div>
        <div className="flex gap-2 items-end">
          <label className="flex items-center gap-2 text-sm h-10">
            <input
              type="checkbox"
              checked={showDrafts}
              onChange={(e) => setShowDrafts(e.target.checked)}
            />
            Show drafts
          </label>
          <Button onClick={openCreate}>
            <Plus className="h-4 w-4 mr-1" /> New exam
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filtered.length === 0 ? (
          <Card className="md:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-brand-brown-light">
              No exams configured. Click "New exam" to add one.
            </CardContent>
          </Card>
        ) : (
          filtered.map((e) => (
            <Card key={e.id} className="flex flex-col">
              <CardHeader>
                <div className="flex items-start justify-between gap-2 flex-wrap">
                  <CardTitle className="text-base">{e.title}</CardTitle>
                  <div className="flex gap-1 flex-shrink-0">
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${
                        TYPE_COLOR[e.exam_type] ?? ""
                      }`}
                    >
                      {e.exam_type}
                    </span>
                    {e.is_published ? (
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
                  {e.code}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 space-y-2 text-sm">
                {e.description && (
                  <p className="text-brand-brown-light">{e.description}</p>
                )}
                <div className="flex gap-3 flex-wrap text-xs">
                  <span className="inline-flex items-center gap-1">
                    <Clock className="size-3" />
                    {e.time_limit_minutes} min
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Award className="size-3" />
                    Pass {e.passing_percentage}%
                  </span>
                  <span>
                    {e.total_questions} Qs · {e.attempts_allowed} attempts
                  </span>
                </div>
                <div className="pt-3 border-t border-brand-brown-50 mt-auto flex flex-wrap gap-1">
                  <Button
                    size="sm"
                    variant={e.is_published ? "outline" : "default"}
                    onClick={() => publish.mutate({ id: e.id, on: !e.is_published })}
                  >
                    <CheckCircle2 className="size-3 mr-1" />
                    {e.is_published ? "Unpublish" : "Publish"}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openEdit(e)}
                  >
                    <Pencil className="size-3" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      if (confirm(`Delete "${e.title}"?`)) remove.mutate(e.id);
                    }}
                  >
                    <Trash2 className="size-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {editorOpen && (
        <Editor
          mode={editing ? "edit" : "create"}
          draft={draft}
          setDraft={setDraft}
          courses={courses.map((c) => ({ id: c.id, title: c.title }))}
          bankQuestions={bankQuestions}
          pickedQuestionIds={pickedQuestionIds}
          setPickedQuestionIds={(ids) => {
            setPickedQuestionIds(ids);
            setQuestionsTouched(true);
          }}
          autoFillEnabled={autoFillEnabled}
          setAutoFillEnabled={setAutoFillEnabled}
          onClose={() => setEditorOpen(false)}
          onSubmit={() => (editing ? update.mutate() : create.mutate())}
          submitting={create.isPending || update.isPending}
        />
      )}
    </div>
  );
}

function Editor({
  mode,
  draft,
  setDraft,
  courses,
  bankQuestions,
  pickedQuestionIds,
  setPickedQuestionIds,
  autoFillEnabled,
  setAutoFillEnabled,
  onClose,
  onSubmit,
  submitting,
}: {
  mode: "create" | "edit";
  draft: ExamDraft;
  setDraft: (v: ExamDraft) => void;
  courses: { id: number; title: string }[];
  bankQuestions: Question[];
  pickedQuestionIds: number[];
  setPickedQuestionIds: (ids: number[]) => void;
  autoFillEnabled: boolean;
  setAutoFillEnabled: (v: boolean) => void;
  onClose: () => void;
  onSubmit: () => void;
  submitting: boolean;
}) {
  const togglePick = (id: number) => {
    if (pickedQuestionIds.includes(id))
      setPickedQuestionIds(pickedQuestionIds.filter((x) => x !== id));
    else setPickedQuestionIds([...pickedQuestionIds, id]);
  };
  const allFromBank = () =>
    setPickedQuestionIds(bankQuestions.map((q) => q.id));
  const clearPicks = () => setPickedQuestionIds([]);
  return (
    <div className="fixed inset-0 z-50 flex items-start md:items-center justify-center p-4 bg-black/40">
      <div className="bg-card rounded-xl border border-brand-brown-100 shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-brand-brown-100">
          <div className="font-display text-lg">
            {mode === "create" ? "New" : "Edit"} exam
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
            <Label>Course (links the exam to a course)</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.course_id ?? ""}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  course_id: e.target.value ? Number(e.target.value) : null,
                })
              }
            >
              <option value="">— None (standalone exam) —</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Type</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.exam_type}
              onChange={(e) =>
                setDraft({ ...draft, exam_type: e.target.value })
              }
            >
              {EXAM_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Total questions</Label>
            <Input
              type="number"
              min={1}
              max={200}
              value={draft.total_questions}
              onChange={(e) =>
                setDraft({ ...draft, total_questions: Number(e.target.value) })
              }
            />
          </div>
          <div>
            <Label>Time limit (min)</Label>
            <Input
              type="number"
              min={1}
              max={480}
              value={draft.time_limit_minutes}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  time_limit_minutes: Number(e.target.value),
                })
              }
            />
          </div>
          <div>
            <Label>Passing %</Label>
            <Input
              type="number"
              min={0}
              max={100}
              value={draft.passing_percentage}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  passing_percentage: Number(e.target.value),
                })
              }
            />
          </div>
          <div>
            <Label>Attempts allowed</Label>
            <Input
              type="number"
              min={1}
              max={20}
              value={draft.attempts_allowed}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  attempts_allowed: Number(e.target.value),
                })
              }
            />
          </div>
          <div>
            <Label>Cooldown (hours)</Label>
            <Input
              type="number"
              min={0}
              max={720}
              value={draft.cooldown_hours}
              onChange={(e) =>
                setDraft({ ...draft, cooldown_hours: Number(e.target.value) })
              }
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={draft.shuffle_questions}
              onChange={(e) =>
                setDraft({ ...draft, shuffle_questions: e.target.checked })
              }
            />
            Shuffle questions
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={draft.shuffle_options}
              onChange={(e) =>
                setDraft({ ...draft, shuffle_options: e.target.checked })
              }
            />
            Shuffle options
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={draft.negative_marking}
              onChange={(e) =>
                setDraft({ ...draft, negative_marking: e.target.checked })
              }
            />
            Negative marking
          </label>
        </div>

        {/* Question picker panel */}
        <div className="px-4 pb-4">
          <div className="border-t border-brand-brown-50 pt-4">
            <div className="flex items-center justify-between flex-wrap gap-2 mb-2">
              <div>
                <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                  Questions
                </div>
                <div className="text-sm">
                  {draft.course_id
                    ? `${bankQuestions.length} question${
                        bankQuestions.length === 1 ? "" : "s"
                      } in this course's bank · ${pickedQuestionIds.length} selected`
                    : "Pick a course to load its question bank, or leave blank for a standalone exam."}
                </div>
              </div>
              <div className="flex gap-2 flex-wrap">
                {mode === "create" && draft.course_id != null && (
                  <label className="flex items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={autoFillEnabled}
                      onChange={(e) => setAutoFillEnabled(e.target.checked)}
                    />
                    Auto-fill on save
                  </label>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  disabled={bankQuestions.length === 0}
                  onClick={allFromBank}
                >
                  Select all
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={pickedQuestionIds.length === 0}
                  onClick={clearPicks}
                >
                  Clear
                </Button>
              </div>
            </div>
            {bankQuestions.length > 0 && (
              <div className="border border-brand-brown-50 rounded max-h-56 overflow-y-auto">
                <table className="w-full text-sm">
                  <tbody>
                    {bankQuestions.map((q) => (
                      <tr
                        key={q.id}
                        className="border-b border-brand-brown-50 last:border-0 hover:bg-brand-brown-50/40 cursor-pointer"
                        onClick={() => togglePick(q.id)}
                      >
                        <td className="py-2 px-3 w-8">
                          <input
                            type="checkbox"
                            checked={pickedQuestionIds.includes(q.id)}
                            onChange={() => togglePick(q.id)}
                            onClick={(ev) => ev.stopPropagation()}
                          />
                        </td>
                        <td className="py-2 pr-3">
                          <div className="line-clamp-2">{q.question_text}</div>
                          <div className="text-xs text-brand-brown-light">
                            {q.topic ?? "no topic"} · {q.difficulty} · {q.marks}m
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {mode === "edit" && pickedQuestionIds.length === 0 && draft.course_id != null && (
              <div className="text-xs text-brand-brown-light mt-2">
                Save without ticking anything to leave the existing
                question set unchanged.
              </div>
            )}
          </div>
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
