import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  FileDown,
  Pencil,
  Plus,
  Search,
  X,
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
import { compensationApi, type SalaryRevision } from "@/lib/api/compensation";
import { employeesApi } from "@/lib/api/employees";

const STATUS_COLOR: Record<string, string> = {
  draft: "bg-brand-brown-50 text-brand-brown-darker",
  pending_approval: "bg-info/15 text-info",
  approved: "bg-brand-gold/15 text-brand-gold-dark",
  applied: "bg-success/15 text-success",
  rejected: "bg-error/15 text-error",
  cancelled: "bg-brand-brown-50 text-brand-brown-darker",
};

const REASONS = [
  "annual_review",
  "promotion",
  "market_correction",
  "retention",
  "role_change",
  "other",
];

const PAGE_SIZE = 12;

interface ProposeDraft {
  employee_id: number | "";
  new_ctc_annual: string;
  effective_date: string;
  reason: string;
  notes: string;
}

interface EditDraft {
  new_ctc_annual: string;
  effective_date: string;
  reason: string;
  notes: string;
}

const todayStr = new Date().toISOString().slice(0, 10);

const EMPTY_PROPOSE: ProposeDraft = {
  employee_id: "",
  new_ctc_annual: "",
  effective_date: todayStr,
  reason: "annual_review",
  notes: "",
};

export default function SalaryRevisionsPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [employeeFilter, setEmployeeFilter] = useState<number | "">("");
  const [statusFilter, setStatusFilter] = useState("");
  const [reasonFilter, setReasonFilter] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [page, setPage] = useState(1);

  const [proposeOpen, setProposeOpen] = useState(false);
  const [proposeDraft, setProposeDraft] = useState<ProposeDraft>(EMPTY_PROPOSE);

  const [editing, setEditing] = useState<SalaryRevision | null>(null);
  const [editDraft, setEditDraft] = useState<EditDraft>({
    new_ctc_annual: "",
    effective_date: "",
    reason: "annual_review",
    notes: "",
  });

  const { data: list = [], isLoading } = useQuery({
    queryKey: [
      "compensation-revisions",
      employeeFilter,
      statusFilter,
      reasonFilter,
      fromDate,
      toDate,
    ],
    queryFn: () =>
      compensationApi.listAll({
        employee_id: employeeFilter === "" ? undefined : employeeFilter,
        status: statusFilter || undefined,
        reason: reasonFilter || undefined,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
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

  const propose = useMutation({
    mutationFn: () =>
      compensationApi.propose({
        employee_id: Number(proposeDraft.employee_id),
        new_ctc_annual: Number(proposeDraft.new_ctc_annual),
        effective_date: proposeDraft.effective_date,
        reason: proposeDraft.reason,
        notes: proposeDraft.notes || undefined,
      }),
    onSuccess: () => {
      toast.success("Revision proposed");
      setProposeOpen(false);
      setProposeDraft(EMPTY_PROPOSE);
      qc.invalidateQueries({ queryKey: ["compensation-revisions"] });
      qc.invalidateQueries({ queryKey: ["compensation-pending"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not propose"),
  });

  const update = useMutation({
    mutationFn: () =>
      compensationApi.update(editing!.id, {
        new_ctc_annual: editDraft.new_ctc_annual
          ? Number(editDraft.new_ctc_annual)
          : undefined,
        effective_date: editDraft.effective_date || undefined,
        reason: editDraft.reason || undefined,
        notes: editDraft.notes,
      }),
    onSuccess: () => {
      toast.success("Revision updated");
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["compensation-revisions"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not update"),
  });

  const decide = useMutation({
    mutationFn: ({
      id,
      action,
    }: {
      id: number;
      action: "approve" | "reject" | "apply" | "cancel";
    }) =>
      action === "approve"
        ? compensationApi.approve(id)
        : action === "reject"
          ? compensationApi.reject(id)
          : action === "apply"
            ? compensationApi.apply(id)
            : compensationApi.cancel(id),
    onSuccess: () => {
      toast.success("Updated");
      qc.invalidateQueries({ queryKey: ["compensation-revisions"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Failed"),
  });

  const filtered = useMemo(() => {
    if (!search.trim()) return list;
    const q = search.trim().toLowerCase();
    return list.filter((r) => {
      const emp = empById.get(r.employee_id);
      const hay = [
        emp ? `${emp.employee_code} ${emp.first_name} ${emp.last_name}` : "",
        r.notes ?? "",
        r.reason,
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [list, search, empById]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageRows = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const openEdit = (r: SalaryRevision) => {
    setEditing(r);
    setEditDraft({
      new_ctc_annual: r.new_ctc_annual,
      effective_date: r.effective_date,
      reason: r.reason,
      notes: r.notes ?? "",
    });
  };

  if (isLoading) return <LoadingScreen label="Loading revisions…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Salary Revisions
          </h1>
          <p className="text-sm text-brand-brown-light">
            {filtered.length} revision{filtered.length === 1 ? "" : "s"} match
            current filters. Increment letters generate automatically on
            apply.
          </p>
        </div>
        <Button onClick={() => setProposeOpen(true)} className="gap-2">
          <Plus className="size-4" /> Propose revision
        </Button>
      </div>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-3">
          <div className="md:col-span-3 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search employee / notes / reason…"
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
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All statuses</option>
            {Object.keys(STATUS_COLOR).map((s) => (
              <option key={s} value={s}>
                {s.replace("_", " ")}
              </option>
            ))}
          </select>
          <select
            value={reasonFilter}
            onChange={(e) => {
              setReasonFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All reasons</option>
            {REASONS.map((r) => (
              <option key={r} value={r}>
                {r.replaceAll("_", " ")}
              </option>
            ))}
          </select>
          <div className="flex gap-2 md:col-span-2">
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
                <th className="px-4 py-3">Employee</th>
                <th className="px-4 py-3">Reason</th>
                <th className="px-4 py-3">Previous</th>
                <th className="px-4 py-3">New</th>
                <th className="px-4 py-3">Increment</th>
                <th className="px-4 py-3">Effective</th>
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
                    No revisions match these filters.
                  </td>
                </tr>
              ) : (
                pageRows.map((r) => {
                  const emp = empById.get(r.employee_id);
                  const editable =
                    r.status === "draft" || r.status === "pending_approval";
                  return (
                    <tr key={r.id} className="border-t border-brand-brown-50">
                      <td className="px-4 py-3">
                        {emp
                          ? `${emp.employee_code} — ${emp.first_name} ${emp.last_name}`
                          : `Employee #${r.employee_id}`}
                        {r.notes && (
                          <div className="text-[11px] text-brand-brown-light truncate max-w-xs">
                            {r.notes}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 capitalize text-xs">
                        {r.reason.replaceAll("_", " ")}
                      </td>
                      <td className="px-4 py-3">
                        ₹
                        {Number(r.previous_ctc_annual).toLocaleString("en-IN")}
                      </td>
                      <td className="px-4 py-3 font-semibold">
                        ₹{Number(r.new_ctc_annual).toLocaleString("en-IN")}
                      </td>
                      <td className="px-4 py-3 text-success">
                        +{Number(r.increment_pct).toFixed(2)}%
                      </td>
                      <td className="px-4 py-3 text-xs">{r.effective_date}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${STATUS_COLOR[r.status] ?? ""}`}
                        >
                          {r.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end flex-wrap gap-1">
                          {editable && (
                            <Button
                              size="sm"
                              variant="ghost"
                              title="Edit"
                              onClick={() => openEdit(r)}
                            >
                              <Pencil className="size-3" />
                            </Button>
                          )}
                          {r.status === "pending_approval" && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() =>
                                  decide.mutate({ id: r.id, action: "approve" })
                                }
                              >
                                <CheckCircle2 className="size-3 mr-1" />
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() =>
                                  decide.mutate({ id: r.id, action: "reject" })
                                }
                              >
                                <XCircle className="size-3 mr-1" />
                                Reject
                              </Button>
                            </>
                          )}
                          {r.status === "approved" && (
                            <Button
                              size="sm"
                              onClick={() =>
                                decide.mutate({ id: r.id, action: "apply" })
                              }
                            >
                              Apply now
                            </Button>
                          )}
                          {r.increment_letter_url && (
                            <a
                              href={r.increment_letter_url}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <Button size="sm" variant="ghost">
                                <FileDown className="size-3 mr-1" />
                                Letter
                              </Button>
                            </a>
                          )}
                        </div>
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

      {proposeOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card className="w-full max-w-2xl">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Propose new revision</CardTitle>
                <CardDescription>
                  Approver must be a different user than the proposer.
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setProposeOpen(false)}
              >
                <X className="size-4" />
              </Button>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <Label>Employee *</Label>
                <select
                  value={proposeDraft.employee_id}
                  onChange={(e) =>
                    setProposeDraft({
                      ...proposeDraft,
                      employee_id: e.target.value
                        ? Number(e.target.value)
                        : "",
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
              <div>
                <Label>Reason</Label>
                <select
                  value={proposeDraft.reason}
                  onChange={(e) =>
                    setProposeDraft({ ...proposeDraft, reason: e.target.value })
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {REASONS.map((r) => (
                    <option key={r} value={r}>
                      {r.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>New CTC (₹/yr) *</Label>
                <Input
                  type="number"
                  value={proposeDraft.new_ctc_annual}
                  onChange={(e) =>
                    setProposeDraft({
                      ...proposeDraft,
                      new_ctc_annual: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label>Effective from *</Label>
                <Input
                  type="date"
                  value={proposeDraft.effective_date}
                  onChange={(e) =>
                    setProposeDraft({
                      ...proposeDraft,
                      effective_date: e.target.value,
                    })
                  }
                />
              </div>
              <div className="md:col-span-2">
                <Label>Notes</Label>
                <Input
                  value={proposeDraft.notes}
                  onChange={(e) =>
                    setProposeDraft({ ...proposeDraft, notes: e.target.value })
                  }
                />
              </div>
              <div className="md:col-span-2 flex justify-end gap-2">
                <Button variant="outline" onClick={() => setProposeOpen(false)}>
                  Cancel
                </Button>
                <Button
                  disabled={
                    !proposeDraft.employee_id ||
                    !proposeDraft.new_ctc_annual ||
                    propose.isPending
                  }
                  onClick={() => propose.mutate()}
                >
                  Save
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {editing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card className="w-full max-w-2xl">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Edit revision #{editing.id}</CardTitle>
                <CardDescription>
                  Only draft / pending revisions can be edited. Approved or
                  applied revisions are locked.
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditing(null)}
              >
                <X className="size-4" />
              </Button>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>New CTC (₹/yr)</Label>
                <Input
                  type="number"
                  value={editDraft.new_ctc_annual}
                  onChange={(e) =>
                    setEditDraft({
                      ...editDraft,
                      new_ctc_annual: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label>Effective from</Label>
                <Input
                  type="date"
                  value={editDraft.effective_date}
                  onChange={(e) =>
                    setEditDraft({
                      ...editDraft,
                      effective_date: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label>Reason</Label>
                <select
                  value={editDraft.reason}
                  onChange={(e) =>
                    setEditDraft({ ...editDraft, reason: e.target.value })
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {REASONS.map((r) => (
                    <option key={r} value={r}>
                      {r.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <Label>Notes</Label>
                <Input
                  value={editDraft.notes}
                  onChange={(e) =>
                    setEditDraft({ ...editDraft, notes: e.target.value })
                  }
                />
              </div>
              <div className="md:col-span-2 flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditing(null)}>
                  Cancel
                </Button>
                <Button
                  disabled={update.isPending}
                  onClick={() => update.mutate()}
                >
                  Save
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
