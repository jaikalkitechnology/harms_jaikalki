// One incentive run (HR), and the lines table used by both the run and
// the managers' review queue.
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { RefreshCw, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { fmtTargetValue } from "@/lib/api/sales";
import { REVIEW_STATUS, incentivesApi, type IncentiveLine } from "@/lib/api/incentives";
import { Modal } from "@/features/polish/assets/AssetDialogs";
import { Chip, Field, FormActions, errDetail } from "@/features/employees/profile/ui";
import { inr } from "@/features/team/shared";

function invalidate(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["incentive-review"] });
  qc.invalidateQueries({ queryKey: ["incentive-run"] });
  qc.invalidateQueries({ queryKey: ["incentive-runs"] });
}

export function LinesTable({
  lines,
  canReview,
  showScheme = false,
}: {
  lines: IncentiveLine[];
  canReview: boolean;
  showScheme?: boolean;
}) {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<{ line: IncentiveLine; action: "adjust" | "reject" } | null>(null);
  const review = useMutation({
    mutationFn: (v: { id: number; action: "approve" | "reset" }) => incentivesApi.review(v.id, { action: v.action }),
    onSuccess: () => invalidate(qc),
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[980px] text-sm">
        <thead className="text-left text-xs uppercase tracking-wide text-brand-brown-light">
          <tr className="border-b border-brand-brown-50">
            <th className="px-5 py-2 font-medium">Person</th>
            <th className="px-3 py-2 font-medium">Progress</th>
            <th className="px-3 py-2 font-medium">Attendance</th>
            <th className="px-3 py-2 font-medium">Eligibility</th>
            <th className="px-3 py-2 font-medium">Calculated</th>
            <th className="px-3 py-2 font-medium">To pay</th>
            <th className="px-3 py-2 font-medium">Review</th>
          </tr>
        </thead>
        <tbody>
          {lines.map((l) => (
            <tr key={l.id} className="border-b border-brand-brown-50 align-top last:border-0">
              <td className="px-5 py-3">
                <div className="font-medium text-brand-brown-darker">{l.employee_name}</div>
                <div className="text-xs text-brand-brown-light">
                  {[l.designation, l.manager_name && `reports to ${l.manager_name}`].filter(Boolean).join(" · ")}
                </div>
                {showScheme && (
                  <div className="mt-0.5 text-xs text-brand-gold-dark">
                    {l.scheme_name} · {l.period_label}
                  </div>
                )}
              </td>
              <td className="px-3 py-3">
                <div className="font-medium">{l.achievement_pct.toFixed(0)}%</div>
                <div className="text-xs text-brand-brown-light">
                  {fmtTargetValue(l.metric ?? undefined, l.achieved_amount)} of {fmtTargetValue(l.metric ?? undefined, l.target_amount)}
                </div>
                {l.slab_min_pct != null && <div className="text-xs text-brand-gold-dark">{l.slab_min_pct}% slab</div>}
              </td>
              <td className="px-3 py-3">{l.attendance_pct != null ? `${l.attendance_pct.toFixed(0)}%` : "—"}</td>
              <td className="max-w-[220px] px-3 py-3">
                {l.eligible ? (
                  <Chip tone="success">Eligible</Chip>
                ) : (
                  <ul className="space-y-0.5 text-xs text-error">
                    {l.reasons.map((r) => (
                      <li key={r}>• {r}</li>
                    ))}
                  </ul>
                )}
              </td>
              <td className="px-3 py-3">{inr(l.calculated_amount)}</td>
              <td className="px-3 py-3 font-semibold text-brand-brown-darker">
                {l.amount != null ? inr(l.amount) : "—"}
                {l.in_payroll && <div className="text-[11px] font-normal text-success">{l.paid ? "Paid" : "In payroll"}</div>}
              </td>
              <td className="px-3 py-3">
                <Chip tone={REVIEW_STATUS[l.review_status].tone}>{REVIEW_STATUS[l.review_status].label}</Chip>
                {l.review_note && <div className="mt-1 max-w-[200px] text-xs text-brand-brown-light">“{l.review_note}”</div>}
                {canReview && l.run_status === "review" && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {l.review_status !== "approved" && (
                      <Button size="sm" variant="outline" disabled={review.isPending} onClick={() => review.mutate({ id: l.id, action: "approve" })}>
                        Approve
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" onClick={() => setEditing({ line: l, action: "adjust" })}>
                      Change
                    </Button>
                    {l.review_status !== "rejected" && (
                      <Button size="sm" variant="ghost" className="text-error" onClick={() => setEditing({ line: l, action: "reject" })}>
                        Reject
                      </Button>
                    )}
                    {l.review_status !== "pending" && (
                      <Button size="sm" variant="ghost" onClick={() => review.mutate({ id: l.id, action: "reset" })}>
                        Undo
                      </Button>
                    )}
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {editing && <DecisionModal {...editing} onClose={() => setEditing(null)} />}
    </div>
  );
}

function DecisionModal({ line, action, onClose }: { line: IncentiveLine; action: "adjust" | "reject"; onClose: () => void }) {
  const qc = useQueryClient();
  const [amount, setAmount] = useState(String(Number(line.amount ?? line.calculated_amount)));
  const [note, setNote] = useState("");
  const save = useMutation({
    mutationFn: () =>
      incentivesApi.review(line.id, { action, note: note.trim(), ...(action === "adjust" ? { amount: Number(amount) } : {}) }),
    onSuccess: () => {
      invalidate(qc);
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });
  return (
    <Modal
      title={action === "adjust" ? `Change ${line.employee_name}'s incentive` : `Reject ${line.employee_name}'s incentive`}
      description={`Calculated: ${inr(line.calculated_amount)}${line.eligible ? "" : " (not eligible)"}`}
      onClose={onClose}
    >
      <div className="grid gap-4">
        {action === "adjust" && (
          <Field label="Amount to pay (₹)">
            <Input type="number" min={0} value={amount} onChange={(e) => setAmount(e.target.value)} />
          </Field>
        )}
        <Field label="Reason (HR and the employee's record keep it)">
          <Input value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} />
        </Field>
        <FormActions
          onCancel={onClose}
          onSave={() => save.mutate()}
          saving={save.isPending}
          disabled={!note.trim() || (action === "adjust" && amount === "")}
          saveLabel={action === "adjust" ? "Save amount" : "Reject"}
        />
      </div>
    </Modal>
  );
}

export function RunPanel({ runId, onClose }: { runId: number; onClose: () => void }) {
  const qc = useQueryClient();
  const { data: r } = useQuery({ queryKey: ["incentive-run", runId], queryFn: () => incentivesApi.run(runId) });
  const [approvePending, setApprovePending] = useState(false);
  const act = (fn: () => Promise<unknown>, ok: string) =>
    fn()
      .then(() => {
        toast.success(ok);
        invalidate(qc);
      })
      .catch((e) => toast.error(errDetail(e, "Could not do that")));

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/30" onClick={onClose}>
      <aside className="flex h-full w-full max-w-6xl flex-col bg-card shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start gap-3 border-b border-brand-brown-50 px-5 py-4">
          <div className="min-w-0 flex-1">
            <div className="text-lg font-semibold">{r ? `${r.scheme_name} · ${r.period_label}` : "…"}</div>
            {r && (
              <div className="text-xs text-brand-brown-light">
                {r.eligible} of {r.lines} eligible · {inr(r.total_amount)} to pay · paid with{" "}
                {new Date(r.payout_year, r.payout_month - 1, 1).toLocaleDateString("en-IN", { month: "long", year: "numeric" })} salary
                {r.pending_review > 0 && ` · ${r.pending_review} not reviewed yet`}
              </div>
            )}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            <X className="size-4" />
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto">{r && <LinesTable lines={r.lines_detail} canReview />}</div>
        {r && (
          <div className="flex flex-wrap items-center gap-3 border-t border-brand-brown-50 px-5 py-3">
            {r.status === "review" ? (
              <>
                <Button variant="outline" className="gap-2" onClick={() => act(() => incentivesApi.recalculate(r.id), "Recalculated")}>
                  <RefreshCw className="size-4" /> Recalculate
                </Button>
                <label className="ml-auto flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={approvePending} onChange={(e) => setApprovePending(e.target.checked)} />
                  Also approve lines managers haven't reviewed
                </label>
                <Button
                  onClick={() =>
                    act(() => incentivesApi.approve(r.id, approvePending), "Approved — it will be paid with that month's payroll")
                  }
                >
                  Approve for payroll
                </Button>
              </>
            ) : (
              <>
                <Chip tone="success">{r.paid_lines ? "Included in payroll" : "Approved"}</Chip>
                <Button variant="outline" className="ml-auto" onClick={() => act(() => incentivesApi.reopen(r.id), "Reopened for review")}>
                  Reopen
                </Button>
              </>
            )}
          </div>
        )}
      </aside>
    </div>
  );
}
