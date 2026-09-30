import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  FileText,
  Paperclip,
  Search,
  Trash2,
  Upload,
  XCircle,
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
import { launchApi, type Resignation } from "@/lib/api/launch";
import { employeesApi } from "@/lib/api/employees";
import { fmtIstDate } from "@/lib/datetime";
import { API_BASE_URL } from "@/lib/constants";
import { SeparationActions } from "./SeparationActions";

const STATUS_COLOR: Record<string, string> = {
  submitted: "bg-info/15 text-info",
  manager_review: "bg-info/15 text-info",
  accepted: "bg-info/25 text-info",
  in_notice: "bg-brand-gold/15 text-brand-gold-dark",
  ndc_pending: "bg-warning/15 text-warning",
  cleared: "bg-success/15 text-success",
  settled: "bg-brand-brown-50 text-brand-brown-darker",
  rejected: "bg-error/15 text-error",
  cancelled: "bg-brand-brown-50 text-brand-brown-darker",
};

const DOC_KINDS = [
  "resignation_letter",
  "noc",
  "experience_letter",
  "settlement_sheet",
  "asset_handover",
  "other",
];

const PAGE_SIZE = 8;

function fmtBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function absUrl(u: string): string {
  return u.startsWith("http") ? u : `${API_BASE_URL}${u}`;
}

export default function ResignationsPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [employeeFilter, setEmployeeFilter] = useState<number | "">("");
  const [page, setPage] = useState(1);

  const [target, setTarget] = useState<Resignation | null>(null);
  const [comment, setComment] = useState("");
  const [amount, setAmount] = useState("");
  const [notes, setNotes] = useState("");

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadFor, setUploadFor] = useState<{
    id: number;
    kind: string;
  } | null>(null);

  const { data: items = [], isLoading } = useQuery({
    queryKey: ["resignations", search, statusFilter, employeeFilter],
    queryFn: () =>
      launchApi.listResignations({
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        employee_id: employeeFilter === "" ? undefined : employeeFilter,
      }),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });

  const decide = useMutation({
    mutationFn: ({ id, accept }: { id: number; accept: boolean }) =>
      launchApi.decideResignation(id, accept, comment),
    onSuccess: () => {
      toast.success("Saved");
      setComment("");
      qc.invalidateQueries({ queryKey: ["resignations"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed"),
  });

  const updateNdc = useMutation({
    mutationFn: ({
      id,
      updates,
    }: {
      id: number;
      updates: Record<string, boolean>;
    }) => launchApi.updateNdc(id, updates),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["resignations"] }),
  });

  const settle = useMutation({
    mutationFn: ({ id }: { id: number }) =>
      launchApi.settleResignation(id, Number(amount), notes || undefined),
    onSuccess: () => {
      toast.success("Settlement recorded");
      setTarget(null);
      setAmount("");
      setNotes("");
      qc.invalidateQueries({ queryKey: ["resignations"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed"),
  });

  const uploadDoc = useMutation({
    mutationFn: ({
      id,
      file,
      kind,
    }: {
      id: number;
      file: File;
      kind: string;
    }) => launchApi.uploadResignationDocument(id, file, kind),
    onSuccess: () => {
      toast.success("Document attached");
      qc.invalidateQueries({ queryKey: ["resignations"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Upload failed"),
  });

  const removeDoc = useMutation({
    mutationFn: ({ id, idx }: { id: number; idx: number }) =>
      launchApi.removeResignationDocument(id, idx),
    onSuccess: () => {
      toast.success("Document removed");
      qc.invalidateQueries({ queryKey: ["resignations"] });
    },
  });

  const empById = useMemo(
    () => new Map(employees.map((e) => [e.id, e])),
    [employees],
  );

  const onFileChosen = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || uploadFor == null) return;
    uploadDoc.mutate({ id: uploadFor.id, file, kind: uploadFor.kind });
    setUploadFor(null);
  };

  const triggerUpload = (id: number, kind: string) => {
    setUploadFor({ id, kind });
    setTimeout(() => fileInputRef.current?.click(), 0);
  };

  const pageCount = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const pageRows = items.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (isLoading) return <LoadingScreen label="Loading resignations…" />;

  return (
    <div className="space-y-6">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.zip,.csv,.xls,.xlsx,.png,.jpg,.jpeg,.webp"
        className="hidden"
        onChange={onFileChosen}
      />

      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Resignations
        </h1>
        <p className="text-sm text-brand-brown-light">
          {items.length} resignation{items.length === 1 ? "" : "s"} match
          current filters. Drive the offboarding lifecycle from acceptance
          through final settlement.
        </p>
      </div>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-3">
          <div className="md:col-span-1 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search reason / comments / notes…"
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
            {Object.keys(STATUS_COLOR).map((s) => (
              <option key={s} value={s}>
                {s.replaceAll("_", " ")}
              </option>
            ))}
          </select>
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
        </CardContent>
      </Card>

      {pageRows.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-brand-brown-light">
            No resignations match these filters.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {pageRows.map((r) => {
            const ndc = r.ndc_checklist ?? {};
            const ndcKeys = Object.keys(ndc);
            const ndcChecked = ndcKeys.filter((k) => ndc[k]).length;
            const emp = empById.get(r.employee_id);
            const docs = r.documents ?? [];
            return (
              <Card key={r.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base">
                      {emp
                        ? `${emp.employee_code} · ${emp.first_name} ${emp.last_name}`
                        : `Employee #${r.employee_id}`}
                      <span className="ml-2 text-xs text-brand-brown-light font-normal">
                        LWD {r.proposed_last_working_day}
                      </span>
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${STATUS_COLOR[r.status] ?? ""}`}
                      >
                        {r.status.replaceAll("_", " ")}
                      </span>
                      <SeparationActions
                        resignation={r}
                        employeeLabel={
                          emp
                            ? `${emp.first_name} ${emp.last_name}`
                            : `Employee #${r.employee_id}`
                        }
                      />
                    </div>
                  </div>
                  <CardDescription>
                    Notice {r.notice_period_days} days · Requested{" "}
                    {fmtIstDate(r.requested_at)}
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
                    <div className="flex items-center gap-2 flex-wrap">
                      <Input
                        placeholder="Optional comment"
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        className="flex-1 min-w-[200px]"
                      />
                      <Button
                        variant="outline"
                        className="gap-1"
                        onClick={() =>
                          decide.mutate({ id: r.id, accept: true })
                        }
                      >
                        <CheckCircle2 className="size-4" /> Accept
                      </Button>
                      <Button
                        variant="destructive"
                        className="gap-1"
                        onClick={() =>
                          decide.mutate({ id: r.id, accept: false })
                        }
                      >
                        <XCircle className="size-4" /> Reject
                      </Button>
                    </div>
                  )}

                  {(r.status === "in_notice" ||
                    r.status === "ndc_pending" ||
                    r.status === "cleared" ||
                    r.status === "settled") &&
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
                                disabled={
                                  r.status === "settled" ||
                                  r.status === "rejected"
                                }
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

                  {/* Documents */}
                  <div className="rounded-md border border-brand-brown-50 p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-xs font-semibold uppercase text-brand-gold-dark inline-flex items-center gap-1">
                        <Paperclip className="size-3" /> Documents ({docs.length})
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {DOC_KINDS.map((k) => (
                          <Button
                            key={k}
                            size="sm"
                            variant="outline"
                            className="text-[10px] h-7"
                            onClick={() => triggerUpload(r.id, k)}
                          >
                            <Upload className="size-3 mr-1" />
                            {k.replaceAll("_", " ")}
                          </Button>
                        ))}
                      </div>
                    </div>
                    {docs.length === 0 ? (
                      <div className="text-xs text-brand-brown-light">
                        No documents attached yet.
                      </div>
                    ) : (
                      <ul className="space-y-1">
                        {docs.map((d, i) => (
                          <li
                            key={i}
                            className="flex items-center justify-between text-xs"
                          >
                            <a
                              href={absUrl(d.url)}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-brand-gold-dark hover:underline truncate"
                              title={d.name}
                            >
                              <FileText className="size-3 shrink-0" />
                              <span className="truncate max-w-[260px]">
                                {d.name}
                              </span>
                              <span className="text-brand-brown-light">
                                · {d.kind.replaceAll("_", " ")} ·{" "}
                                {fmtBytes(d.size)}
                              </span>
                            </a>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() =>
                                removeDoc.mutate({ id: r.id, idx: i })
                              }
                            >
                              <Trash2 className="size-3 text-destructive" />
                            </Button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {r.status === "cleared" && (
                    <div className="rounded-md border border-success/30 bg-success/5 p-3 space-y-2">
                      <div className="flex items-center gap-1 text-success font-semibold text-xs">
                        <CheckCircle2 className="size-4" />
                        NDC cleared — ready for final settlement
                      </div>
                      {target?.id === r.id ? (
                        <div className="space-y-2">
                          <div>
                            <Label>Final settlement amount (₹)</Label>
                            <Input
                              type="number"
                              value={amount}
                              onChange={(e) => setAmount(e.target.value)}
                            />
                          </div>
                          <div>
                            <Label>Exit interview notes</Label>
                            <Input
                              value={notes}
                              onChange={(e) => setNotes(e.target.value)}
                            />
                          </div>
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
                              Record settlement
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

                  {r.status === "settled" && (
                    <div className="rounded-md border border-brand-brown-50 bg-brand-brown-50/40 p-3 text-xs">
                      Settled at {fmtIstDate(r.final_settled_at ?? "")} · ₹
                      {(r.final_settlement_amount ?? 0).toLocaleString("en-IN")}
                      {r.exit_interview_notes && (
                        <div className="mt-1 text-brand-brown-light">
                          Exit notes: {r.exit_interview_notes}
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

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
