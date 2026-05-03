import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { AlertTriangle, Eye, Lock, ShieldCheck } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import {
  COMPLAINT_TYPE_LABEL,
  justiceApi,
  type ComplaintListItem,
} from "@/lib/api/justice";
import { fmtIstDate } from "@/lib/datetime";

const SEVERITY_COLOR: Record<string, string> = {
  low: "bg-brand-brown-50 text-brand-brown-darker",
  medium: "bg-info/15 text-info",
  high: "bg-warning/15 text-warning",
  critical: "bg-error/15 text-error",
};

const STATUS_COLOR: Record<string, string> = {
  submitted: "bg-warning/15 text-warning",
  acknowledged: "bg-info/15 text-info",
  under_investigation: "bg-info/15 text-info",
  action_taken: "bg-brand-gold/15 text-brand-gold-dark",
  resolved: "bg-success/15 text-success",
  withdrawn: "bg-brand-brown-50 text-brand-brown-darker",
  rejected: "bg-error/15 text-error",
};

export default function JusticeInboxPage() {
  const [filter, setFilter] = useState<string | null>(null);

  const { data: complaints = [], isLoading } = useQuery({
    queryKey: ["justice-inbox"],
    queryFn: justiceApi.inbox,
  });
  const { data: compliance } = useQuery({
    queryKey: ["justice-icc-compliance"],
    queryFn: justiceApi.iccCompliance,
  });

  const filtered = filter
    ? complaints.filter((c) => c.complaint_type === filter)
    : complaints;

  const types = Array.from(new Set(complaints.map((c) => c.complaint_type)));

  if (isLoading) return <LoadingScreen label="Loading complaints…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Phase 8 · Justice Portal
          </div>
          <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
            Authority <span className="display-em">inbox</span>
          </h2>
          <p className="mt-1 text-sm text-brand-brown-light">
            {complaints.length} complaints visible to you. All access is logged.
          </p>
        </div>
        {compliance && <PoshComplianceBadge status={compliance} />}
      </div>

      <div className="flex flex-wrap gap-2">
        <FilterPill
          label={`All · ${complaints.length}`}
          active={filter === null}
          onClick={() => setFilter(null)}
        />
        {types.map((t) => {
          const n = complaints.filter((c) => c.complaint_type === t).length;
          return (
            <FilterPill
              key={t}
              label={`${COMPLAINT_TYPE_LABEL[t] ?? t} · ${n}`}
              active={filter === t}
              onClick={() => setFilter(t)}
            />
          );
        })}
      </div>

      {filtered.length === 0 ? (
        <Card>
          <CardContent className="py-12 flex flex-col items-center gap-3 text-brand-brown-light">
            <ShieldCheck className="h-10 w-10" />
            <div>No complaints to action right now.</div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {filtered.map((c) => (
            <ComplaintCard key={c.id} complaint={c} />
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

function ComplaintCard({ complaint }: { complaint: ComplaintListItem }) {
  const sev = SEVERITY_COLOR[complaint.severity] ?? "";
  const status = STATUS_COLOR[complaint.status] ?? "";
  const isPosh =
    complaint.complaint_type === "sexual_harassment" ||
    complaint.complaint_type === "discrimination";
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
              <span>{complaint.ticket_number}</span>
              {complaint.is_anonymous && (
                <span className="inline-flex items-center gap-1">
                  <Lock className="h-3 w-3" /> Anonymous
                </span>
              )}
              {isPosh && (
                <span className="inline-flex items-center gap-1 text-error">
                  <AlertTriangle className="h-3 w-3" /> POSH
                </span>
              )}
            </div>
            <CardTitle className="text-base mt-1 truncate">
              {complaint.subject}
            </CardTitle>
            <CardDescription>
              {COMPLAINT_TYPE_LABEL[complaint.complaint_type] ?? complaint.complaint_type}
            </CardDescription>
          </div>
          <div className="flex flex-col gap-1 items-end shrink-0">
            <span
              className={`text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded ${sev}`}
            >
              {complaint.severity}
            </span>
            <span
              className={`text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded ${status}`}
            >
              {complaint.status.replace(/_/g, " ")}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="text-xs text-brand-brown-light">
          Submitted {fmtIstDate(complaint.submitted_at)}
          {complaint.deadline_at && (
            <>
              {" · "}deadline{" "}
              {fmtIstDate(complaint.deadline_at)}
            </>
          )}
        </div>
        <Link
          to={`/justice/${complaint.id}`}
          className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.2em] text-brand-gold-dark hover:text-brand-brown-darker"
        >
          <Eye className="h-3 w-3" />
          Open · access logged
        </Link>
      </CardContent>
    </Card>
  );
}

function PoshComplianceBadge({
  status,
}: {
  status: import("@/lib/api/justice").IccComplianceStatus;
}) {
  return (
    <Card className="max-w-sm">
      <CardContent className="pt-5">
        <div className="flex items-start gap-3">
          {status.compliant ? (
            <ShieldCheck className="h-6 w-6 text-success shrink-0 mt-1" />
          ) : (
            <AlertTriangle className="h-6 w-6 text-warning shrink-0 mt-1" />
          )}
          <div className="min-w-0">
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
              POSH ICC
            </div>
            <div className="text-sm font-medium">
              {status.compliant ? "Compliant" : "Action required"}
            </div>
            <div className="text-xs text-brand-brown-light">
              {status.member_count} members · {status.women_count} women ·{" "}
              {status.external_count} external
            </div>
            {!status.compliant && (
              <ul className="mt-2 text-xs text-warning list-disc pl-4">
                {status.reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
