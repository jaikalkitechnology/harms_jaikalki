import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { CheckCircle2, RefreshCcw, XCircle, AlertTriangle } from "lucide-react";

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
import { verificationApi } from "@/lib/api/verification";
import { fmtIst } from "@/lib/datetime";

export default function VerificationAuditPage() {
  const qc = useQueryClient();
  const [comments, setComments] = useState<Record<number, string>>({});

  const { data: list = [], isLoading } = useQuery({
    queryKey: ["verification-audit-queue"],
    queryFn: verificationApi.auditQueue,
  });

  const decide = useMutation({
    mutationFn: ({
      id,
      action,
    }: {
      id: number;
      action: "approved" | "rejected" | "rework";
    }) => verificationApi.audit(id, action, comments[id]),
    onSuccess: () => {
      toast.success("Decision recorded");
      qc.invalidateQueries({ queryKey: ["verification-audit-queue"] });
      qc.invalidateQueries({ queryKey: ["verifications"] });
    },
    onError: () => toast.error("Could not save decision"),
  });

  if (isLoading) return <LoadingScreen label="Loading audit queue…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Verification Audit Queue
        </h1>
        <p className="text-sm text-brand-brown-light">
          {list.length} submission{list.length === 1 ? "" : "s"} awaiting QA review.
        </p>
      </div>

      {list.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-brand-brown-light">
            Nothing to audit. Newly submitted verifications appear here.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {list.map((v) => (
            <Card key={v.id}>
              <CardHeader className="flex flex-row items-start justify-between gap-4">
                <div>
                  <CardTitle className="font-mono text-base">
                    {v.ticket_number}
                  </CardTitle>
                  <CardDescription>
                    {v.subject_name} · {v.type}
                  </CardDescription>
                </div>
                {v.fraud_flags.length > 0 && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-error/15 px-3 py-1 text-xs text-error">
                    <AlertTriangle className="size-3" />
                    {v.fraud_flags.length} fraud flag
                    {v.fraud_flags.length === 1 ? "" : "s"}
                  </span>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-brand-brown-light">Address: </span>
                    {v.address ?? "—"}
                  </div>
                  <div>
                    <span className="text-brand-brown-light">Phone: </span>
                    {v.contact_phone ?? "—"}
                  </div>
                  <div>
                    <span className="text-brand-brown-light">Result: </span>
                    <span className="capitalize">
                      {v.result?.replace("_", " ") ?? "—"}
                    </span>
                  </div>
                  <div>
                    <span className="text-brand-brown-light">Submitted: </span>
                    {v.submitted_at
                      ? fmtIst(v.submitted_at)
                      : "—"}
                  </div>
                </div>

                {v.form_data && (
                  <div className="rounded-md border border-brand-brown-50 bg-cream p-3 text-sm">
                    <div className="text-xs font-semibold uppercase text-brand-gold-dark mb-2">
                      Findings
                    </div>
                    <dl className="grid grid-cols-2 gap-2">
                      {Object.entries(v.form_data).map(([k, val]) => (
                        <div key={k}>
                          <dt className="text-xs text-brand-brown-light">
                            {k}
                          </dt>
                          <dd>{String(val)}</dd>
                        </div>
                      ))}
                    </dl>
                  </div>
                )}

                {v.remarks && (
                  <div className="text-sm">
                    <span className="text-brand-brown-light">Remarks: </span>
                    {v.remarks}
                  </div>
                )}

                {v.fraud_flags.length > 0 && (
                  <div className="rounded-md border border-error/30 bg-error/5 p-3 text-xs space-y-1">
                    {v.fraud_flags.map((f) => (
                      <div key={f.id}>
                        <span className="font-semibold">{f.flag_type}</span> ·{" "}
                        {f.severity} · {f.detected_by}
                        {f.notes && ` — ${f.notes}`}
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center">
                  <Input
                    placeholder="Audit comments…"
                    value={comments[v.id] ?? ""}
                    onChange={(e) =>
                      setComments({ ...comments, [v.id]: e.target.value })
                    }
                    className="flex-1"
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1"
                      disabled={decide.isPending}
                      onClick={() =>
                        decide.mutate({ id: v.id, action: "rework" })
                      }
                    >
                      <RefreshCcw className="size-4" />
                      Rework
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      className="gap-1"
                      disabled={decide.isPending}
                      onClick={() =>
                        decide.mutate({ id: v.id, action: "rejected" })
                      }
                    >
                      <XCircle className="size-4" />
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      className="gap-1"
                      disabled={decide.isPending}
                      onClick={() =>
                        decide.mutate({ id: v.id, action: "approved" })
                      }
                    >
                      <CheckCircle2 className="size-4" />
                      Approve
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
