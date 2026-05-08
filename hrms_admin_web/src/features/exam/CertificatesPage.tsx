import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Award,
  ChevronLeft,
  ChevronRight,
  Download,
  Eye,
  Pencil,
  Plus,
  RotateCcw,
  Search,
  ShieldOff,
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
import { examApi, type Certificate } from "@/lib/api/exam";
import { employeesApi } from "@/lib/api/employees";

const PAGE_SIZE = 12;

interface IssueDraft {
  employee_id: number | "";
  title: string;
  issued_date: string;
  expiry_date: string;
  score_percentage: string;
}

interface EditDraft {
  title: string;
  issued_date: string;
  expiry_date: string;
  score_percentage: string;
}

const todayStr = new Date().toISOString().slice(0, 10);

const EMPTY_ISSUE: IssueDraft = {
  employee_id: "",
  title: "",
  issued_date: todayStr,
  expiry_date: "",
  score_percentage: "",
};

export default function CertificatesPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [employeeFilter, setEmployeeFilter] = useState<number | "">("");
  const [statusFilter, setStatusFilter] = useState<"" | "active" | "revoked">(
    "",
  );
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [page, setPage] = useState(1);

  const [issueOpen, setIssueOpen] = useState(false);
  const [issueDraft, setIssueDraft] = useState<IssueDraft>(EMPTY_ISSUE);

  const [editing, setEditing] = useState<Certificate | null>(null);
  const [editDraft, setEditDraft] = useState<EditDraft>({
    title: "",
    issued_date: "",
    expiry_date: "",
    score_percentage: "",
  });

  const [previewing, setPreviewing] = useState<Certificate | null>(null);

  const { data: list = [], isLoading } = useQuery({
    queryKey: [
      "certificates",
      search,
      employeeFilter,
      statusFilter,
      fromDate,
      toDate,
    ],
    queryFn: () =>
      examApi.listCertificates({
        search: search || undefined,
        employee_id: employeeFilter === "" ? undefined : employeeFilter,
        is_revoked:
          statusFilter === ""
            ? undefined
            : statusFilter === "revoked",
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
        limit: 500,
      }),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });
  const empById = useMemo(
    () => new Map(employees.map((e) => [e.id, e])),
    [employees],
  );

  const issue = useMutation({
    mutationFn: () =>
      examApi.issueCertificate({
        employee_id: Number(issueDraft.employee_id),
        title: issueDraft.title,
        issued_date: issueDraft.issued_date || undefined,
        expiry_date: issueDraft.expiry_date || null,
        score_percentage: issueDraft.score_percentage
          ? Number(issueDraft.score_percentage)
          : null,
      }),
    onSuccess: () => {
      toast.success("Certificate issued");
      setIssueOpen(false);
      setIssueDraft(EMPTY_ISSUE);
      qc.invalidateQueries({ queryKey: ["certificates"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not issue"),
  });

  const update = useMutation({
    mutationFn: () =>
      examApi.updateCertificate(editing!.id, {
        title: editDraft.title,
        issued_date: editDraft.issued_date || undefined,
        expiry_date: editDraft.expiry_date || null,
        score_percentage: editDraft.score_percentage
          ? Number(editDraft.score_percentage)
          : null,
      }),
    onSuccess: () => {
      toast.success("Certificate updated");
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["certificates"] });
    },
    onError: () => toast.error("Could not update"),
  });

  const revoke = useMutation({
    mutationFn: (args: { id: number; reason: string }) =>
      examApi.revokeCertificate(args.id, args.reason),
    onSuccess: () => {
      toast.success("Certificate revoked");
      qc.invalidateQueries({ queryKey: ["certificates"] });
    },
    onError: () => toast.error("Could not revoke"),
  });

  const restore = useMutation({
    mutationFn: (id: number) => examApi.restoreCertificate(id),
    onSuccess: () => {
      toast.success("Certificate restored");
      qc.invalidateQueries({ queryKey: ["certificates"] });
    },
    onError: () => toast.error("Could not restore"),
  });

  const counts = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    let active = 0;
    let revoked = 0;
    let expired = 0;
    list.forEach((c) => {
      if (c.is_revoked) revoked++;
      else if (c.expiry_date && c.expiry_date < today) expired++;
      else active++;
    });
    return { active, revoked, expired, total: list.length };
  }, [list]);

  const pageCount = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
  const pageRows = list.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const openEdit = (c: Certificate) => {
    setEditing(c);
    setEditDraft({
      title: c.title,
      issued_date: c.issued_date,
      expiry_date: c.expiry_date ?? "",
      score_percentage: c.score_percentage ?? "",
    });
  };

  if (isLoading) return <LoadingScreen label="Loading certificates…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Learning · Certificates
          </div>
          <h1 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            Certificate <span className="display-em">ledger</span>
          </h1>
          <p className="mt-1 text-sm text-brand-brown-light">
            {counts.total} issued · {counts.active} active · {counts.expired}{" "}
            expired · {counts.revoked} revoked
          </p>
        </div>
        <Button onClick={() => setIssueOpen(true)} className="gap-2">
          <Plus className="size-4" /> Issue certificate
        </Button>
      </div>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-5">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search number / title…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9"
            />
          </div>
          <select
            value={employeeFilter}
            onChange={(e) => {
              setEmployeeFilter(e.target.value ? Number(e.target.value) : "");
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All employees</option>
            {employees.map((emp) => (
              <option key={emp.id} value={emp.id}>
                {emp.employee_code} — {emp.first_name} {emp.last_name}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as "" | "active" | "revoked");
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All statuses</option>
            <option value="active">Not revoked</option>
            <option value="revoked">Revoked</option>
          </select>
          <div className="flex gap-2">
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => {
                setFromDate(e.target.value);
                setPage(1);
              }}
            />
            <Input
              type="date"
              value={toDate}
              onChange={(e) => {
                setToDate(e.target.value);
                setPage(1);
              }}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Number</th>
                <th className="px-4 py-3">Holder</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Issued</th>
                <th className="px-4 py-3">Expires</th>
                <th className="px-4 py-3 text-right">Score</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={8}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No certificates match these filters.
                  </td>
                </tr>
              ) : (
                pageRows.map((c) => {
                  const emp = empById.get(c.employee_id);
                  const today = new Date().toISOString().slice(0, 10);
                  const expired =
                    !c.is_revoked && c.expiry_date && c.expiry_date < today;
                  return (
                    <tr key={c.id} className="border-t border-brand-brown-50">
                      <td className="px-4 py-3 font-mono text-xs">
                        {c.certificate_number}
                      </td>
                      <td className="px-4 py-3">
                        {emp
                          ? `${emp.employee_code} · ${emp.first_name} ${emp.last_name}`
                          : `Employee #${c.employee_id}`}
                      </td>
                      <td className="px-4 py-3">{c.title}</td>
                      <td className="px-4 py-3">{c.issued_date}</td>
                      <td className="px-4 py-3">
                        {c.expiry_date ?? (
                          <span className="text-brand-brown-light text-xs">
                            no expiry
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {c.score_percentage ? `${c.score_percentage}%` : "—"}
                      </td>
                      <td className="px-4 py-3">
                        {c.is_revoked ? (
                          <span
                            className="rounded-full bg-error/15 px-2 py-1 text-xs text-error"
                            title={c.revoked_reason ?? undefined}
                          >
                            revoked
                          </span>
                        ) : expired ? (
                          <span className="rounded-full bg-warning/15 px-2 py-1 text-xs text-warning">
                            expired
                          </span>
                        ) : (
                          <span className="rounded-full bg-success/15 px-2 py-1 text-xs text-success">
                            active
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="sm"
                          title="Preview"
                          onClick={() => setPreviewing(c)}
                        >
                          <Eye className="size-4" />
                        </Button>
                        <a
                          href={examApi.certificatePdfUrl(c.id)}
                          target="_blank"
                          rel="noreferrer"
                          title="Download PDF"
                          className="inline-flex items-center justify-center px-2 py-1 hover:bg-brand-brown-50/50 rounded"
                        >
                          <Download className="size-4" />
                        </a>
                        <Button
                          variant="ghost"
                          size="sm"
                          title="Edit"
                          onClick={() => openEdit(c)}
                          disabled={c.is_revoked}
                        >
                          <Pencil className="size-4" />
                        </Button>
                        {c.is_revoked ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Restore"
                            onClick={() => restore.mutate(c.id)}
                          >
                            <RotateCcw className="size-4 text-success" />
                          </Button>
                        ) : (
                          <Button
                            variant="ghost"
                            size="sm"
                            title="Revoke"
                            onClick={() => {
                              const reason = prompt(
                                "Reason for revocation?",
                                "",
                              );
                              if (!reason) return;
                              revoke.mutate({ id: c.id, reason });
                            }}
                          >
                            <ShieldOff className="size-4 text-error" />
                          </Button>
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

      {issueOpen && (
        <IssueModal
          draft={issueDraft}
          setDraft={setIssueDraft}
          employees={employees}
          onClose={() => setIssueOpen(false)}
          onSave={() => issue.mutate()}
          saving={issue.isPending}
        />
      )}

      {editing && (
        <EditModal
          cert={editing}
          draft={editDraft}
          setDraft={setEditDraft}
          onClose={() => setEditing(null)}
          onSave={() => update.mutate()}
          saving={update.isPending}
        />
      )}

      {previewing && (
        <PreviewModal
          cert={previewing}
          empLabel={(() => {
            const emp = empById.get(previewing.employee_id);
            return emp
              ? `${emp.first_name} ${emp.last_name}`
              : `Employee #${previewing.employee_id}`;
          })()}
          onClose={() => setPreviewing(null)}
        />
      )}
    </div>
  );
}

function IssueModal({
  draft,
  setDraft,
  employees,
  onClose,
  onSave,
  saving,
}: {
  draft: IssueDraft;
  setDraft: (d: IssueDraft) => void;
  employees: { id: number; employee_code: string; first_name: string; last_name: string }[];
  onClose: () => void;
  onSave: () => void;
  saving: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Award className="size-5 text-brand-gold-dark" />
              Issue certificate
            </CardTitle>
            <CardDescription>
              The certificate number is auto-generated. The PDF gets a QR code
              linking to the public verification URL.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <Label>Employee *</Label>
            <select
              value={draft.employee_id}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  employee_id: e.target.value ? Number(e.target.value) : "",
                })
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">— Select —</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.employee_code} — {emp.first_name} {emp.last_name}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <Label>Title *</Label>
            <Input
              placeholder="e.g. Field Verification Mastery"
              value={draft.title}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            />
          </div>
          <div>
            <Label>Issued date</Label>
            <Input
              type="date"
              value={draft.issued_date}
              onChange={(e) =>
                setDraft({ ...draft, issued_date: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Expiry date</Label>
            <Input
              type="date"
              value={draft.expiry_date}
              onChange={(e) =>
                setDraft({ ...draft, expiry_date: e.target.value })
              }
              placeholder="No expiry"
            />
          </div>
          <div>
            <Label>Score %</Label>
            <Input
              type="number"
              min={0}
              max={100}
              step="0.5"
              value={draft.score_percentage}
              onChange={(e) =>
                setDraft({ ...draft, score_percentage: e.target.value })
              }
              placeholder="optional"
            />
          </div>
          <div className="md:col-span-2 flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              disabled={saving || !draft.employee_id || !draft.title}
              onClick={onSave}
            >
              {saving ? "Issuing…" : "Issue"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function EditModal({
  cert,
  draft,
  setDraft,
  onClose,
  onSave,
  saving,
}: {
  cert: Certificate;
  draft: EditDraft;
  setDraft: (d: EditDraft) => void;
  onClose: () => void;
  onSave: () => void;
  saving: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Edit certificate</CardTitle>
            <CardDescription className="font-mono text-xs">
              {cert.certificate_number}
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <Label>Title</Label>
            <Input
              value={draft.title}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            />
          </div>
          <div>
            <Label>Issued date</Label>
            <Input
              type="date"
              value={draft.issued_date}
              onChange={(e) =>
                setDraft({ ...draft, issued_date: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Expiry date</Label>
            <Input
              type="date"
              value={draft.expiry_date}
              onChange={(e) =>
                setDraft({ ...draft, expiry_date: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Score %</Label>
            <Input
              type="number"
              min={0}
              max={100}
              step="0.5"
              value={draft.score_percentage}
              onChange={(e) =>
                setDraft({ ...draft, score_percentage: e.target.value })
              }
            />
          </div>
          <div className="md:col-span-2 flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button disabled={saving} onClick={onSave}>
              {saving ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function PreviewModal({
  cert,
  empLabel,
  onClose,
}: {
  cert: Certificate;
  empLabel: string;
  onClose: () => void;
}) {
  const pdf = examApi.certificatePdfUrl(cert.id);
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-5xl max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-2 text-white">
          <div>
            <div className="font-display text-xl">{cert.title}</div>
            <div className="text-xs opacity-80 font-mono">
              {cert.certificate_number} · {empLabel}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <a
              href={pdf}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-xs hover:underline"
            >
              <Download className="size-3" /> Download PDF
            </a>
            <button
              onClick={onClose}
              className="text-white/80 hover:text-white text-2xl leading-none"
              title="Close"
            >
              ×
            </button>
          </div>
        </div>
        <iframe
          title={cert.certificate_number}
          src={pdf}
          className="w-full flex-1 bg-white rounded"
        />
      </div>
    </div>
  );
}
