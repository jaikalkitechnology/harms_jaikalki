import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Clock,
  FileText,
  Pencil,
  Plus,
  Search,
  X,
} from "lucide-react";

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
import { verificationApi, type Verification } from "@/lib/api/verification";
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

const PAGE_SIZE = 12;

export default function VerificationQueuePage() {
  const qc = useQueryClient();

  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [search, setSearch] = useState("");
  const [fraudOnly, setFraudOnly] = useState(false);
  const [page, setPage] = useState(1);

  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<Verification | null>(null);

  const [templateId, setTemplateId] = useState<number | "">("");
  const [subjectName, setSubjectName] = useState("");
  const [address, setAddress] = useState("");
  const [phone, setPhone] = useState("");
  const [requestedByOrg, setRequestedByOrg] = useState("");
  const [assignedTo, setAssignedTo] = useState<number | "">("");

  const { data: list = [], isLoading } = useQuery({
    queryKey: [
      "verifications",
      statusFilter,
      typeFilter,
      search,
      fraudOnly,
    ],
    queryFn: () =>
      verificationApi.list({
        status: statusFilter || undefined,
        type: typeFilter || undefined,
        search: search || undefined,
        fraud_only: fraudOnly || undefined,
      }),
  });
  const { data: templates = [] } = useQuery({
    queryKey: ["verification-templates"],
    queryFn: () => verificationApi.templates(),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });
  const { data: tat } = useQuery({
    queryKey: ["verification-tat"],
    queryFn: verificationApi.tatStats,
  });

  const empById = useMemo(
    () => new Map(employees.map((e) => [e.id, e])),
    [employees],
  );

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
      resetForm();
      qc.invalidateQueries({ queryKey: ["verifications"] });
    },
    onError: () => toast.error("Could not create verification"),
  });

  const update = useMutation({
    mutationFn: () =>
      verificationApi.update(editing!.id, {
        subject_name: subjectName,
        address: address || null,
        contact_phone: phone || null,
        requested_by_org: requestedByOrg || null,
        assigned_to: assignedTo ? Number(assignedTo) : null,
      }),
    onSuccess: () => {
      toast.success("Verification updated");
      resetForm();
      qc.invalidateQueries({ queryKey: ["verifications"] });
    },
    onError: () => toast.error("Could not update"),
  });

  const resetForm = () => {
    setShowForm(false);
    setEditing(null);
    setTemplateId("");
    setSubjectName("");
    setAddress("");
    setPhone("");
    setRequestedByOrg("");
    setAssignedTo("");
  };

  const openEdit = (v: Verification) => {
    setEditing(v);
    setSubjectName(v.subject_name);
    setAddress(v.address ?? "");
    setPhone(v.contact_phone ?? "");
    setRequestedByOrg(v.requested_by_org ?? "");
    setAssignedTo(v.assigned_to ?? "");
    setTemplateId(v.template_id);
    setShowForm(true);
  };

  const flagged = useMemo(
    () => list.filter((v) => v.fraud_flags.length > 0).length,
    [list],
  );

  const pageCount = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
  const pageRows = list.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

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
        <Button
          onClick={() => (showForm ? resetForm() : setShowForm(true))}
          className="gap-2"
        >
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
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>
                {editing
                  ? `Edit ${editing.ticket_number}`
                  : "Create verification job"}
              </CardTitle>
              <CardDescription>
                {editing
                  ? "Adjust subject details, address, owner."
                  : "The deadline is auto-set from the template SLA."}
              </CardDescription>
            </div>
            <Button variant="ghost" size="sm" onClick={resetForm}>
              <X className="size-4" />
            </Button>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Template *</Label>
              <select
                value={templateId}
                disabled={!!editing}
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
                disabled={
                  !subjectName ||
                  (!editing && !templateId) ||
                  create.isPending ||
                  update.isPending
                }
                onClick={() =>
                  editing ? update.mutate() : create.mutate()
                }
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filter bar */}
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-5">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search ticket / subject / phone / address…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="in_progress">In progress</option>
            <option value="audit_pending">Audit pending</option>
            <option value="completed">Completed</option>
            <option value="audit_failed">Audit failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All types</option>
            {[
              "address",
              "employment",
              "document",
              "business",
              "education",
              "criminal",
              "bank",
              "other",
            ].map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={fraudOnly}
              onChange={(e) => {
                setFraudOnly(e.target.checked);
                setPage(1);
              }}
            />
            Fraud-flagged only
          </label>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Ticket</th>
                <th className="px-4 py-3">Subject</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Owner</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Deadline</th>
                <th className="px-4 py-3">Result</th>
                <th className="px-4 py-3">Flags</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={9}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No verifications match these filters.
                  </td>
                </tr>
              ) : (
                pageRows.map((v) => {
                  const breached =
                    v.deadline_at &&
                    new Date(v.deadline_at) < new Date() &&
                    v.status !== "completed";
                  const owner = v.assigned_to ? empById.get(v.assigned_to) : null;
                  return (
                    <tr key={v.id} className="border-t border-brand-brown-50">
                      <td className="px-4 py-3 font-mono text-xs">
                        {v.ticket_number}
                      </td>
                      <td className="px-4 py-3">
                        {v.subject_name}
                        {v.contact_phone && (
                          <div className="text-xs text-brand-brown-light">
                            {v.contact_phone}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 capitalize">{v.type}</td>
                      <td className="px-4 py-3 text-xs text-brand-brown-light">
                        {owner
                          ? `${owner.first_name} ${owner.last_name}`
                          : "—"}
                      </td>
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
                        {v.deadline_at ? fmtIst(v.deadline_at) : "—"}
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
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="sm"
                          title="Edit"
                          onClick={() => openEdit(v)}
                        >
                          <Pencil className="size-4" />
                        </Button>
                        {v.status === "completed" && (
                          <a
                            href={verificationApi.reportUrl(v.id)}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-brand-gold-dark hover:underline text-xs ml-1"
                          >
                            <FileText className="size-3" /> PDF
                          </a>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {pageCount > 1 && (
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <div className="text-sm text-brand-brown-light">
            Page {page} of {pageCount}
          </div>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= pageCount}
            onClick={() => setPage(page + 1)}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}
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
