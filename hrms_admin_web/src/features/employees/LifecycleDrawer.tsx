import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { CheckCircle2, ChevronRight, Clock, GraduationCap, Undo2, X } from "lucide-react";

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
import { lifecycleApi, type LifecyclePhase } from "@/lib/api/employees";

const STAGE_TONE: Record<string, string> = {
  intern: "text-info",
  probation: "text-brand-gold-dark",
  confirmed: "text-success",
};

const STAGE_LABEL: Record<string, string> = {
  intern: "Intern (3-month default)",
  probation: "Probation (6-month default)",
  confirmed: "Confirmed",
};

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

function plusMonths(iso: string, m: number): string {
  const d = new Date(iso + "T00:00:00");
  d.setMonth(d.getMonth() + m);
  return d.toISOString().slice(0, 10);
}

export function LifecycleDrawer({
  employeeId,
  employeeName,
  onClose,
}: {
  employeeId: number;
  employeeName: string;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["lifecycle", employeeId],
    queryFn: () => lifecycleApi.get(employeeId),
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["lifecycle", employeeId] });
    qc.invalidateQueries({ queryKey: ["employees"] });
    refetch();
  };

  const [internStart, setInternStart] = useState(today());
  const [internMonths, setInternMonths] = useState(3);
  const [probStart, setProbStart] = useState(today());
  const [probMonths, setProbMonths] = useState(6);
  const [extEnd, setExtEnd] = useState(plusMonths(today(), 2));
  const [extReason, setExtReason] = useState("");
  const [confirmOn, setConfirmOn] = useState(today());

  const stage = data?.stage ?? "probation";

  const startIntern = useMutation({
    mutationFn: () =>
      lifecycleApi.startIntern(employeeId, {
        start_date: internStart,
        months: internMonths,
      }),
    onSuccess: () => {
      toast.success("Internship started");
      invalidate();
    },
    onError: (e: unknown) =>
      toast.error(errDetail(e) ?? "Could not start internship"),
  });

  const extendIntern = useMutation({
    mutationFn: () =>
      lifecycleApi.extendIntern(employeeId, {
        extension_end_date: extEnd,
        reason: extReason || undefined,
      }),
    onSuccess: () => {
      toast.success("Internship extended");
      invalidate();
    },
    onError: (e: unknown) =>
      toast.error(errDetail(e) ?? "Could not extend"),
  });

  const startProbation = useMutation({
    mutationFn: () =>
      lifecycleApi.startProbation(employeeId, {
        start_date: probStart,
        months: probMonths,
      }),
    onSuccess: () => {
      toast.success("Probation started");
      invalidate();
    },
    onError: (e: unknown) =>
      toast.error(errDetail(e) ?? "Could not start probation"),
  });

  const extendProbation = useMutation({
    mutationFn: () =>
      lifecycleApi.extendProbation(employeeId, {
        extension_end_date: extEnd,
        reason: extReason || undefined,
      }),
    onSuccess: () => {
      toast.success("Probation extended");
      invalidate();
    },
    onError: (e: unknown) =>
      toast.error(errDetail(e) ?? "Could not extend"),
  });

  const confirm = useMutation({
    mutationFn: () =>
      lifecycleApi.confirm(employeeId, { confirmed_on: confirmOn }),
    onSuccess: () => {
      toast.success("Employee confirmed");
      invalidate();
    },
    onError: (e: unknown) =>
      toast.error(errDetail(e) ?? "Could not confirm"),
  });

  const undo = useMutation({
    mutationFn: () => lifecycleApi.undo(employeeId),
    onSuccess: (res) => {
      const label =
        res.action === "confirm_undone"
          ? "Confirmation undone"
          : res.action === "extension_undone"
            ? `${res.phase === "intern" ? "Internship" : "Probation"} extension removed`
            : `${res.phase === "intern" ? "Internship" : "Probation"} removed`;
      toast.success(label);
      invalidate();
    },
    onError: (e: unknown) =>
      toast.error(errDetail(e) ?? "Nothing to undo"),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-2xl max-h-[92vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <GraduationCap className="h-5 w-5" /> Lifecycle · {employeeName}
            </CardTitle>
            <CardDescription>
              Intern (3-month default, extendable) → Probation (6-month
              default, extendable) → Confirmation. Non-sick leaves stay
              locked until confirmation.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-5">
          {isLoading && (
            <div className="text-sm text-brand-brown-light">Loading…</div>
          )}
          {data && (
            <>
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.2em]">
                  <span className="text-brand-brown-light">Stage:</span>
                  <span className={STAGE_TONE[stage]}>
                    {STAGE_LABEL[stage] ?? stage}
                  </span>
                  {data.confirmation_date && (
                    <span className="text-brand-brown-light">
                      · confirmed {data.confirmation_date}
                    </span>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (
                      window.confirm(
                        "Undo the most recent lifecycle change on this employee?",
                      )
                    ) {
                      undo.mutate();
                    }
                  }}
                  disabled={
                    undo.isPending || (data.history.length === 0 && !data.confirmation_date)
                  }
                >
                  <Undo2 className="h-4 w-4 mr-1" />
                  {undo.isPending ? "Undoing…" : "Undo last"}
                </Button>
              </div>

              {stage === "intern" || stage === "probation" ? (
                <div className="grid gap-2 rounded-md border border-brand-brown-50 p-3">
                  <Label className="text-xs uppercase tracking-[0.15em] text-brand-brown-light">
                    Extend current phase
                  </Label>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label>New end date</Label>
                      <Input
                        type="date"
                        value={extEnd}
                        onChange={(e) => setExtEnd(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label>Reason</Label>
                      <Input
                        value={extReason}
                        onChange={(e) => setExtReason(e.target.value)}
                        placeholder="e.g. Additional evaluation"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <Button
                      onClick={() =>
                        (stage === "intern"
                          ? extendIntern
                          : extendProbation
                        ).mutate()
                      }
                      disabled={
                        stage === "intern"
                          ? extendIntern.isPending
                          : extendProbation.isPending
                      }
                    >
                      <Clock className="h-4 w-4 mr-1" />
                      {stage === "intern"
                        ? "Extend internship"
                        : "Extend probation"}
                    </Button>
                  </div>
                </div>
              ) : null}

              {stage !== "confirmed" && (
                <div className="grid gap-2 rounded-md border border-brand-brown-50 p-3">
                  <Label className="text-xs uppercase tracking-[0.15em] text-brand-brown-light">
                    Move to next phase
                  </Label>
                  {stage === "intern" ? (
                    <>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <Label>Probation start</Label>
                          <Input
                            type="date"
                            value={probStart}
                            onChange={(e) => setProbStart(e.target.value)}
                          />
                        </div>
                        <div>
                          <Label>Probation months</Label>
                          <Input
                            type="number"
                            min={1}
                            max={24}
                            value={probMonths}
                            onChange={(e) =>
                              setProbMonths(Number(e.target.value) || 6)
                            }
                          />
                        </div>
                      </div>
                      <div className="flex justify-end">
                        <Button
                          onClick={() => startProbation.mutate()}
                          disabled={startProbation.isPending}
                        >
                          <ChevronRight className="h-4 w-4 mr-1" />
                          Start probation
                        </Button>
                      </div>
                    </>
                  ) : (
                    <div className="grid grid-cols-2 gap-2 items-end">
                      <div>
                        <Label>Confirmed on</Label>
                        <Input
                          type="date"
                          value={confirmOn}
                          onChange={(e) => setConfirmOn(e.target.value)}
                        />
                      </div>
                      <div className="flex justify-end">
                        <Button
                          onClick={() => confirm.mutate()}
                          disabled={confirm.isPending}
                        >
                          <CheckCircle2 className="h-4 w-4 mr-1" />
                          Confirm employee
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {stage === "confirmed" && (
                <div className="grid gap-2 rounded-md border border-brand-brown-50 p-3">
                  <Label className="text-xs uppercase tracking-[0.15em] text-brand-brown-light">
                    Start a fresh internship (rehire)
                  </Label>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label>Start date</Label>
                      <Input
                        type="date"
                        value={internStart}
                        onChange={(e) => setInternStart(e.target.value)}
                      />
                    </div>
                    <div>
                      <Label>Months</Label>
                      <Input
                        type="number"
                        min={1}
                        max={24}
                        value={internMonths}
                        onChange={(e) =>
                          setInternMonths(Number(e.target.value) || 3)
                        }
                      />
                    </div>
                  </div>
                  <div className="flex justify-end">
                    <Button
                      variant="outline"
                      onClick={() => startIntern.mutate()}
                      disabled={startIntern.isPending}
                    >
                      Start internship
                    </Button>
                  </div>
                </div>
              )}

              {data.stage === "confirmed" && !data.history.length && (
                <p className="text-xs text-brand-brown-light">
                  No lifecycle history — employee was confirmed directly.
                </p>
              )}
              {data.history.length > 0 && (
                <div>
                  <Label className="text-xs uppercase tracking-[0.15em] text-brand-brown-light">
                    History
                  </Label>
                  <div className="mt-1 divide-y divide-brand-brown-50 border border-brand-brown-50 rounded-md">
                    {data.history.map((h) => (
                      <PhaseRow key={h.id} phase={h} />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PhaseRow({ phase }: { phase: LifecyclePhase }) {
  const end = phase.extension_end_date ?? phase.probation_end_date;
  return (
    <div className="flex items-center justify-between px-3 py-2 text-xs">
      <div>
        <span
          className={
            "font-mono uppercase tracking-[0.15em] " +
            (phase.phase === "intern"
              ? "text-info"
              : "text-brand-gold-dark")
          }
        >
          {phase.phase}
        </span>
        <span className="ml-2 text-brand-brown-darker">
          {phase.probation_start_date} → {end}
        </span>
        {phase.is_extended && (
          <span className="ml-2 text-brand-brown-light">· extended</span>
        )}
      </div>
      <span
        className={
          "font-mono uppercase tracking-[0.15em] " +
          (phase.status === "confirmed"
            ? "text-success"
            : phase.status === "terminated"
              ? "text-error"
              : "text-brand-gold-dark")
        }
      >
        {phase.status.replace("_", " ")}
      </span>
    </div>
  );
}

function errDetail(e: unknown): string | undefined {
  return (
    (e as { response?: { data?: { detail?: string } } })?.response?.data
      ?.detail
  );
}

// Small stage badge for use in the list column.
export function StageBadge({
  employee,
}: {
  employee: {
    is_on_probation: boolean;
    date_of_joining: string | null;
  };
}) {
  // Coarse label from the row we already have — the drawer fetches the
  // canonical value if the operator opens it.
  const label = employee.is_on_probation ? "In onboarding" : "Confirmed";
  return (
    <span
      className={
        "text-[10px] font-mono uppercase tracking-[0.15em] " +
        (employee.is_on_probation
          ? "text-brand-gold-dark"
          : "text-success")
      }
    >
      {label}
    </span>
  );
}
