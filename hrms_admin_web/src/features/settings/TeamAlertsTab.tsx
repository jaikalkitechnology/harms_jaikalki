// Settings → Team alerts: the automatic nudges to managers and their
// people — when they go out and which are on.
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { BellRing, Save, Send } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api/client";

const V1 = "/api/v1";

interface AlertSettings {
  morning_digest: boolean;
  digest_time: string;
  plan_reminder: boolean;
  plan_reminder_time: string;
  task_escalation: boolean;
  escalate_after_days: number;
  weekly_summary: boolean;
  weekly_day: number;
  weekly_time: string;
  target_alerts: boolean;
  target_behind_by: number;
}
interface Message {
  title: string;
  body: string;
}

const api = {
  get: async () => (await apiClient.get<AlertSettings>(`${V1}/team/alerts/settings`)).data,
  put: async (b: Partial<AlertSettings>) =>
    (await apiClient.put<AlertSettings>(`${V1}/team/alerts/settings`, b)).data,
  run: async (job: string) => (await apiClient.post<Record<string, unknown>>(`${V1}/team/alerts/run/${job}`)).data,
  preview: async () =>
    (await apiClient.get<{ morning_digest: Message | null; weekly_summary: Message | null }>(`${V1}/team/alerts/preview`))
      .data,
};

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

function errDetail(e: unknown, fallback: string): string {
  return (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? fallback;
}

function Toggle({
  checked,
  onChange,
  title,
  hint,
  children,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  title: string;
  hint: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4 border-b border-brand-brown-50 py-4 last:border-0">
      <label className="flex min-w-0 flex-1 cursor-pointer items-start gap-3">
        <input type="checkbox" className="mt-1" checked={checked} onChange={(e) => onChange(e.target.checked)} />
        <span>
          <span className="block font-medium text-brand-brown-darker">{title}</span>
          <span className="block text-sm text-brand-brown-light">{hint}</span>
        </span>
      </label>
      {checked && <div className="flex flex-wrap items-center gap-2 text-sm">{children}</div>}
    </div>
  );
}

export function TeamAlertsTab() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["team-alerts"], queryFn: api.get });
  const { data: preview } = useQuery({ queryKey: ["team-alerts-preview"], queryFn: api.preview });
  const [d, setD] = useState<AlertSettings | null>(null);
  useEffect(() => {
    if (data) setD(data);
  }, [data]);

  const save = useMutation({
    mutationFn: () => api.put(d!),
    onSuccess: (s) => {
      qc.setQueryData(["team-alerts"], s);
      toast.success("Alert settings saved");
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });
  const run = useMutation({
    mutationFn: (job: string) => api.run(job),
    onSuccess: (r, job) => {
      const n = (r.sent ?? r.reminded ?? r.escalated ?? r.refreshed ?? 0) as number;
      toast.success(`${job.replace(/_/g, " ")}: ${n} sent`);
    },
    onError: (e) => toast.error(errDetail(e, "Could not send")),
  });

  if (!d) return <p className="text-sm text-brand-brown-light">Loading…</p>;
  const set = <K extends keyof AlertSettings>(k: K, v: AlertSettings[K]) => setD({ ...d, [k]: v });
  const dirty = JSON.stringify(d) !== JSON.stringify(data);
  const time = (k: "digest_time" | "plan_reminder_time" | "weekly_time") => (
    <Input type="time" className="w-32" value={d[k]} onChange={(e) => set(k, e.target.value)} />
  );
  const sendNow = (job: string) => (
    <Button
      variant="ghost"
      size="sm"
      className="gap-1"
      disabled={run.isPending}
      onClick={() => window.confirm("Send this now to everyone it applies to?") && run.mutate(job)}
    >
      <Send className="size-3.5" /> Send now
    </Button>
  );

  return (
    <div className="grid items-start gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BellRing className="size-5" /> Team alerts
          </CardTitle>
          <CardDescription>
            Automatic notifications in the app (and on phones) that keep managers and their people on
            track. Times are India time.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Toggle
            checked={d.morning_digest}
            onChange={(v) => set("morning_digest", v)}
            title="Morning digest to managers"
            hint="Who's absent, late or not in yet, who hasn't sent a morning plan, and overdue tasks — for everyone with a team."
          >
            at {time("digest_time")} {sendNow("morning_digest")}
          </Toggle>
          <Toggle
            checked={d.plan_reminder}
            onChange={(v) => set("plan_reminder", v)}
            title="Morning-plan reminder"
            hint="Nudges people who usually send a morning plan but haven't today."
          >
            at {time("plan_reminder_time")} {sendNow("plan_reminder")}
          </Toggle>
          <Toggle
            checked={d.task_escalation}
            onChange={(v) => set("task_escalation", v)}
            title="Escalate overdue tasks"
            hint="The day after a task is due, the person and whoever gave it are reminded. After that it goes one manager up the chain every few days."
          >
            every
            <Input
              type="number"
              min={1}
              max={30}
              className="w-16"
              value={d.escalate_after_days}
              onChange={(e) => set("escalate_after_days", Number(e.target.value))}
            />
            days {sendNow("task_escalation")}
          </Toggle>
          <Toggle
            checked={d.weekly_summary}
            onChange={(v) => set("weekly_summary", v)}
            title="Weekly summary to managers"
            hint="Last week's attendance, daily plans, tasks and target progress for their team and each sub-team."
          >
            <select
              className="h-9 rounded-md border border-input bg-card px-2"
              value={d.weekly_day}
              onChange={(e) => set("weekly_day", Number(e.target.value))}
            >
              {DAYS.map((name, i) => (
                <option key={name} value={i}>
                  {name}
                </option>
              ))}
            </select>
            at {time("weekly_time")} {sendNow("weekly_summary")}
          </Toggle>
          <Toggle
            checked={d.target_alerts}
            onChange={(v) => set("target_alerts", v)}
            title="Behind-target alerts"
            hint="With the weekly summary: people whose progress is well behind the calendar get a nudge, and their manager sees who they are."
          >
            when more than
            <Input
              type="number"
              min={5}
              max={60}
              className="w-16"
              value={d.target_behind_by}
              onChange={(e) => set("target_behind_by", Number(e.target.value))}
            />
            points behind
          </Toggle>
          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" disabled={!dirty} onClick={() => data && setD(data)}>
              Discard
            </Button>
            <Button className="gap-2" disabled={!dirty || save.isPending} onClick={() => save.mutate()}>
              <Save className="size-4" /> Save
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>What you'd get</CardTitle>
          <CardDescription>Your own digest and weekly summary right now (not sent).</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          {[
            ["Morning digest", preview?.morning_digest],
            ["Weekly summary", preview?.weekly_summary],
          ].map(([label, m]) => (
            <div key={label as string} className="rounded-xl border border-brand-brown-100 p-3">
              <div className="text-xs uppercase tracking-wide text-brand-gold-dark">{label as string}</div>
              {m ? (
                <>
                  <div className="mt-1 font-medium">{(m as Message).title}</div>
                  <div className="mt-1 whitespace-pre-line text-brand-brown-light">{(m as Message).body}</div>
                </>
              ) : (
                <div className="mt-1 text-brand-brown-light">Nothing — you have no team, or it's a day off.</div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
