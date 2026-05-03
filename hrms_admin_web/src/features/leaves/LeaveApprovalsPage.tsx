import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, X } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { leavesApi, type LeaveRequest } from "@/lib/api/leaves";
import { fmtIstDate } from "@/lib/datetime";

export default function LeaveApprovalsPage() {
  const queryClient = useQueryClient();

  const { data: pending = [], isLoading } = useQuery({
    queryKey: ["leaves-pending"],
    queryFn: leavesApi.pending,
  });

  const approve = useMutation({
    mutationFn: (id: number) => leavesApi.approve(id, "Approved"),
    onSuccess: () => {
      toast.success("Leave approved");
      queryClient.invalidateQueries({ queryKey: ["leaves-pending"] });
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed";
      toast.error(detail);
    },
  });
  const reject = useMutation({
    mutationFn: (id: number) => leavesApi.reject(id, "Rejected"),
    onSuccess: () => {
      toast.success("Leave rejected");
      queryClient.invalidateQueries({ queryKey: ["leaves-pending"] });
    },
  });

  if (isLoading) return <LoadingScreen label="Loading approvals…" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Phase 3 · Leave Approvals
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          Pending <span className="display-em">approvals</span>
        </h2>
      </div>

      {pending.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-brand-brown-light">
            All caught up.
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {pending.map((req) => (
            <LeaveCard
              key={req.id}
              request={req}
              onApprove={() => approve.mutate(req.id)}
              onReject={() => reject.mutate(req.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function LeaveCard({
  request,
  onApprove,
  onReject,
}: {
  request: LeaveRequest;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle>
              {request.leave_type?.code ?? "—"} · {request.days} day
              {Number(request.days) > 1 ? "s" : ""}
            </CardTitle>
            <CardDescription>
              Employee #{request.employee_id} ·{" "}
              {fmtIstDate(request.applied_at)}
            </CardDescription>
          </div>
          {request.half_day && (
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded bg-info/15 text-info">
              Half day
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm">
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
            Dates
          </div>
          <div>
            {request.from_date} → {request.to_date}
          </div>
        </div>
        {request.reason && (
          <div className="text-sm">
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
              Reason
            </div>
            <p>{request.reason}</p>
          </div>
        )}
        <div className="flex gap-2 pt-2">
          <Button onClick={onApprove} variant="gold" size="sm" className="flex-1">
            <Check className="h-4 w-4" /> Approve
          </Button>
          <Button onClick={onReject} variant="outline" size="sm" className="flex-1">
            <X className="h-4 w-4" /> Reject
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
