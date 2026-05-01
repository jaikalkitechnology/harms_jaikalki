import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Calendar } from "lucide-react";

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
import { performanceApi } from "@/lib/api/performance";

const STATUS_COLOR: Record<string, string> = {
  draft: "bg-brand-brown-50 text-brand-brown-darker",
  open: "bg-info/15 text-info",
  review: "bg-brand-gold/15 text-brand-gold-dark",
  calibration: "bg-warning/15 text-warning",
  closed: "bg-success/15 text-success",
};

const NEXT_STATUS: Record<string, string[]> = {
  draft: ["open"],
  open: ["review", "closed"],
  review: ["calibration", "closed"],
  calibration: ["closed"],
  closed: [],
};

export default function CyclesPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [cycleType, setCycleType] = useState("quarterly");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [selfReviewDue, setSelfReviewDue] = useState("");
  const [managerReviewDue, setManagerReviewDue] = useState("");

  const { data: cycles = [], isLoading } = useQuery({
    queryKey: ["performance-cycles"],
    queryFn: performanceApi.listCycles,
  });

  const create = useMutation({
    mutationFn: () =>
      performanceApi.createCycle({
        code,
        name,
        cycle_type: cycleType,
        period_start: periodStart,
        period_end: periodEnd,
        self_review_due: selfReviewDue || null,
        manager_review_due: managerReviewDue || null,
      }),
    onSuccess: () => {
      toast.success("Cycle created");
      setShowForm(false);
      setCode("");
      setName("");
      setPeriodStart("");
      setPeriodEnd("");
      qc.invalidateQueries({ queryKey: ["performance-cycles"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Could not create"),
  });

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      performanceApi.setCycleStatus(id, status),
    onSuccess: () => {
      toast.success("Updated");
      qc.invalidateQueries({ queryKey: ["performance-cycles"] });
    },
    onError: () => toast.error("Could not update"),
  });

  if (isLoading) return <LoadingScreen label="Loading cycles…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Performance Cycles
          </h1>
          <p className="text-sm text-brand-brown-light">
            {cycles.length} cycle{cycles.length === 1 ? "" : "s"} configured.
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
          <Plus className="size-4" />
          {showForm ? "Cancel" : "New cycle"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create cycle</CardTitle>
            <CardDescription>
              Open the cycle when employees are ready to log goals and submit
              self reviews.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Code *</Label>
              <Input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Q3-2026"
              />
            </div>
            <div>
              <Label>Name *</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div>
              <Label>Type</Label>
              <select
                value={cycleType}
                onChange={(e) => setCycleType(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="half_yearly">Half-yearly</option>
                <option value="annual">Annual</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label>Period start *</Label>
                <Input
                  type="date"
                  value={periodStart}
                  onChange={(e) => setPeriodStart(e.target.value)}
                />
              </div>
              <div>
                <Label>Period end *</Label>
                <Input
                  type="date"
                  value={periodEnd}
                  onChange={(e) => setPeriodEnd(e.target.value)}
                />
              </div>
            </div>
            <div>
              <Label>Self-review due</Label>
              <Input
                type="date"
                value={selfReviewDue}
                onChange={(e) => setSelfReviewDue(e.target.value)}
              />
            </div>
            <div>
              <Label>Manager-review due</Label>
              <Input
                type="date"
                value={managerReviewDue}
                onChange={(e) => setManagerReviewDue(e.target.value)}
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                disabled={
                  !code || !name || !periodStart || !periodEnd || create.isPending
                }
                onClick={() => create.mutate()}
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {cycles.map((c) => (
          <Card key={c.id}>
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base">{c.name}</CardTitle>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${STATUS_COLOR[c.status] ?? ""}`}
                >
                  {c.status}
                </span>
              </div>
              <CardDescription className="font-mono text-xs">
                {c.code} · {c.cycle_type}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex items-center gap-1 text-xs">
                <Calendar className="size-3" />
                {c.period_start} → {c.period_end}
              </div>
              {c.self_review_due && (
                <div className="text-xs text-brand-brown-light">
                  Self review due: {c.self_review_due}
                </div>
              )}
              {c.manager_review_due && (
                <div className="text-xs text-brand-brown-light">
                  Manager review due: {c.manager_review_due}
                </div>
              )}
              <div className="flex flex-wrap gap-2 pt-2">
                {(NEXT_STATUS[c.status] ?? []).map((next) => (
                  <Button
                    key={next}
                    size="sm"
                    variant={next === "closed" ? "destructive" : "outline"}
                    onClick={() =>
                      setStatus.mutate({ id: c.id, status: next })
                    }
                  >
                    Move to {next}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
