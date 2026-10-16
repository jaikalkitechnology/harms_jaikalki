// Tasks: what your team is working on, what you've given out, and
// what's been given to you.
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { MessageSquare, Plus } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PRIORITY, tasksApi, type TaskFilter, type TaskView } from "@/lib/api/tasks";
import { cn } from "@/lib/utils";
import { Chip, fmtDate } from "@/features/employees/profile/ui";
import { AssignTaskModal, TaskPanel, TaskStatusChip } from "./TaskDialogs";

const VIEWS: { key: TaskView; label: string }[] = [
  { key: "team", label: "My team's tasks" },
  { key: "given", label: "Given by me" },
  { key: "mine", label: "Given to me" },
];
const FILTERS: { key: TaskFilter; label: string }[] = [
  { key: "open", label: "Open" },
  { key: "overdue", label: "Overdue" },
  { key: "done", label: "Done" },
  { key: "all", label: "All" },
];

export default function TasksPage() {
  const [params, setParams] = useSearchParams();
  const view = (params.get("view") as TaskView) || "team";
  const filter = (params.get("status") as TaskFilter) || "open";
  const [q, setQ] = useState("");
  const [assigning, setAssigning] = useState(false);
  const [open, setOpen] = useState<number | null>(null);
  const set = (k: string, v: string) =>
    setParams(
      (p) => {
        p.set(k, v);
        return p;
      },
      { replace: true },
    );

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ["tasks", view, filter],
    queryFn: () => tasksApi.list({ view, status: filter }),
  });
  const query = q.trim().toLowerCase();
  const rows = query
    ? tasks.filter(
        (t) =>
          t.title.toLowerCase().includes(query) ||
          t.assignee_name.toLowerCase().includes(query) ||
          (t.assigner_name ?? "").toLowerCase().includes(query),
      )
    : tasks;
  const overdue = tasks.filter((t) => t.is_overdue).length;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold text-brand-brown-darker">Tasks</h1>
          <p className="text-sm text-brand-brown-light">
            Give tasks to people in your team. Late ones are escalated up the reporting chain.
          </p>
        </div>
        <Button className="gap-2" onClick={() => setAssigning(true)}>
          <Plus className="size-4" /> Give a task
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="inline-flex rounded-lg border border-brand-brown-100 bg-card p-1">
          {VIEWS.map((v) => (
            <button
              key={v.key}
              type="button"
              onClick={() => set("view", v.key)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm",
                view === v.key ? "bg-brand-gold/15 text-brand-brown-darker" : "text-brand-brown-light",
              )}
            >
              {v.label}
            </button>
          ))}
        </div>
        <div className="inline-flex rounded-lg border border-brand-brown-100 bg-card p-1">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              type="button"
              onClick={() => set("status", f.key)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm",
                filter === f.key ? "bg-brand-gold/15 text-brand-brown-darker" : "text-brand-brown-light",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
        <Input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search tasks or people"
          className="ml-auto w-64"
        />
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="border-b border-brand-brown-50 px-5 py-2 text-xs text-brand-brown-light">
            {tasks.length} task{tasks.length === 1 ? "" : "s"}
            {overdue ? <span className="text-error"> · {overdue} overdue</span> : null}
          </div>
          {isLoading ? (
            <p className="px-5 py-8 text-sm text-brand-brown-light">Loading…</p>
          ) : rows.length === 0 ? (
            <p className="px-5 py-12 text-center text-sm text-brand-brown-light">
              {view === "mine" ? "Nothing has been given to you." : "No tasks here."}
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[820px] text-sm">
                <thead className="text-left text-xs uppercase tracking-wide text-brand-brown-light">
                  <tr className="border-b border-brand-brown-50">
                    <th className="px-5 py-2 font-medium">Task</th>
                    <th className="px-3 py-2 font-medium">{view === "mine" ? "From" : "For"}</th>
                    <th className="px-3 py-2 font-medium">Due</th>
                    <th className="px-3 py-2 font-medium">Priority</th>
                    <th className="px-3 py-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((t) => (
                    <tr
                      key={t.id}
                      className="cursor-pointer border-b border-brand-brown-50 last:border-0 hover:bg-brand-brown-50/40"
                      onClick={() => setOpen(t.id)}
                    >
                      <td className="px-5 py-3">
                        <div className="font-medium text-brand-brown-darker">{t.title}</div>
                        {t.comment_count > 0 && (
                          <div className="mt-0.5 flex items-center gap-1 text-xs text-brand-brown-light">
                            <MessageSquare className="size-3" /> {t.comment_count}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-3">
                        {view === "mine" ? t.assigner_name ?? "—" : t.assignee_name}
                        {view === "team" && t.assigner_name && (
                          <div className="text-xs text-brand-brown-light">from {t.assigner_name}</div>
                        )}
                      </td>
                      <td className={cn("px-3 py-3", t.is_overdue && "font-medium text-error")}>
                        {t.due_date ? fmtDate(t.due_date) : "—"}
                      </td>
                      <td className="px-3 py-3">
                        <Chip tone={PRIORITY[t.priority].tone}>{PRIORITY[t.priority].label}</Chip>
                      </td>
                      <td className="px-3 py-3">
                        <TaskStatusChip t={t} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {assigning && <AssignTaskModal onClose={() => setAssigning(false)} />}
      {open && <TaskPanel taskId={open} onClose={() => setOpen(null)} />}
    </div>
  );
}
