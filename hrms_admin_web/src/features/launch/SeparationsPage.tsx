import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { DoorOpen, FileText, Mail, Plus, Printer, Upload, X } from "lucide-react";

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
import { launchApi, type Resignation } from "@/lib/api/launch";
import { employeesApi } from "@/lib/api/employees";
import { SeparationActions } from "./SeparationActions";

const TYPE_LABEL: Record<string, string> = {
  resignation: "Resignation",
  termination: "Termination",
};

const STATUS_TONE: Record<string, string> = {
  in_notice: "text-brand-gold-dark",
  cleared: "text-success",
  settled: "text-success",
  rejected: "text-error",
  cancelled: "text-brand-brown-light",
};

export default function SeparationsPage() {
  const qc = useQueryClient();
  const [showNew, setShowNew] = useState(false);
  const [emailingId, setEmailingId] = useState<number | null>(null);

  const { data: rows = [], isLoading } = useQuery({
    queryKey: ["separations"],
    queryFn: () => launchApi.listResignations(),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });
  const empById = useMemo(
    () => new Map(employees.map((e) => [e.id, e])),
    [employees],
  );

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <DoorOpen className="h-5 w-5" /> Resign / Terminate
            </CardTitle>
            <CardDescription>
              HR-initiated separation with auto-approval. Generates the
              formal letter on the Jaikalki letterhead, emails it to the
              employee, and clamps the employee&apos;s exit_date so
              attendance and payroll respect the last working day.
            </CardDescription>
          </div>
          <Button onClick={() => setShowNew(true)} className="shrink-0">
            <Plus className="h-4 w-4 mr-1" /> Initiate separation
          </Button>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm min-w-[880px]">
            <thead className="text-left text-brand-brown-light bg-brand-brown-50/40">
              <tr>
                <th className="py-2 px-4">Employee</th>
                <th>Type</th>
                <th>Last working day</th>
                <th>Status</th>
                <th>Requested</th>
                <th className="text-right pr-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(rows as Resignation[]).map((r) => {
                const emp = empById.get(r.employee_id);
                const kind = r.separation_type ?? "resignation";
                return (
                  <tr
                    key={r.id}
                    className="border-t border-brand-brown-50"
                  >
                    <td className="py-2 px-4">
                      {emp ? (
                        <>
                          <span className="font-semibold text-brand-brown-darker">
                            {emp.first_name} {emp.last_name}
                          </span>
                          <span className="ml-1 font-mono text-xs text-brand-brown-light">
                            · {emp.employee_code}
                          </span>
                        </>
                      ) : (
                        <span className="font-mono">#{r.employee_id}</span>
                      )}
                    </td>
                    <td>
                      <span
                        className={
                          "text-xs font-mono uppercase tracking-[0.15em] " +
                          (kind === "termination"
                            ? "text-error"
                            : "text-brand-gold-dark")
                        }
                      >
                        {TYPE_LABEL[kind] ?? kind}
                      </span>
                    </td>
                    <td className="text-xs">
                      {r.actual_last_working_day ??
                        r.proposed_last_working_day}
                    </td>
                    <td>
                      <span
                        className={
                          "text-xs font-mono uppercase tracking-[0.15em] " +
                          (STATUS_TONE[r.status] ?? "text-brand-brown-light")
                        }
                      >
                        {r.status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="text-xs text-brand-brown-light">
                      {new Date(r.requested_at).toLocaleDateString("en-IN")}
                    </td>
                    <td className="text-right pr-4 whitespace-nowrap">
                      <a
                        href={launchApi.separationPdfUrl(r.id)}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-[0.15em] text-brand-gold-dark hover:text-brand-brown-darker mr-3"
                      >
                        <Printer className="h-3 w-3" /> PDF
                      </a>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setEmailingId(r.id)}
                      >
                        <Mail className="h-3 w-3 mr-1" /> Email
                      </Button>{" "}
                      <SeparationActions
                        resignation={r}
                        employeeLabel={
                          emp
                            ? `${emp.first_name} ${emp.last_name}`
                            : `Employee #${r.employee_id}`
                        }
                      />
                    </td>
                  </tr>
                );
              })}
              {rows.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="text-center py-6 text-brand-brown-light"
                  >
                    No separations yet. Click <em>Initiate separation</em> to
                    create the first one.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {showNew && (
        <NewSeparationModal
          employees={employees.map((e) => ({
            id: e.id,
            label: `${e.first_name} ${e.last_name} · ${e.employee_code}`,
          }))}
          onClose={() => setShowNew(false)}
          onSaved={() => {
            qc.invalidateQueries({ queryKey: ["separations"] });
            setShowNew(false);
          }}
        />
      )}
      {emailingId != null && (
        <EmailSeparationModal
          resignationId={emailingId}
          onClose={() => setEmailingId(null)}
        />
      )}
    </div>
  );
}

function NewSeparationModal({
  employees,
  onClose,
  onSaved,
}: {
  employees: { id: number; label: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [kind, setKind] = useState<"resignation" | "termination">(
    "resignation",
  );
  const [lwd, setLwd] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() + 30);
    return d.toISOString().slice(0, 10);
  });
  const [reason, setReason] = useState("");
  const [notice, setNotice] = useState(30);
  const [managerComment, setManagerComment] = useState("");

  const save = useMutation({
    mutationFn: () =>
      launchApi.adminCreateSeparation({
        employee_id: Number(employeeId),
        separation_type: kind,
        proposed_last_working_day: lwd,
        reason: reason || undefined,
        notice_period_days: notice,
        manager_comment: managerComment || undefined,
      }),
    onSuccess: () => {
      toast.success(
        kind === "termination"
          ? "Termination recorded and letter ready"
          : "Resignation accepted and letter ready",
      );
      onSaved();
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not save";
      toast.error(detail);
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Initiate separation</CardTitle>
            <CardDescription>
              Auto-approves and locks the employee&apos;s exit_date. HR can
              undo from the employee&apos;s detail page.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Employee</Label>
            <select
              value={employeeId}
              onChange={(e) =>
                setEmployeeId(e.target.value ? Number(e.target.value) : "")
              }
              className="w-full bg-transparent border border-brand-brown-50 rounded-md px-3 py-2 text-sm"
            >
              <option value="">Select an employee…</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Type</Label>
            <div className="flex gap-3 mt-1">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  checked={kind === "resignation"}
                  onChange={() => setKind("resignation")}
                />
                Resignation
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  checked={kind === "termination"}
                  onChange={() => setKind("termination")}
                />
                Termination
              </label>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Last working day</Label>
              <Input
                type="date"
                value={lwd}
                onChange={(e) => setLwd(e.target.value)}
              />
            </div>
            <div>
              <Label>Notice period (days)</Label>
              <Input
                type="number"
                min={0}
                max={180}
                value={notice}
                onChange={(e) =>
                  setNotice(Number(e.target.value) || 0)
                }
              />
            </div>
          </div>
          <div>
            <Label>Reason (optional)</Label>
            <Input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={
                kind === "termination"
                  ? "e.g. Non-performance during probation"
                  : "e.g. Personal reasons"
              }
            />
          </div>
          <div>
            <Label>Internal comment (optional)</Label>
            <textarea
              rows={3}
              value={managerComment}
              onChange={(e) => setManagerComment(e.target.value)}
              className="w-full bg-transparent border border-brand-brown-50 rounded-md p-2 text-sm"
              placeholder="Not shown on the letter — stored for audit."
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={() => save.mutate()}
              disabled={
                save.isPending || !employeeId || !lwd || !kind
              }
            >
              <FileText className="h-4 w-4 mr-1" />
              {save.isPending ? "Saving…" : "Submit & auto-approve"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function EmailSeparationModal({
  resignationId,
  onClose,
}: {
  resignationId: number;
  onClose: () => void;
}) {
  const [to, setTo] = useState("");
  const [cc, setCc] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [uploading, setUploading] = useState<File | null>(null);

  const send = useMutation({
    mutationFn: () =>
      launchApi.emailSeparationLetter(resignationId, {
        to: to || undefined,
        cc: cc
          ? cc.split(",").map((s) => s.trim()).filter(Boolean)
          : undefined,
        subject: subject || undefined,
        body: body || undefined,
      }),
    onSuccess: (data) => {
      toast.success(`Letter emailed to ${data.to}`);
      onClose();
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not send email";
      toast.error(detail);
    },
  });

  const upload = useMutation({
    mutationFn: async () => {
      if (!uploading) return;
      await launchApi.uploadResignationDocument(
        resignationId,
        uploading,
        "other",
      );
    },
    onSuccess: () => {
      toast.success("Document attached");
      setUploading(null);
    },
    onError: () => toast.error("Could not upload document"),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Email the letter</CardTitle>
            <CardDescription>
              Sends the generated PDF as an attachment. Attach any
              supporting documents to the record first.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <Label>To</Label>
            <Input
              type="email"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              placeholder="Leave blank to use the employee's personal email"
            />
          </div>
          <div>
            <Label>Cc (comma-separated)</Label>
            <Input
              value={cc}
              onChange={(e) => setCc(e.target.value)}
              placeholder="hr@jaikalki.com, manager@…"
            />
          </div>
          <div>
            <Label>Subject (optional)</Label>
            <Input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Leave blank to use the default"
            />
          </div>
          <div>
            <Label>Body (optional HTML)</Label>
            <textarea
              rows={4}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="w-full bg-transparent border border-brand-brown-50 rounded-md p-2 text-sm"
              placeholder="Leave blank for the default cover note."
            />
          </div>
          <div className="border border-dashed border-brand-brown-50 rounded-md p-3">
            <Label className="flex items-center gap-1 text-xs">
              <Upload className="h-3 w-3" /> Attach a supporting doc
            </Label>
            <div className="flex items-center gap-2 mt-1">
              <input
                type="file"
                onChange={(e) =>
                  setUploading(e.target.files?.[0] ?? null)
                }
                className="text-xs"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={() => upload.mutate()}
                disabled={!uploading || upload.isPending}
              >
                {upload.isPending ? "Uploading…" : "Upload"}
              </Button>
            </div>
            <p className="text-[11px] text-brand-brown-light mt-1">
              Uploaded documents appear on the resignation record. The
              email always includes the generated letter PDF.
            </p>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={() => send.mutate()}
              disabled={send.isPending}
            >
              <Mail className="h-4 w-4 mr-1" />
              {send.isPending ? "Sending…" : "Send"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
