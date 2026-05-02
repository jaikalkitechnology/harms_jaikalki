import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { CheckCircle2, FileDown, Plus, XCircle } from "lucide-react";

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
import { compensationApi } from "@/lib/api/compensation";
import { employeesApi } from "@/lib/api/employees";

const STATUS_COLOR: Record<string, string> = {
  draft: "bg-brand-brown-50 text-brand-brown-darker",
  pending_approval: "bg-info/15 text-info",
  approved: "bg-brand-gold/15 text-brand-gold-dark",
  applied: "bg-success/15 text-success",
  rejected: "bg-error/15 text-error",
  cancelled: "bg-brand-brown-50 text-brand-brown-darker",
};

export default function SalaryRevisionsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [newCtc, setNewCtc] = useState("");
  const [effectiveDate, setEffectiveDate] = useState(
    new Date().toISOString().slice(0, 10),
  );
  const [reason, setReason] = useState("annual_review");
  const [notes, setNotes] = useState("");

  const { data: pending = [], isLoading } = useQuery({
    queryKey: ["compensation-pending"],
    queryFn: compensationApi.pending,
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });

  const propose = useMutation({
    mutationFn: () =>
      compensationApi.propose({
        employee_id: Number(employeeId),
        new_ctc_annual: Number(newCtc),
        effective_date: effectiveDate,
        reason,
        notes: notes || undefined,
      }),
    onSuccess: () => {
      toast.success("Revision proposed");
      setShowForm(false);
      setEmployeeId("");
      setNewCtc("");
      setNotes("");
      qc.invalidateQueries({ queryKey: ["compensation-pending"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Could not propose"),
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
      qc.invalidateQueries({ queryKey: ["compensation-pending"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Failed"),
  });

  if (isLoading) return <LoadingScreen label="Loading revisions…" />;

  const empById = new Map(employees.map((e) => [e.id, e]));

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Salary Revisions
          </h1>
          <p className="text-sm text-brand-brown-light">
            {pending.length} revision{pending.length === 1 ? "" : "s"}{" "}
            in flight. Increment letters are generated automatically on
            apply.
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
          <Plus className="size-4" />
          {showForm ? "Cancel" : "Propose revision"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Propose new revision</CardTitle>
            <CardDescription>
              Approver must be a different user than the proposer.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Employee *</Label>
              <select
                value={employeeId}
                onChange={(e) =>
                  setEmployeeId(e.target.value ? Number(e.target.value) : "")
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
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="annual_review">Annual review</option>
                <option value="promotion">Promotion</option>
                <option value="market_correction">Market correction</option>
                <option value="retention">Retention</option>
                <option value="role_change">Role change</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <Label>New CTC (₹/yr) *</Label>
              <Input
                type="number"
                value={newCtc}
                onChange={(e) => setNewCtc(e.target.value)}
              />
            </div>
            <div>
              <Label>Effective from *</Label>
              <Input
                type="date"
                value={effectiveDate}
                onChange={(e) => setEffectiveDate(e.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Label>Notes</Label>
              <Input
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                disabled={!employeeId || !newCtc || propose.isPending}
                onClick={() => propose.mutate()}
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Employee</th>
                <th className="px-4 py-3">Previous</th>
                <th className="px-4 py-3">New</th>
                <th className="px-4 py-3">Increment</th>
                <th className="px-4 py-3">Effective</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {pending.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No revisions pending.
                  </td>
                </tr>
              ) : (
                pending.map((r) => {
                  const emp = empById.get(r.employee_id);
                  return (
                    <tr key={r.id} className="border-t border-brand-brown-50">
                      <td className="px-4 py-3">
                        {emp
                          ? `${emp.employee_code} — ${emp.first_name} ${emp.last_name}`
                          : `Employee #${r.employee_id}`}
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
                      <td className="px-4 py-3 text-xs">
                        {r.effective_date}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${STATUS_COLOR[r.status] ?? ""}`}
                        >
                          {r.status.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          {r.status === "pending_approval" && (
                            <>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() =>
                                  decide.mutate({
                                    id: r.id,
                                    action: "approve",
                                  })
                                }
                              >
                                <CheckCircle2 className="size-3 mr-1" />
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() =>
                                  decide.mutate({
                                    id: r.id,
                                    action: "reject",
                                  })
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
                                decide.mutate({
                                  id: r.id,
                                  action: "apply",
                                })
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
    </div>
  );
}
