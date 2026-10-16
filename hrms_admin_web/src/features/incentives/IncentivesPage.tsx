// Incentives: schemes HR sets up, monthly runs that work out who earned
// what, the manager review, and HR approval into payroll.
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Calculator, Plus } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/auth";
import { TARGET_METRICS } from "@/lib/api/sales";
import { incentivesApi, type IncentiveScheme } from "@/lib/api/incentives";
import { cn } from "@/lib/utils";
import { Modal } from "@/features/polish/assets/AssetDialogs";
import { Chip, Field, FormActions, SELECT_CLASS, errDetail, fmtDate } from "@/features/employees/profile/ui";
import { inr } from "@/features/team/shared";
import { LinesTable, RunPanel } from "./RunPanel";
import { SchemeModal, slabText } from "./SchemeModal";

type Tab = "review" | "runs" | "schemes";

export default function IncentivesPage() {
  const isPayroll = useAuthStore((s) => s.hasPermission("payroll.run"));
  const [params, setParams] = useSearchParams();
  const tabs: { key: Tab; label: string }[] = [
    { key: "review", label: "To review" },
    ...(isPayroll
      ? ([
          { key: "runs", label: "Runs" },
          { key: "schemes", label: "Schemes" },
        ] as const)
      : []),
  ];
  const requested = params.get("tab") as Tab | null;
  const tab: Tab = tabs.some((t) => t.key === requested) ? requested! : isPayroll ? "runs" : "review";

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-2xl font-bold text-brand-brown-darker">Incentives</h1>
        <p className="text-sm text-brand-brown-light">
          Schemes pay on target progress, subject to eligibility rules. Each month the system works out
          who qualifies; direct managers review; HR approves and it's paid with that month's salary.
        </p>
      </div>
      <div className="inline-flex rounded-lg border border-brand-brown-100 bg-card p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setParams({ tab: t.key }, { replace: true })}
            className={cn(
              "rounded-md px-4 py-1.5 text-sm",
              tab === t.key ? "bg-brand-gold/15 text-brand-brown-darker" : "text-brand-brown-light",
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "review" && <ReviewTab />}
      {tab === "runs" && <RunsTab />}
      {tab === "schemes" && <SchemesTab />}
    </div>
  );
}

function ReviewTab() {
  const { data: lines = [], isLoading } = useQuery({
    queryKey: ["incentive-review"],
    queryFn: incentivesApi.reviewQueue,
  });
  const pending = lines.filter((l) => l.review_status === "pending").length;
  return (
    <Card>
      <CardContent className="p-0">
        <div className="border-b border-brand-brown-50 px-5 py-3 text-sm text-brand-brown-light">
          Incentives for your direct reports waiting for your decision. Approve the calculated amount,
          change it (with a reason) or reject it. {pending > 0 && <b className="text-brand-brown-darker">{pending} to review.</b>}
        </div>
        {isLoading ? (
          <p className="px-5 py-8 text-sm text-brand-brown-light">Loading…</p>
        ) : lines.length === 0 ? (
          <p className="px-5 py-12 text-center text-sm text-brand-brown-light">Nothing to review right now.</p>
        ) : (
          <LinesTable lines={lines} canReview showScheme />
        )}
      </CardContent>
    </Card>
  );
}

function RunsTab() {
  const qc = useQueryClient();
  const { data: runs = [] } = useQuery({ queryKey: ["incentive-runs"], queryFn: incentivesApi.runs });
  const [calc, setCalc] = useState(false);
  const [open, setOpen] = useState<number | null>(null);
  return (
    <>
      <div className="flex justify-end">
        <Button className="gap-2" onClick={() => setCalc(true)}>
          <Calculator className="size-4" /> Calculate a period
        </Button>
      </div>
      <Card>
        <CardContent className="p-0">
          {runs.length === 0 ? (
            <p className="px-5 py-12 text-center text-sm text-brand-brown-light">
              No runs yet. Runs are created automatically at the start of each month for active schemes, or
              calculate one now.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[820px] text-sm">
                <thead className="text-left text-xs uppercase tracking-wide text-brand-brown-light">
                  <tr className="border-b border-brand-brown-50">
                    <th className="px-5 py-2 font-medium">Scheme</th>
                    <th className="px-3 py-2 font-medium">Period</th>
                    <th className="px-3 py-2 font-medium">Paid with</th>
                    <th className="px-3 py-2 font-medium">Eligible</th>
                    <th className="px-3 py-2 font-medium">Total</th>
                    <th className="px-3 py-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((r) => (
                    <tr
                      key={r.id}
                      className="cursor-pointer border-b border-brand-brown-50 last:border-0 hover:bg-brand-brown-50/40"
                      onClick={() => setOpen(r.id)}
                    >
                      <td className="px-5 py-3 font-medium text-brand-brown-darker">{r.scheme_name}</td>
                      <td className="px-3 py-3">{r.period_label}</td>
                      <td className="px-3 py-3">
                        {new Date(r.payout_year, r.payout_month - 1, 1).toLocaleDateString("en-IN", { month: "short", year: "numeric" })}
                      </td>
                      <td className="px-3 py-3">
                        {r.eligible} of {r.lines}
                      </td>
                      <td className="px-3 py-3 font-medium">{inr(r.total_amount)}</td>
                      <td className="px-3 py-3">
                        {r.status === "approved" ? (
                          <Chip tone="success">{r.paid_lines ? "In payroll" : "Approved"}</Chip>
                        ) : (
                          <Chip tone="warning">
                            Under review{r.pending_review ? ` · ${r.pending_review} left` : ""}
                          </Chip>
                        )}
                        {r.approved_at && (
                          <div className="mt-0.5 text-[11px] text-brand-brown-light">{fmtDate(r.approved_at)}</div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
      {calc && (
        <CalculateModal
          onClose={() => setCalc(false)}
          onDone={(id) => {
            setCalc(false);
            qc.invalidateQueries({ queryKey: ["incentive-runs"] });
            setOpen(id);
          }}
        />
      )}
      {open && <RunPanel runId={open} onClose={() => setOpen(null)} />}
    </>
  );
}

function CalculateModal({ onClose, onDone }: { onClose: () => void; onDone: (runId: number) => void }) {
  const { data: schemes = [] } = useQuery({ queryKey: ["incentive-schemes"], queryFn: incentivesApi.schemes });
  const active = schemes.filter((s) => s.is_active);
  const last = new Date();
  last.setDate(0);
  const ym = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  const [schemeId, setSchemeId] = useState<number | "">("");
  const [period, setPeriod] = useState(ym(last));
  const [payout, setPayout] = useState(ym(last));
  const run = useMutation({
    mutationFn: () =>
      incentivesApi.calculate({
        scheme_id: Number(schemeId),
        period_date: `${period}-01`,
        payout_year: Number(payout.slice(0, 4)),
        payout_month: Number(payout.slice(5, 7)),
      }),
    onSuccess: (r) => {
      toast.success(`${r.scheme_name} · ${r.period_label}: ${r.eligible} of ${r.lines} eligible`);
      onDone(r.id);
    },
    onError: (e) => toast.error(errDetail(e, "Could not calculate")),
  });
  return (
    <Modal
      title="Calculate incentives"
      description="Works out each covered employee's progress and eligibility. Managers are asked to review."
      onClose={onClose}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Scheme" className="col-span-full">
          <select className={SELECT_CLASS} value={schemeId} onChange={(e) => setSchemeId(e.target.value ? Number(e.target.value) : "")}>
            <option value="">Choose a scheme…</option>
            {active.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.period_type})
              </option>
            ))}
          </select>
        </Field>
        <Field label="Period (month)" help="For quarterly schemes, any month in the quarter.">
          <Input type="month" value={period} onChange={(e) => setPeriod(e.target.value)} />
        </Field>
        <Field label="Pay with salary of">
          <Input type="month" value={payout} onChange={(e) => setPayout(e.target.value)} />
        </Field>
        <FormActions
          onCancel={onClose}
          onSave={() => run.mutate()}
          saving={run.isPending}
          disabled={!schemeId || !period || !payout}
          saveLabel="Calculate"
        />
      </div>
    </Modal>
  );
}

function SchemesTab() {
  const qc = useQueryClient();
  const { data: schemes = [] } = useQuery({ queryKey: ["incentive-schemes"], queryFn: incentivesApi.schemes });
  const [editing, setEditing] = useState<IncentiveScheme | "new" | null>(null);
  const toggle = useMutation({
    mutationFn: (s: IncentiveScheme) => incentivesApi.updateScheme(s.id, { is_active: !s.is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["incentive-schemes"] }),
    onError: (e) => toast.error(errDetail(e, "Could not change")),
  });
  return (
    <>
      <div className="flex justify-end">
        <Button className="gap-2" onClick={() => setEditing("new")}>
          <Plus className="size-4" /> New scheme
        </Button>
      </div>
      {schemes.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-sm text-brand-brown-light">
            No schemes yet. A scheme says what's paid for which target progress — e.g. 80% of target → ₹2,000,
            100% → ₹5,000 — and who qualifies.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {schemes.map((s) => (
            <Card key={s.id} className={cn(!s.is_active && "opacity-70")}>
              <CardContent className="space-y-3 p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-semibold text-brand-brown-darker">{s.name}</div>
                    <div className="text-xs text-brand-brown-light">
                      {TARGET_METRICS.find((m) => m.value === s.metric)?.label} target · {s.period_type}
                    </div>
                  </div>
                  {s.is_active ? <Chip tone="success">Active</Chip> : <Chip>Off</Chip>}
                </div>
                {s.description && <p className="text-sm text-brand-brown-light">{s.description}</p>}
                <div className="flex flex-wrap gap-1.5">
                  {s.slabs.map((sl) => (
                    <Chip key={sl.min_pct} tone="gold">
                      {slabText(s, sl)}
                    </Chip>
                  ))}
                  {s.max_payout && <Chip>max {inr(s.max_payout)}</Chip>}
                </div>
                <ul className="list-inside list-disc text-xs text-brand-brown-light">
                  {s.min_attendance_pct != null && <li>Attendance at least {s.min_attendance_pct}%</li>}
                  {s.confirmed_only && <li>Confirmed staff only (not on probation)</li>}
                  {s.exclude_notice && <li>Not serving notice</li>}
                  {s.no_warning_days && <li>No warning letter in the last {s.no_warning_days} days</li>}
                  {s.min_tenure_days && <li>At least {s.min_tenure_days} days with the company</li>}
                  {(s.department_ids?.length || s.category_codes?.length || s.designation_ids?.length) && (
                    <li>Only selected departments / categories / designations</li>
                  )}
                </ul>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => setEditing(s)}>
                    Edit
                  </Button>
                  <Button size="sm" variant="ghost" disabled={toggle.isPending} onClick={() => toggle.mutate(s)}>
                    {s.is_active ? "Switch off" : "Switch on"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      {editing && <SchemeModal scheme={editing === "new" ? null : editing} onClose={() => setEditing(null)} />}
    </>
  );
}
