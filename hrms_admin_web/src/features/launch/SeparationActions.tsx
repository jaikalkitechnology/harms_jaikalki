import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil, Save, Trash2, Undo2, X } from "lucide-react";

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
import { launchApi, type Resignation } from "@/lib/api/launch";

const UNDOABLE = new Set([
  "accepted",
  "in_notice",
  "ndc_pending",
  "cleared",
  "rejected",
  "settled",
]);

const UNDO_LABEL: Record<string, string> = {
  settlement_undone: "Settlement undone — back to cleared",
  decision_undone: "Decision undone — back to manager review, employee restored",
  rejection_undone: "Rejection undone — back to manager review",
};

function errDetail(e: unknown, fallback: string): string {
  return (
    (e as { response?: { data?: { detail?: string } } })?.response?.data
      ?.detail ?? fallback
  );
}

/** Edit / Undo / Delete controls shared by the Resignations and
 * Resign / Terminate pages. */
export function SeparationActions({
  resignation,
  employeeLabel,
}: {
  resignation: Resignation;
  employeeLabel: string;
}) {
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["resignations"] });
    qc.invalidateQueries({ queryKey: ["separations"] });
    qc.invalidateQueries({ queryKey: ["employees"] });
    qc.invalidateQueries({ queryKey: ["employees-all"] });
  };

  const undo = useMutation({
    mutationFn: () => launchApi.undoSeparation(resignation.id),
    onSuccess: (res) => {
      toast.success(UNDO_LABEL[res.action] ?? "Undone");
      refresh();
    },
    onError: (e) => toast.error(errDetail(e, "Could not undo")),
  });

  const remove = useMutation({
    mutationFn: () => launchApi.deleteSeparation(resignation.id),
    onSuccess: () => {
      toast.success("Deleted — employee restored to active");
      refresh();
    },
    onError: (e) => toast.error(errDetail(e, "Could not delete")),
  });

  const canUndo = UNDOABLE.has(resignation.status);

  return (
    <>
      <div className="inline-flex items-center gap-1">
        <Button
          size="sm"
          variant="outline"
          onClick={() => setEditing(true)}
          aria-label="Edit"
          title="Edit"
        >
          <Pencil className="h-3 w-3" />
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={!canUndo || undo.isPending}
          onClick={() => {
            if (window.confirm(`Undo the last step for ${employeeLabel}?`)) {
              undo.mutate();
            }
          }}
          aria-label="Undo"
          title={canUndo ? "Undo last step" : "Nothing to undo"}
        >
          <Undo2 className="h-3 w-3" />
        </Button>
        <Button
          size="sm"
          variant="ghost"
          disabled={remove.isPending}
          onClick={() => {
            if (
              window.confirm(
                `Delete this separation for ${employeeLabel}? ` +
                  "The employee will be restored to active.",
              )
            ) {
              remove.mutate();
            }
          }}
          aria-label="Delete"
          title="Delete"
        >
          <Trash2 className="h-3 w-3 text-error" />
        </Button>
      </div>

      {editing && (
        <EditSeparationModal
          resignation={resignation}
          employeeLabel={employeeLabel}
          onClose={() => setEditing(false)}
          onSaved={() => {
            refresh();
            setEditing(false);
          }}
        />
      )}
    </>
  );
}

function EditSeparationModal({
  resignation,
  employeeLabel,
  onClose,
  onSaved,
}: {
  resignation: Resignation;
  employeeLabel: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [kind, setKind] = useState<"resignation" | "termination">(
    resignation.separation_type === "termination" ? "termination" : "resignation",
  );
  const [proposed, setProposed] = useState(resignation.proposed_last_working_day);
  const [actual, setActual] = useState(resignation.actual_last_working_day ?? "");
  const [notice, setNotice] = useState(resignation.notice_period_days);
  const [reason, setReason] = useState(resignation.reason ?? "");
  const [comment, setComment] = useState(resignation.manager_comment ?? "");

  const save = useMutation({
    mutationFn: () =>
      launchApi.updateSeparation(resignation.id, {
        separation_type: kind,
        proposed_last_working_day: proposed,
        actual_last_working_day: actual || null,
        notice_period_days: notice,
        reason: reason || null,
        manager_comment: comment || null,
      }),
    onSuccess: () => {
      toast.success("Separation updated");
      onSaved();
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
    >
      <Card className="w-full max-w-lg">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Edit separation</CardTitle>
            <CardDescription>{employeeLabel}</CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Type</Label>
            <div className="mt-1 flex gap-4">
              {(["resignation", "termination"] as const).map((k) => (
                <label key={k} className="flex items-center gap-2 text-sm capitalize">
                  <input
                    type="radio"
                    checked={kind === k}
                    onChange={() => setKind(k)}
                  />
                  {k}
                </label>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Proposed last working day</Label>
              <Input
                type="date"
                value={proposed}
                onChange={(e) => setProposed(e.target.value)}
              />
            </div>
            <div>
              <Label>Actual last working day</Label>
              <Input
                type="date"
                value={actual}
                onChange={(e) => setActual(e.target.value)}
              />
            </div>
          </div>
          <div>
            <Label>Notice period (days)</Label>
            <Input
              type="number"
              min={0}
              max={180}
              value={notice}
              onChange={(e) => setNotice(Number(e.target.value) || 0)}
            />
          </div>
          <div>
            <Label>Reason</Label>
            <Input value={reason} onChange={(e) => setReason(e.target.value)} />
          </div>
          <div>
            <Label>Internal comment</Label>
            <textarea
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="w-full rounded-md border border-brand-brown-50 bg-transparent p-2 text-sm"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={() => save.mutate()}
              disabled={save.isPending || !proposed}
            >
              <Save className="mr-1 h-4 w-4" />
              {save.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
