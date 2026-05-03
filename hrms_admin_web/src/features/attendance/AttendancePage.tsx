import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, Clock, X } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import {
  attendanceApi,
  type AttendanceRecord,
  type RegularizationRequest,
} from "@/lib/api/attendance";
import { fmtIst, fmtIstTime } from "@/lib/datetime";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export default function AttendancePage() {
  const [date, setDate] = useState(todayISO());

  const { data: records = [], isLoading } = useQuery({
    queryKey: ["attendance-team", date],
    queryFn: () => attendanceApi.team(date),
  });

  const present = records.filter((r) => r.status === "present").length;
  const wfh = records.filter((r) => r.status === "wfh").length;
  const halfDay = records.filter((r) => r.status === "half_day").length;

  if (isLoading) return <LoadingScreen label="Loading attendance…" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Phase 3 · Attendance
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          Today's <span className="display-em">attendance</span>
        </h2>
      </div>

      <div className="flex items-end gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="date">Date</Label>
          <Input
            id="date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-44"
          />
        </div>
        <div className="flex gap-2 ml-auto">
          <Stat label="Present" value={present} accent="success" />
          <Stat label="WFH" value={wfh} accent="info" />
          <Stat label="Half day" value={halfDay} accent="warning" />
        </div>
      </div>

      <RegularizationQueue />

      <Card>
        <CardHeader>
          <CardTitle>Records</CardTitle>
          <CardDescription>
            {records.length} entries for {date}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {records.length === 0 ? (
            <p className="text-sm text-brand-brown-light">
              No attendance recorded for this date yet.
            </p>
          ) : (
            <div className="space-y-1">
              {records.map((r) => (
                <AttendanceRow key={r.id} record={r} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function AttendanceRow({ record }: { record: AttendanceRecord }) {
  const status = record.status;
  const color =
    status === "present"
      ? "bg-success/15 text-success"
      : status === "wfh"
        ? "bg-info/15 text-info"
        : status === "half_day"
          ? "bg-warning/15 text-warning"
          : status === "absent"
            ? "bg-error/15 text-error"
            : "bg-brand-brown-50 text-brand-brown-darker";
  return (
    <div className="flex items-center justify-between py-2 border-b border-brand-brown-100/50 last:border-0">
      <div className="flex items-center gap-3">
        <Clock className="h-4 w-4 text-brand-brown-light" />
        <div>
          <div className="font-medium text-sm">Employee #{record.employee_id}</div>
          <div className="text-xs text-brand-brown-light">
            {record.check_in
              ? fmtIstTime(record.check_in)
              : "—"}{" "}
            →{" "}
            {record.check_out
              ? fmtIstTime(record.check_out)
              : "—"}
            {record.check_in_distance_m !== null &&
              ` · ${record.check_in_distance_m}m from office`}
          </div>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-xs text-brand-brown-light">
          {Math.round(record.total_minutes / 60)}h {record.total_minutes % 60}m
        </span>
        <span
          className={`text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded ${color}`}
        >
          {status}
        </span>
      </div>
    </div>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: "success" | "info" | "warning";
}) {
  const map = {
    success: "bg-success/15 text-success",
    info: "bg-info/15 text-info",
    warning: "bg-warning/15 text-warning",
  };
  return (
    <div className={`px-4 py-2 rounded-xl ${map[accent]}`}>
      <div className="text-[10px] font-mono uppercase tracking-[0.2em]">
        {label}
      </div>
      <div className="font-display text-2xl font-bold">{value}</div>
    </div>
  );
}

function RegularizationQueue() {
  const queryClient = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["regularizations-pending"],
    queryFn: attendanceApi.pendingRegularizations,
  });

  const approve = useMutation({
    mutationFn: (id: number) => attendanceApi.approveRegularization(id),
    onSuccess: () => {
      toast.success("Regularization approved");
      queryClient.invalidateQueries({ queryKey: ["regularizations-pending"] });
      queryClient.invalidateQueries({ queryKey: ["attendance-team"] });
    },
  });
  const reject = useMutation({
    mutationFn: (id: number) =>
      attendanceApi.rejectRegularization(id, "Rejected"),
    onSuccess: () => {
      toast.success("Rejected");
      queryClient.invalidateQueries({ queryKey: ["regularizations-pending"] });
    },
  });

  if (isLoading || data.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Regularization queue</CardTitle>
        <CardDescription>
          {data.length} pending correction request{data.length === 1 ? "" : "s"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {data.map((r) => (
          <RegRow
            key={r.id}
            req={r}
            onApprove={() => approve.mutate(r.id)}
            onReject={() => reject.mutate(r.id)}
          />
        ))}
      </CardContent>
    </Card>
  );
}

function RegRow({
  req,
  onApprove,
  onReject,
}: {
  req: RegularizationRequest;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <div className="flex items-start justify-between py-2 border-b border-brand-brown-100/50 last:border-0">
      <div className="min-w-0">
        <div className="font-medium text-sm">
          Employee #{req.employee_id} · {req.date}
        </div>
        <div className="text-xs text-brand-brown-light">
          {req.requested_check_in &&
            fmtIst(req.requested_check_in)}{" "}
          {req.requested_check_out &&
            `→ ${fmtIst(req.requested_check_out)}`}
        </div>
        <p className="text-xs mt-1">{req.reason}</p>
      </div>
      <div className="flex gap-2">
        <Button size="sm" variant="gold" onClick={onApprove}>
          <Check className="h-3.5 w-3.5" /> Approve
        </Button>
        <Button size="sm" variant="outline" onClick={onReject}>
          <X className="h-3.5 w-3.5" /> Reject
        </Button>
      </div>
    </div>
  );
}
