import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { CheckCircle2, XCircle, FileText } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { launchApi, type Resignation } from "@/lib/api/launch";

const STATUS_COLOR: Record<string, string> = {
  manager_review: "bg-info/15 text-info",
  in_notice: "bg-brand-gold/15 text-brand-gold-dark",
  ndc_pending: "bg-warning/15 text-warning",
  cleared: "bg-success/15 text-success",
  settled: "bg-brand-brown-50 text-brand-brown-darker",
  rejected: "bg-error/15 text-error",
};

export default function ResignationsPage() {
  const qc = useQueryClient();
  const [target, setTarget] = useState<Resignation | null>(null);
  const [comment, setComment] = useState("");
  const [amount, setAmount] = useState("");
  const [notes, setNotes] = useState("");

  const { data: items = [], isLoading } = useQuery({
    queryKey: ["pending-resignations"],
    queryFn: () => launchApi.pendingResignations(),
  });

  const decide = useMutation({
    mutationFn: ({ id, accept }: { id: number; accept: boolean }) =>
      launchApi.decideResignation(id, accept, comment),
    onSuccess: () => {
      toast.success("Saved");
      setComment("");
      qc.invalidateQueries({ queryKey: ["pending-resignations"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Failed"),
  });

  const updateNdc = useMutation({
    mutationFn: ({
      id,
      updates,
    }: {
      id: number;
      updates: Record<string, boolean>;
    }) => launchApi.updateNdc(id, updates),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pending-resignations"] });
    },
  });

  const settle = useMutation({
    mutationFn: ({ id }: { id: number }) =>
      launchApi.settleResignation(id, Number(amount), notes || undefined),
    onSuccess: () => {
      toast.success("Settlement recorded");
      setTarget(null);
      setAmount("");
      setNotes("");
      qc.invalidateQueries({ queryKey: ["pending-resignations"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Failed"),
  });

  if (isLoading) return <LoadingScreen label="Loading resignations…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Resignations
        </h1>
        <p className="text-sm text-brand-brown-light">
          {items.length} active resignation
          {items.length === 1 ? "" : "s"} across the funnel.
        </p>
      </div>

      {items.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-brand-brown-light">
            No active resignations.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {items.map((r) => {
            const ndc = r.ndc_checklist ?? {};
            const ndcKeys = Object.keys(ndc);
            const ndcChecked = ndcKeys.filter((k) => ndc[k]).length;
            return (
              <Card key={r.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base">
                      Employee #{r.employee_id} · {r.proposed_last_working_day}
                    </CardTitle>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${STATUS_COLOR[r.status] ?? ""}`}
                    >
                      {r.status.replaceAll("_", " ")}
                    </span>
                  </div>
                  <CardDescription>
                    Notice {r.notice_period_days} days · Requested{" "}
                    {new Date(r.requested_at).toLocaleDateString()}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  {r.reason && (
                    <p>
                      <span className="text-brand-brown-light">Reason: </span>
                      {r.reason}
                    </p>
                  )}

                  {r.status === "manager_review" && (
                    <div className="flex items-center gap-2">
                      <Input
                        placeholder="Optional comment"
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                      />
                      <Button
                        variant="outline"
                        className="gap-1"
                        onClick={() =>
                          decide.mutate({ id: r.id, accept: true })
                        }
                      >
                        <CheckCircle2 className="size-4" />
                        Accept
                      </Button>
                      <Button
                        variant="destructive"
                        className="gap-1"
                        onClick={() =>
                          decide.mutate({ id: r.id, accept: false })
                        }
                      >
                        <XCircle className="size-4" />
                        Reject
                      </Button>
                    </div>
                  )}

                  {(r.status === "in_notice" || r.status === "ndc_pending") &&
                    ndcKeys.length > 0 && (
                      <div className="rounded-md border border-brand-brown-50 p-3">
                        <div className="text-xs font-semibold uppercase text-brand-gold-dark mb-2">
                          NDC checklist · {ndcChecked}/{ndcKeys.length}
                        </div>
                        <div className="grid grid-cols-2 gap-1">
                          {ndcKeys.map((k) => (
                            <label
                              key={k}
                              className="flex items-center gap-2 text-xs"
                            >
                              <input
                                type="checkbox"
                                checked={ndc[k] ?? false}
                                onChange={(e) =>
                                  updateNdc.mutate({
                                    id: r.id,
                                    updates: { [k]: e.target.checked },
                                  })
                                }
                              />
                              {k.replaceAll("_", " ")}
                            </label>
                          ))}
                        </div>
                      </div>
                    )}

                  {r.status === "cleared" && (
                    <div className="rounded-md border border-success/30 bg-success/5 p-3 space-y-2">
                      <div className="flex items-center gap-1 text-success font-semibold text-xs">
                        <CheckCircle2 className="size-4" />
                        NDC cleared — ready for final settlement
                      </div>
                      {target?.id === r.id ? (
                        <div className="space-y-2">
                          <Input
                            type="number"
                            placeholder="Final settlement amount (₹)"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                          />
                          <Input
                            placeholder="Exit interview notes"
                            value={notes}
                            onChange={(e) => setNotes(e.target.value)}
                          />
                          <div className="flex gap-2 justify-end">
                            <Button
                              variant="ghost"
                              onClick={() => setTarget(null)}
                            >
                              Cancel
                            </Button>
                            <Button
                              onClick={() => settle.mutate({ id: r.id })}
                              disabled={!amount || settle.isPending}
                            >
                              <FileText className="size-4 mr-1" />
                              Settle
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setTarget(r)}
                        >
                          Record settlement
                        </Button>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
