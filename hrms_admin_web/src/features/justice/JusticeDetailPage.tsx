import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ArrowLeft, AlertTriangle, Eye, Lock, ShieldCheck } from "lucide-react";

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
import { COMPLAINT_TYPE_LABEL, justiceApi } from "@/lib/api/justice";

const ACTION_TYPES = [
  "acknowledged",
  "investigation_started",
  "comment",
  "warning_issued",
  "training_assigned",
  "transfer",
  "termination",
  "no_action",
];

export default function JusticeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const cid = Number(id);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: c, isLoading } = useQuery({
    queryKey: ["justice-detail", cid],
    queryFn: () => justiceApi.detail(cid),
    enabled: Number.isFinite(cid),
  });

  const [actionType, setActionType] = useState("comment");
  const [actionNotes, setActionNotes] = useState("");

  const addAction = useMutation({
    mutationFn: () => justiceApi.addAction(cid, actionType, actionNotes),
    onSuccess: () => {
      toast.success("Action recorded");
      setActionNotes("");
      queryClient.invalidateQueries({ queryKey: ["justice-detail", cid] });
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed";
      toast.error(detail);
    },
  });
  const resolve = useMutation({
    mutationFn: () => justiceApi.resolve(cid, "Closed by authority"),
    onSuccess: () => {
      toast.success("Complaint marked resolved");
      queryClient.invalidateQueries({ queryKey: ["justice-detail", cid] });
      queryClient.invalidateQueries({ queryKey: ["justice-inbox"] });
    },
  });

  if (isLoading || !c) return <LoadingScreen label="Loading complaint…" />;

  const isPosh =
    c.complaint_type === "sexual_harassment" ||
    c.complaint_type === "discrimination";

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate("/justice")}
        className="flex items-center gap-2 text-sm text-brand-brown-light hover:text-brand-brown-darker"
      >
        <ArrowLeft className="h-4 w-4" /> Back to inbox
      </button>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark flex items-center gap-2">
            ★ {c.ticket_number}
            {c.privacy_level === "anonymous" && (
              <span className="inline-flex items-center gap-1">
                <Lock className="h-3 w-3" /> Anonymous
              </span>
            )}
            {isPosh && (
              <span className="inline-flex items-center gap-1 text-error">
                <AlertTriangle className="h-3 w-3" /> POSH
              </span>
            )}
          </div>
          <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
            {c.subject}
          </h2>
          <p className="mt-1 text-sm text-brand-brown-light">
            {COMPLAINT_TYPE_LABEL[c.complaint_type] ?? c.complaint_type} ·
            severity {c.severity} · status {c.status.replace(/_/g, " ")}
          </p>
        </div>
        <div className="flex gap-2">
          {c.status !== "resolved" && c.status !== "withdrawn" && (
            <Button
              variant="gold"
              onClick={() => resolve.mutate()}
              disabled={resolve.isPending}
            >
              <ShieldCheck className="h-4 w-4" /> Resolve
            </Button>
          )}
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Complaint</CardTitle>
            <CardDescription>
              Decrypted on access · entry recorded in audit log
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Field label="Description" value={c.description} preserveWhitespace />
            <Field label="Desired outcome" value={c.desired_outcome} />
            <Field label="Incident date" value={c.incident_date ?? "—"} />
            <Field label="Incident location" value={c.incident_location ?? "—"} />
            <Field
              label="Submitted"
              value={new Date(c.submitted_at).toLocaleString()}
            />
            {c.deadline_at && (
              <Field
                label="Deadline"
                value={new Date(c.deadline_at).toLocaleDateString()}
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>People</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                Accused
              </div>
              {c.accused.length === 0 ? (
                <p className="text-brand-brown-light">None disclosed.</p>
              ) : (
                <ul className="space-y-1">
                  {c.accused.map((a) => (
                    <li key={a.id}>
                      {a.name ?? "—"}
                      {a.relationship_type && ` · ${a.relationship_type}`}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                Witnesses
              </div>
              {c.witnesses.length === 0 ? (
                <p className="text-brand-brown-light">None disclosed.</p>
              ) : (
                <ul className="space-y-1">
                  {c.witnesses.map((w) => (
                    <li key={w.id}>
                      {w.is_anonymous ? "Anonymous witness" : w.name ?? "—"}
                      {w.statement && (
                        <p className="text-xs text-brand-brown-light mt-0.5">
                          {w.statement}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                Evidence
              </div>
              {c.evidence.length === 0 ? (
                <p className="text-brand-brown-light">No evidence attached.</p>
              ) : (
                <ul className="space-y-1">
                  {c.evidence.map((e) => (
                    <li key={e.id} className="break-all">
                      {e.file_name ?? e.file_url ?? "—"}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>
              Record an <span className="display-em">action</span>
            </CardTitle>
            <CardDescription>
              Notes are encrypted at rest and visible only to authorised users.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid md:grid-cols-3 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="action_type">Action</Label>
                <select
                  id="action_type"
                  value={actionType}
                  onChange={(e) => setActionType(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
                >
                  {ACTION_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, " ")}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2 space-y-1.5">
                <Label htmlFor="action_notes">Notes</Label>
                <Input
                  id="action_notes"
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  placeholder="Investigation finding, decision, etc."
                />
              </div>
            </div>
            <div>
              <Button
                onClick={() => addAction.mutate()}
                disabled={addAction.isPending || !actionNotes.trim()}
              >
                Record action
              </Button>
            </div>

            <div className="pt-3">
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-2">
                History
              </div>
              {c.actions.length === 0 ? (
                <p className="text-sm text-brand-brown-light">No actions yet.</p>
              ) : (
                <ul className="space-y-1.5">
                  {c.actions.map((a) => (
                    <li
                      key={a.id}
                      className="text-sm border-l-2 border-brand-gold/40 pl-3"
                    >
                      <div className="font-medium">
                        {a.action_type.replace(/_/g, " ")}
                      </div>
                      <div className="text-xs text-brand-brown-light">
                        {new Date(a.action_date).toLocaleString()}
                      </div>
                      {a.notes && <p>{a.notes}</p>}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>
              Audit <span className="display-em">log</span>
            </CardTitle>
            <CardDescription>Every access is recorded.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm">
              {c.access_log.map((e) => (
                <li
                  key={e.id}
                  className="flex items-start justify-between border-b border-brand-brown-100/60 last:border-0 py-1.5"
                >
                  <div className="flex items-center gap-2">
                    <Eye className="h-3 w-3 text-brand-brown-light" />
                    <span className="font-mono text-xs">{e.action}</span>
                  </div>
                  <div className="text-xs text-brand-brown-light text-right">
                    {new Date(e.timestamp).toLocaleString()}
                    {e.user_id && ` · user #${e.user_id}`}
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  preserveWhitespace = false,
}: {
  label: string;
  value: string | null;
  preserveWhitespace?: boolean;
}) {
  return (
    <div>
      <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
        {label}
      </div>
      <div
        className={
          preserveWhitespace ? "whitespace-pre-line text-brand-brown-darker" : ""
        }
      >
        {value || "—"}
      </div>
    </div>
  );
}
