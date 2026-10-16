// Give a task, and the side panel for one task (status, details,
// comments). Shared by the Tasks page, My Team and the member panel.
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Send, Trash2, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { teamApi } from "@/lib/api/team";
import {
  PRIORITY,
  STATUS,
  tasksApi,
  type TaskPriority,
  type TaskStatus,
  type WorkTask,
} from "@/lib/api/tasks";
import { Modal } from "@/features/polish/assets/AssetDialogs";
import {
  Chip,
  Field,
  FormActions,
  SELECT_CLASS,
  errDetail,
  fmtDate,
  todayIso,
} from "@/features/employees/profile/ui";
import { cn } from "@/lib/utils";

const TEXTAREA = "flex w-full rounded-md border border-input bg-card px-3 py-2 text-sm";

export function invalidateTasks(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["tasks"] });
  qc.invalidateQueries({ queryKey: ["task"] });
  qc.invalidateQueries({ queryKey: ["team-overview"] });
  qc.invalidateQueries({ queryKey: ["team-member"] });
}

/** Everyone the signed-in user may give a task to. */
export function useAssignable() {
  return useQuery({
    queryKey: ["team-overview", "all", null, "assignable"],
    queryFn: () => teamApi.overview({ scope: "all" }),
    staleTime: 60_000,
    select: (d) =>
      [...d.members].sort((a, b) => a.name.localeCompare(b.name)).map((m) => ({
        id: m.employee_id,
        label: `${m.name}${m.designation ? ` · ${m.designation}` : ""}`,
      })),
  });
}

export function TaskStatusChip({ t }: { t: Pick<WorkTask, "status" | "is_overdue"> }) {
  if (t.is_overdue) return <Chip tone="error">Overdue</Chip>;
  const s = STATUS[t.status];
  return <Chip tone={s.tone}>{s.label}</Chip>;
}

export function AssignTaskModal({
  employeeId,
  employeeName,
  onClose,
}: {
  employeeId?: number;
  employeeName?: string;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const { data: people = [] } = useAssignable();
  const [assignee, setAssignee] = useState<number | "">(employeeId ?? "");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [due, setDue] = useState("");
  const [priority, setPriority] = useState<TaskPriority>("medium");

  const save = useMutation({
    mutationFn: () =>
      tasksApi.create({
        title: title.trim(),
        description: description.trim() || undefined,
        assigned_to: Number(assignee),
        due_date: due || undefined,
        priority,
      }),
    onSuccess: (t) => {
      toast.success(`Task given to ${t.assignee_name}`);
      invalidateTasks(qc);
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not create the task")),
  });

  return (
    <Modal
      title="Give a task"
      description="They get a notification in the app. If it runs late it's escalated up the reporting chain."
      onClose={onClose}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="To" className="col-span-full">
          {employeeId ? (
            <div className="rounded-md border border-brand-brown-100 px-3 py-2 text-sm">{employeeName}</div>
          ) : (
            <select
              className={SELECT_CLASS}
              value={assignee}
              onChange={(e) => setAssignee(e.target.value ? Number(e.target.value) : "")}
            >
              <option value="">Choose a person…</option>
              {people.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Field label="Task" className="col-span-full">
          <Input
            value={title}
            maxLength={200}
            placeholder="e.g. Send the revised quote to Kumar Traders"
            onChange={(e) => setTitle(e.target.value)}
          />
        </Field>
        <Field label="Details (optional)" className="col-span-full">
          <textarea
            className={TEXTAREA}
            rows={3}
            maxLength={5000}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </Field>
        <Field label="Due">
          <Input type="date" min={todayIso()} value={due} onChange={(e) => setDue(e.target.value)} />
        </Field>
        <Field label="Priority">
          <select
            className={SELECT_CLASS}
            value={priority}
            onChange={(e) => setPriority(e.target.value as TaskPriority)}
          >
            {(Object.keys(PRIORITY) as TaskPriority[]).map((p) => (
              <option key={p} value={p}>
                {PRIORITY[p].label}
              </option>
            ))}
          </select>
        </Field>
        <FormActions
          onCancel={onClose}
          onSave={() => save.mutate()}
          saving={save.isPending}
          disabled={!assignee || title.trim().length < 2}
          saveLabel="Give task"
        />
      </div>
    </Modal>
  );
}

export function TaskPanel({ taskId, onClose }: { taskId: number; onClose: () => void }) {
  const qc = useQueryClient();
  const { data: t } = useQuery({ queryKey: ["task", taskId], queryFn: () => tasksApi.get(taskId) });
  const { data: comments = [] } = useQuery({
    queryKey: ["task", taskId, "comments"],
    queryFn: () => tasksApi.comments(taskId),
  });
  const [comment, setComment] = useState("");
  const [editing, setEditing] = useState(false);

  const update = useMutation({
    mutationFn: (body: Parameters<typeof tasksApi.update>[1]) => tasksApi.update(taskId, body),
    onSuccess: () => {
      invalidateTasks(qc);
      setEditing(false);
    },
    onError: (e) => toast.error(errDetail(e, "Could not update the task")),
  });
  const remove = useMutation({
    mutationFn: () => tasksApi.remove(taskId),
    onSuccess: () => {
      toast.success("Task deleted");
      invalidateTasks(qc);
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not delete")),
  });
  const send = useMutation({
    mutationFn: () => tasksApi.addComment(taskId, comment.trim()),
    onSuccess: () => {
      setComment("");
      qc.invalidateQueries({ queryKey: ["task", taskId, "comments"] });
      qc.invalidateQueries({ queryKey: ["tasks"] });
    },
    onError: (e) => toast.error(errDetail(e, "Could not add the comment")),
  });

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30" onClick={onClose}>
      <aside
        className="flex h-full w-full max-w-lg flex-col bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
        aria-label="Task"
      >
        <div className="flex items-start gap-3 border-b border-brand-brown-50 px-5 py-4">
          <div className="min-w-0 flex-1">
            <div className="text-lg font-semibold">{t?.title ?? "…"}</div>
            {t && (
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-brand-brown-light">
                <TaskStatusChip t={t} />
                <Chip tone={PRIORITY[t.priority].tone}>{PRIORITY[t.priority].label}</Chip>
                <span>
                  For <span className="font-medium text-brand-brown-darker">{t.assignee_name}</span>
                  {t.assigner_name ? ` · from ${t.assigner_name}` : ""}
                </span>
              </div>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            <X className="size-4" />
          </Button>
        </div>
        {t && (
          <div className="flex-1 space-y-5 overflow-y-auto px-5 py-4">
            {editing ? (
              <EditForm t={t} saving={update.isPending} onCancel={() => setEditing(false)} onSave={(b) => update.mutate(b)} />
            ) : (
              <>
                <dl className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <dt className="text-xs text-brand-brown-light">Due</dt>
                    <dd className={cn("font-medium", t.is_overdue && "text-error")}>
                      {t.due_date ? fmtDate(t.due_date) : "No due date"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-brand-brown-light">Given</dt>
                    <dd className="font-medium">{t.created_at ? fmtDate(t.created_at) : "—"}</dd>
                  </div>
                  {t.completed_at && (
                    <div className="col-span-2">
                      <dt className="text-xs text-brand-brown-light">Completed</dt>
                      <dd className="font-medium text-success">
                        {fmtDate(t.completed_at)}
                        {t.completion_note ? ` — ${t.completion_note}` : ""}
                      </dd>
                    </div>
                  )}
                  {t.escalation_level > 1 && (
                    <div className="col-span-2 text-xs text-warning">
                      Escalated {t.escalation_level - 1} level{t.escalation_level > 2 ? "s" : ""} up for being late.
                    </div>
                  )}
                </dl>
                {t.description && <p className="whitespace-pre-line text-sm">{t.description}</p>}
                <div className="flex flex-wrap gap-2">
                  {(["open", "in_progress", "done"] as TaskStatus[]).map((s) => (
                    <Button
                      key={s}
                      size="sm"
                      variant={t.status === s ? "default" : "outline"}
                      disabled={update.isPending || t.status === s || (!t.can_manage && !t.is_mine)}
                      onClick={() => update.mutate({ status: s })}
                    >
                      {STATUS[s].label}
                    </Button>
                  ))}
                  {t.can_manage && (
                    <>
                      <Button size="sm" variant="ghost" onClick={() => setEditing(true)}>
                        Edit
                      </Button>
                      {t.status !== "cancelled" && (
                        <Button size="sm" variant="ghost" onClick={() => update.mutate({ status: "cancelled" })}>
                          Cancel task
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-error"
                        aria-label="Delete task"
                        onClick={() => window.confirm("Delete this task?") && remove.mutate()}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </>
                  )}
                </div>
              </>
            )}

            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-gold-dark">
                Comments
              </h3>
              {comments.length === 0 ? (
                <p className="text-sm text-brand-brown-light">No comments yet.</p>
              ) : (
                <ul className="space-y-2">
                  {comments.map((c) => (
                    <li key={c.id} className="rounded-lg bg-brand-brown-50/50 px-3 py-2 text-sm">
                      <div className="text-xs text-brand-brown-light">
                        <span className="font-medium text-brand-brown-darker">{c.author_name}</span>
                        {c.created_at ? ` · ${fmtDate(c.created_at)}` : ""}
                      </div>
                      <div className="whitespace-pre-line">{c.body}</div>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        )}
        <div className="flex gap-2 border-t border-brand-brown-50 px-5 py-3">
          <Input
            value={comment}
            placeholder="Write a comment…"
            onChange={(e) => setComment(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && comment.trim() && send.mutate()}
          />
          <Button aria-label="Send" disabled={!comment.trim() || send.isPending} onClick={() => send.mutate()}>
            <Send className="size-4" />
          </Button>
        </div>
      </aside>
    </div>
  );
}

function EditForm({
  t,
  saving,
  onCancel,
  onSave,
}: {
  t: WorkTask;
  saving: boolean;
  onCancel: () => void;
  onSave: (b: Parameters<typeof tasksApi.update>[1]) => void;
}) {
  const { data: people = [] } = useAssignable();
  const [title, setTitle] = useState(t.title);
  const [description, setDescription] = useState(t.description ?? "");
  const [due, setDue] = useState(t.due_date ?? "");
  const [priority, setPriority] = useState<TaskPriority>(t.priority);
  const [assignee, setAssignee] = useState(t.assigned_to);
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Field label="Task" className="col-span-full">
        <Input value={title} maxLength={200} onChange={(e) => setTitle(e.target.value)} />
      </Field>
      <Field label="Details" className="col-span-full">
        <textarea className={TEXTAREA} rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
      </Field>
      <Field label="Due">
        <Input type="date" value={due} onChange={(e) => setDue(e.target.value)} />
      </Field>
      <Field label="Priority">
        <select className={SELECT_CLASS} value={priority} onChange={(e) => setPriority(e.target.value as TaskPriority)}>
          {(Object.keys(PRIORITY) as TaskPriority[]).map((p) => (
            <option key={p} value={p}>
              {PRIORITY[p].label}
            </option>
          ))}
        </select>
      </Field>
      {people.length > 0 && (
        <Field label="Given to" className="col-span-full">
          <select className={SELECT_CLASS} value={assignee} onChange={(e) => setAssignee(Number(e.target.value))}>
            {!people.some((p) => p.id === t.assigned_to) && <option value={t.assigned_to}>{t.assignee_name}</option>}
            {people.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </Field>
      )}
      <FormActions
        onCancel={onCancel}
        saving={saving}
        disabled={title.trim().length < 2}
        onSave={() =>
          onSave({
            title: title.trim(),
            description: description.trim() || null,
            due_date: due || null,
            priority,
            ...(assignee !== t.assigned_to ? { assigned_to: assignee } : {}),
          })
        }
      />
    </div>
  );
}
