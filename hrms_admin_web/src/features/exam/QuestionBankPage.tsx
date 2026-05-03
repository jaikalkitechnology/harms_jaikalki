import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil, Plus, Search, Trash2, X } from "lucide-react";

import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { examApi, type Question, type QuestionOption } from "@/lib/api/exam";
import { organizationApi } from "@/lib/api/organization";

interface OptionDraft {
  id?: number;
  option_text: string;
  is_correct: boolean;
  sort_order: number;
}

interface QuestionDraft {
  question_text: string;
  question_type: string;
  department_id: number | null;
  topic: string;
  difficulty: string;
  marks: number;
  time_seconds: number;
  explanation: string;
  status: string;
  options: OptionDraft[];
}

const QUESTION_TYPES = [
  "single_choice",
  "multiple_choice",
  "true_false",
  "fill_blank",
  "match_pairs",
  "short_answer",
];
const DIFFICULTIES = ["easy", "medium", "hard"];
const STATUSES = ["draft", "active", "retired"];

const EMPTY_DRAFT: QuestionDraft = {
  question_text: "",
  question_type: "single_choice",
  department_id: null,
  topic: "",
  difficulty: "medium",
  marks: 1,
  time_seconds: 60,
  explanation: "",
  status: "active",
  options: [
    { option_text: "", is_correct: true, sort_order: 0 },
    { option_text: "", is_correct: false, sort_order: 1 },
  ],
};

export default function QuestionBankPage() {
  const qc = useQueryClient();
  const [departmentId, setDepartmentId] = useState<number | "">("");
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [search, setSearch] = useState("");
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<Question | null>(null);
  const [draft, setDraft] = useState<QuestionDraft>(EMPTY_DRAFT);

  const { data: questions = [], isLoading } = useQuery({
    queryKey: ["questions", departmentId, topic, difficulty],
    queryFn: () =>
      examApi.listQuestions({
        department_id: departmentId === "" ? undefined : departmentId,
        topic: topic || undefined,
        difficulty: difficulty || undefined,
      }),
  });

  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: () => organizationApi.listDepartments(),
  });
  useEffect(() => undefined, [departments]);

  const filtered = useMemo(() => {
    if (!search.trim()) return questions;
    const q = search.toLowerCase();
    return questions.filter(
      (it) =>
        it.question_text.toLowerCase().includes(q) ||
        (it.topic ?? "").toLowerCase().includes(q),
    );
  }, [questions, search]);

  const topics = useMemo(() => {
    const set = new Set<string>();
    questions.forEach((q) => q.topic && set.add(q.topic));
    return Array.from(set).sort();
  }, [questions]);

  const create = useMutation({
    mutationFn: () =>
      examApi.createQuestion({
        ...draft,
        topic: draft.topic || null,
        department_id: draft.department_id,
        explanation: draft.explanation || null,
      }),
    onSuccess: () => {
      toast.success("Question added");
      setEditorOpen(false);
      setDraft(EMPTY_DRAFT);
      qc.invalidateQueries({ queryKey: ["questions"] });
    },
    onError: () => toast.error("Could not add question"),
  });

  const update = useMutation({
    mutationFn: () =>
      examApi.updateQuestion(editing!.id, {
        question_text: draft.question_text,
        question_type: draft.question_type,
        department_id: draft.department_id,
        topic: draft.topic || null,
        difficulty: draft.difficulty,
        marks: draft.marks,
        time_seconds: draft.time_seconds,
        explanation: draft.explanation || null,
        status: draft.status,
      }),
    onSuccess: () => {
      toast.success("Saved");
      setEditorOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["questions"] });
    },
    onError: () => toast.error("Save failed"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => examApi.deleteQuestion(id),
    onSuccess: () => {
      toast.success("Removed");
      qc.invalidateQueries({ queryKey: ["questions"] });
    },
    onError: () => toast.error("Could not delete"),
  });

  const togglePublish = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      examApi.updateQuestion(id, { status }),
    onSuccess: (_, vars) => {
      toast.success(
        vars.status === "active" ? "Published" : "Moved to draft",
      );
      qc.invalidateQueries({ queryKey: ["questions"] });
    },
    onError: () => toast.error("Could not update"),
  });

  const openCreate = () => {
    setEditing(null);
    setDraft(EMPTY_DRAFT);
    setEditorOpen(true);
  };
  const openEdit = (q: Question) => {
    setEditing(q);
    setDraft({
      question_text: q.question_text,
      question_type: q.question_type,
      department_id: q.department_id,
      topic: q.topic ?? "",
      difficulty: q.difficulty,
      marks: q.marks,
      time_seconds: q.time_seconds,
      explanation: q.explanation ?? "",
      status: q.status,
      options: (q.options ?? []).map((o: QuestionOption, i) => ({
        id: o.id,
        option_text: o.option_text,
        is_correct: o.is_correct,
        sort_order: i,
      })),
    });
    setEditorOpen(true);
  };

  if (isLoading) return <LoadingScreen label="Loading questions…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Exams · Question bank
          </div>
          <h1 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            Question <span className="display-em">bank</span>
          </h1>
          <p className="text-sm text-brand-brown-light mt-1">
            {filtered.length} question{filtered.length === 1 ? "" : "s"} ·
            tag with department + topic to scope per session.
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-1" /> New question
        </Button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <select
          value={departmentId}
          onChange={(e) =>
            setDepartmentId(e.target.value ? Number(e.target.value) : "")
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
        <select
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          className="h-10 rounded-md border border-input bg-card px-3 text-sm"
        >
          <option value="">All topics</option>
          {topics.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={difficulty}
          onChange={(e) => setDifficulty(e.target.value)}
          className="h-10 rounded-md border border-input bg-card px-3 text-sm"
        >
          <option value="">All difficulties</option>
          {DIFFICULTIES.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <div className="relative">
          <Search className="h-4 w-4 absolute left-2 top-1/2 -translate-y-1/2 text-brand-brown-light" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search…"
            className="pl-8"
          />
        </div>
      </div>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm min-w-[800px]">
            <thead className="text-left text-brand-brown-light bg-brand-brown-50">
              <tr>
                <th className="py-2 px-4">Question</th>
                <th>Type</th>
                <th>Topic</th>
                <th>Department</th>
                <th>Marks</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((q) => (
                <tr
                  key={q.id}
                  className="border-t border-brand-brown-50 hover:bg-brand-brown-50/30"
                >
                  <td className="py-2 px-4">
                    <div className="font-medium line-clamp-2 max-w-md">
                      {q.question_text}
                    </div>
                  </td>
                  <td className="text-brand-brown-light text-xs">
                    {q.question_type.replace("_", " ")}
                  </td>
                  <td className="text-brand-brown-light text-xs">
                    {q.topic ?? "—"}
                  </td>
                  <td className="text-brand-brown-light text-xs">
                    {departments.find((d) => d.id === q.department_id)?.name ??
                      "—"}
                  </td>
                  <td>{q.marks}</td>
                  <td>
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        q.status === "active"
                          ? "bg-success/15 text-success"
                          : q.status === "draft"
                          ? "bg-warning/15 text-warning"
                          : "bg-brand-brown-50 text-brand-brown-light"
                      }`}
                    >
                      {q.status}
                    </span>
                  </td>
                  <td className="text-right pr-4 whitespace-nowrap">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        togglePublish.mutate({
                          id: q.id,
                          status: q.status === "active" ? "draft" : "active",
                        })
                      }
                    >
                      {q.status === "active" ? "Unpublish" : "Publish"}
                    </Button>{" "}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => openEdit(q)}
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>{" "}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        if (confirm("Delete this question?")) remove.mutate(q.id);
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="text-center py-8 text-brand-brown-light"
                  >
                    No questions match the filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

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
  draft: QuestionDraft;
  setDraft: (v: QuestionDraft) => void;
  departments: { id: number; name: string }[];
  onClose: () => void;
  onSubmit: () => void;
  submitting: boolean;
}) {
  const setOpt = (idx: number, patch: Partial<OptionDraft>) => {
    setDraft({
      ...draft,
      options: draft.options.map((o, i) => (i === idx ? { ...o, ...patch } : o)),
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start md:items-center justify-center p-4 bg-black/40">
      <div className="bg-card rounded-xl border border-brand-brown-100 shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-brand-brown-100">
          <div className="font-display text-lg">
            {mode === "create" ? "New" : "Edit"} question
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 grid place-items-center rounded-lg hover:bg-brand-brown-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="overflow-y-auto p-4 space-y-3">
          <div>
            <Label>Question</Label>
            <textarea
              rows={3}
              className="w-full border border-brand-brown-50 rounded p-2 text-sm bg-card"
              value={draft.question_text}
              onChange={(e) =>
                setDraft({ ...draft, question_text: e.target.value })
              }
            />
          </div>
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <Label>Type</Label>
              <select
                className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
                value={draft.question_type}
                onChange={(e) =>
                  setDraft({ ...draft, question_type: e.target.value })
                }
              >
                {QUESTION_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.replace("_", " ")}
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
              <Label>Department</Label>
              <select
                className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
                value={draft.department_id ?? ""}
                onChange={(e) =>
                  setDraft({
                    ...draft,
                    department_id: e.target.value
                      ? Number(e.target.value)
                      : null,
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
              <Label>Topic / session</Label>
              <Input
                value={draft.topic}
                onChange={(e) => setDraft({ ...draft, topic: e.target.value })}
                placeholder="e.g. Onboarding-Q1"
              />
            </div>
            <div>
              <Label>Marks</Label>
              <Input
                type="number"
                min={1}
                max={20}
                value={draft.marks}
                onChange={(e) =>
                  setDraft({ ...draft, marks: Number(e.target.value) })
                }
              />
            </div>
            <div>
              <Label>Time (seconds)</Label>
              <Input
                type="number"
                min={10}
                max={900}
                value={draft.time_seconds}
                onChange={(e) =>
                  setDraft({ ...draft, time_seconds: Number(e.target.value) })
                }
              />
            </div>
            <div>
              <Label>Status (publish)</Label>
              <select
                className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
                value={draft.status}
                onChange={(e) =>
                  setDraft({ ...draft, status: e.target.value })
                }
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {mode === "create" && (
            <div>
              <Label>Options</Label>
              <div className="space-y-2 mt-1">
                {draft.options.map((o, i) => (
                  <div key={i} className="flex gap-2 items-center">
                    <input
                      type={
                        draft.question_type === "multiple_choice"
                          ? "checkbox"
                          : "radio"
                      }
                      checked={o.is_correct}
                      onChange={(e) => {
                        if (draft.question_type === "multiple_choice") {
                          setOpt(i, { is_correct: e.target.checked });
                        } else {
                          setDraft({
                            ...draft,
                            options: draft.options.map((x, j) => ({
                              ...x,
                              is_correct: j === i,
                            })),
                          });
                        }
                      }}
                    />
                    <Input
                      value={o.option_text}
                      onChange={(e) =>
                        setOpt(i, { option_text: e.target.value })
                      }
                      placeholder={`Option ${i + 1}`}
                    />
                    {draft.options.length > 2 && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          setDraft({
                            ...draft,
                            options: draft.options.filter((_, j) => j !== i),
                          })
                        }
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    setDraft({
                      ...draft,
                      options: [
                        ...draft.options,
                        {
                          option_text: "",
                          is_correct: false,
                          sort_order: draft.options.length,
                        },
                      ],
                    })
                  }
                >
                  <Plus className="h-3 w-3 mr-1" /> Add option
                </Button>
              </div>
              <div className="text-xs text-brand-brown-light mt-1">
                Options are only editable on creation. To rewrite a saved
                question's options, delete and re-add it.
              </div>
            </div>
          )}
          <div>
            <Label>Explanation (optional)</Label>
            <textarea
              rows={2}
              className="w-full border border-brand-brown-50 rounded p-2 text-sm bg-card"
              value={draft.explanation}
              onChange={(e) =>
                setDraft({ ...draft, explanation: e.target.value })
              }
            />
          </div>
        </div>
        <div className="p-4 border-t border-brand-brown-100 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            disabled={submitting || !draft.question_text}
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
