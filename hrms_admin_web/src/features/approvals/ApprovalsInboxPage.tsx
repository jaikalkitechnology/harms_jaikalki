import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, Inbox, X } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import {
  approvalsApi,
  REQUEST_TYPE_LABEL,
  type Approval,
} from "@/lib/api/approvals";

export default function ApprovalsInboxPage() {
  const [filter, setFilter] = useState<string | undefined>();
  const queryClient = useQueryClient();

  const { data: approvals = [], isLoading } = useQuery({
    queryKey: ["approvals-inbox", filter],
    queryFn: () => approvalsApi.inbox(filter),
  });

  const { data: counts = [] } = useQuery({
    queryKey: ["approvals-counts"],
    queryFn: approvalsApi.counts,
  });

  const total = counts.reduce((acc, c) => acc + c.count, 0);

  const approve = useMutation({
    mutationFn: (id: number) => approvalsApi.approve(id, "Approved"),
    onSuccess: () => {
      toast.success("Approved");
      queryClient.invalidateQueries({ queryKey: ["approvals-inbox"] });
      queryClient.invalidateQueries({ queryKey: ["approvals-counts"] });
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed";
      toast.error(detail);
    },
  });

  const reject = useMutation({
    mutationFn: (id: number) => approvalsApi.reject(id, "Rejected"),
    onSuccess: () => {
      toast.success("Rejected");
      queryClient.invalidateQueries({ queryKey: ["approvals-inbox"] });
      queryClient.invalidateQueries({ queryKey: ["approvals-counts"] });
    },
  });

  if (isLoading) return <LoadingScreen label="Loading inbox…" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Phase 4 · Universal Approvals
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          Approval <span className="display-em">inbox</span>
        </h2>
        <p className="mt-1 text-sm text-brand-brown-light">
          {total} pending across {counts.length} type{counts.length === 1 ? "" : "s"}
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        <FilterPill
          label={`All · ${total}`}
          active={filter === undefined}
          onClick={() => setFilter(undefined)}
        />
        {counts.map((c) => (
          <FilterPill
            key={c.request_type}
            label={`${REQUEST_TYPE_LABEL[c.request_type] ?? c.request_type} · ${c.count}`}
            active={filter === c.request_type}
            onClick={() => setFilter(c.request_type)}
          />
        ))}
      </div>

      {approvals.length === 0 ? (
        <Card>
          <CardContent className="py-12 flex flex-col items-center gap-3 text-brand-brown-light">
            <Inbox className="h-10 w-10" />
            <div>All caught up — nothing pending.</div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {approvals.map((a) => (
            <ApprovalCard
              key={a.id}
              approval={a}
              onApprove={() => approve.mutate(a.id)}
              onReject={() => reject.mutate(a.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function FilterPill({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`text-[10px] font-mono uppercase tracking-[0.2em] px-3 py-1.5 rounded-full border transition-colors ${
        active
          ? "bg-brand-gold/15 border-brand-gold/40 text-brand-brown-darker"
          : "bg-card border-brand-brown-100 text-brand-brown-light hover:border-brand-gold/40"
      }`}
    >
      {label}
    </button>
  );
}

function ApprovalCard({
  approval,
  onApprove,
  onReject,
}: {
  approval: Approval;
  onApprove: () => void;
  onReject: () => void;
}) {
  const typeLabel =
    REQUEST_TYPE_LABEL[approval.request_type] ?? approval.request_type;
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <CardTitle className="text-base truncate">{approval.title}</CardTitle>
            <CardDescription>
              {typeLabel} · level {approval.current_level} of {approval.max_levels}
            </CardDescription>
          </div>
          <span className="shrink-0 text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded bg-warning/15 text-warning">
            Pending
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {approval.summary && (
          <p className="text-sm text-brand-brown-darker">{approval.summary}</p>
        )}
        <RequestData type={approval.request_type} data={approval.request_data} />
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

function RequestData({
  type,
  data,
}: {
  type: string;
  data: Record<string, unknown>;
}) {
  const rows: [string, string][] = [];
  if (type === "leave_request") {
    rows.push(["Type", String(data.leave_type_code ?? "—")]);
    rows.push(["Dates", `${data.from_date} → ${data.to_date}`]);
    rows.push(["Days", `${data.days}${data.half_day ? " (half day)" : ""}`]);
    if (data.employee_code)
      rows.push(["Employee", String(data.employee_code)]);
  } else if (type === "attendance_regularization") {
    rows.push(["Date", String(data.date ?? "—")]);
    if (data.requested_check_in)
      rows.push(["Check-in", String(data.requested_check_in)]);
    if (data.requested_check_out)
      rows.push(["Check-out", String(data.requested_check_out)]);
  } else if (type === "intern_expense") {
    rows.push(["Amount", `₹${data.amount}`]);
    rows.push(["Date", String(data.expense_date ?? "—")]);
    rows.push(["Type", String(data.expense_type ?? "—")]);
  }

  return (
    <dl className="grid grid-cols-2 gap-2 text-xs">
      {rows.map(([k, v]) => (
        <div key={k}>
          <dt className="font-mono uppercase tracking-[0.2em] text-brand-brown-light text-[10px]">
            {k}
          </dt>
          <dd className="text-sm">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
