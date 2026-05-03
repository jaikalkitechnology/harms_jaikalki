import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Clock, AlertTriangle, FileText } from "lucide-react";

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
import { verificationApi } from "@/lib/api/verification";
import { employeesApi } from "@/lib/api/employees";
import { fmtIst } from "@/lib/datetime";

const STATUS_COLOR: Record<string, string> = {
  pending: "bg-info/15 text-info",
  in_progress: "bg-brand-gold/15 text-brand-gold-dark",
  submitted: "bg-warning/15 text-warning",
  audit_pending: "bg-warning/25 text-warning",
  audit_passed: "bg-success/15 text-success",
  audit_failed: "bg-error/15 text-error",
  completed: "bg-success/25 text-success",
  cancelled: "bg-brand-brown-50 text-brand-brown-darker",
};

export default function VerificationQueuePage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [templateId, setTemplateId] = useState<number | "">("");
  const [subjectName, setSubjectName] = useState("");
  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [requestedByOrg, setRequestedByOrg] = useState("");
  const [assignedTo, setAssignedTo] = useState<number | "">("");

  const { data: list = [], isLoading } = useQuery({
    queryKey: ["verifications", statusFilter],
    queryFn: () =>
      verificationApi.list(
        statusFilter ? { status: statusFilter } : undefined,
      ),
  });
  const { data: templates = [] } = useQuery({
    queryKey: ["verification-templates"],
    queryFn: verificationApi.templates,
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });
  const { data: tat } = useQuery({
    queryKey: ["verification-tat"],
    queryFn: verificationApi.tatStats,
  });

  const create = useMutation({
    mutationFn: () =>
      verificationApi.create({
        template_id: Number(templateId),
        subject_name: subjectName,
        subject_data: {},
        address: address || null,
        contact_phone: phone || null,
        requested_by_org: requestedByOrg || null,
        assigned_to: assignedTo ? Number(assignedTo) : null,
      }),
    onSuccess: () => {
      toast.success("Verification created");
      setShowForm(false);
      setSubjectName("");
      setAddress("");
      setPhone("");
      setRequestedByOrg("");
      qc.invalidateQueries({ queryKey: ["verifications"] });
    },
    onError: () => toast.error("Could not create verification"),
  });

  const flagged = useMemo(
    () => list.filter((v) => v.fraud_flags.length > 0).length,
    [list],
  );

  if (isLoading) return <LoadingScreen label="Loading verifications…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Verifications
          </h1>
          <p className="text-sm text-brand-brown-light">
            Background verification job queue · {list.length} total ·{" "}
            {flagged} fraud-flagged
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
          <Plus className="size-4" />
          {showForm ? "Cancel" : "New job"}
        </Button>
      </div>

      {/* TAT card */}
      {tat && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-brand-brown-light flex items-center gap-2">
              <Clock className="size-4" /> TAT / SLA
            </CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 sm:grid-cols-5 gap-4">
            <Stat label="Completed" value={tat.total} />
            <Stat label="On time" value={tat.on_time} color="text-success" />
            <Stat label="Breached" value={tat.breached} color="text-error" />
            <Stat label="Avg hours" value={tat.avg_hours} />
            <Stat
              label="Breach %"
              value={`${tat.breach_pct}%`}
              color={tat.breach_pct > 10 ? "text-error" : "text-success"}
            />
          </CardContent>
        </Card>
      )}

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create verification job</CardTitle>
            <CardDescription>
              The deadline is auto-set from the template SLA.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Template *</Label>
              <select
                value={templateId}
                onChange={(e) =>
                  setTemplateId(e.target.value ? Number(e.target.value) : "")
                }
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">— Select —</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.code} — {t.name} ({t.sla_hours}h)
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Assign to</Label>
              <select
                value={assignedTo}
                onChange={(e) =>
                  setAssignedTo(e.target.value ? Number(e.target.value) : "")
                }
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">— Unassigned —</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.employee_code} — {emp.first_name} {emp.last_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Subject name *</Label>
              <Input
                value={subjectName}
                onChange={(e) => setSubjectName(e.target.value)}
              />
            </div>
            <div>
              <Label>Subject phone</Label>
              <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
            </div>
            <div className="md:col-span-2">
              <Label>Address</Label>
              <Input
                value={address}
                onChange={(e) => setAddress(e.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Label>Requested by</Label>
              <Input
                value={requestedByOrg}
                onChange={(e) => setRequestedByOrg(e.target.value)}
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                disabled={!templateId || !subjectName || create.isPending}
                onClick={() => create.mutate()}
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-2">
        <Label className="text-xs">Status:</Label>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All</option>
          <option value="pending">Pending</option>
          <option value="in_progress">In progress</option>
          <option value="audit_pending">Audit pending</option>
          <option value="completed">Completed</option>
          <option value="audit_failed">Audit failed</option>
        </select>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Ticket</th>
                <th className="px-4 py-3">Subject</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Deadline</th>
                <th className="px-4 py-3">Result</th>
                <th className="px-4 py-3">Flags</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {list.length === 0 ? (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No verifications.
                  </td>
                </tr>
              ) : (
                list.map((v) => {
                  const breached =
                    v.deadline_at &&
                    new Date(v.deadline_at) < new Date() &&
                    v.status !== "completed";
                  return (
                    <tr key={v.id} className="border-t border-brand-brown-50">
                      <td className="px-4 py-3 font-mono text-xs">
                        {v.ticket_number}
                      </td>
                      <td className="px-4 py-3">{v.subject_name}</td>
                      <td className="px-4 py-3 capitalize">{v.type}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-1 text-xs ${STATUS_COLOR[v.status] ?? ""}`}
                        >
                          {v.status.replace("_", " ")}
                        </span>
                      </td>
                      <td
                        className={`px-4 py-3 text-xs ${breached ? "text-error font-semibold" : ""}`}
                      >
                        {v.deadline_at
                          ? fmtIst(v.deadline_at)
                          : "—"}
                      </td>
                      <td className="px-4 py-3">
                        {v.result ? (
                          <span className="capitalize text-xs">
                            {v.result.replace("_", " ")}
                          </span>
                        ) : (
                          <span className="text-brand-brown-light text-xs">
                            —
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {v.fraud_flags.length > 0 ? (
                          <span className="inline-flex items-center gap-1 text-error text-xs">
                            <AlertTriangle className="size-3" />
                            {v.fraud_flags.length}
                          </span>
                        ) : (
                          ""
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {v.status === "completed" ? (
                          <a
                            href={verificationApi.reportUrl(v.id)}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-brand-gold-dark hover:underline text-xs"
                          >
                            <FileText className="size-3" /> Report
                          </a>
                        ) : null}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

function Stat({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <div>
      <div className="text-xs text-brand-brown-light">{label}</div>
      <div className={`text-2xl font-semibold ${color ?? "text-brand-brown-darker"}`}>
        {value}
      </div>
    </div>
  );
}
