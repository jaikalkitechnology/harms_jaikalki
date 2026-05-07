import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil, Plus, Search, Trash2, X } from "lucide-react";

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
import { salesApi, type Lead } from "@/lib/api/sales";
import { fieldApi } from "@/lib/api/field";
import { employeesApi, type EmployeeListItem } from "@/lib/api/employees";

const SOURCES = [
  "website",
  "referral",
  "cold_call",
  "exhibition",
  "campaign",
  "field_visit",
  "partner",
  "other",
];

const STAGES = [
  "new",
  "contacted",
  "qualified",
  "proposal",
  "negotiation",
  "won",
  "lost",
] as const;

const STAGE_COLOR: Record<Lead["stage"], string> = {
  new: "bg-info/15 text-info",
  contacted: "bg-brand-gold/15 text-brand-gold-dark",
  qualified: "bg-brand-gold/25 text-brand-gold-dark",
  proposal: "bg-warning/15 text-warning",
  negotiation: "bg-warning/25 text-warning",
  won: "bg-success/15 text-success",
  lost: "bg-error/15 text-error",
};

interface LeadDraft {
  customer_id: number | null;
  contact_name: string;
  contact_phone: string;
  contact_email: string;
  source: string;
  stage: Lead["stage"];
  expected_value: string;
  expected_close_date: string;
  assigned_to: number | null;
  next_action: string;
  next_action_date: string;
  notes: string;
  lost_reason: string;
}

const EMPTY_DRAFT: LeadDraft = {
  customer_id: null,
  contact_name: "",
  contact_phone: "",
  contact_email: "",
  source: "other",
  stage: "new",
  expected_value: "",
  expected_close_date: "",
  assigned_to: null,
  next_action: "",
  next_action_date: "",
  notes: "",
  lost_reason: "",
};

export default function LeadsPage() {
  const qc = useQueryClient();
  const [stage, setStage] = useState<string>("");
  const [source, setSource] = useState<string>("");
  const [customerId, setCustomerId] = useState<number | "">("");
  const [assignedTo, setAssignedTo] = useState<number | "">("");
  const [search, setSearch] = useState("");
  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<Lead | null>(null);
  const [draft, setDraft] = useState<LeadDraft>(EMPTY_DRAFT);

  const { data: leads = [], isLoading } = useQuery({
    queryKey: ["sales-leads", stage, source, customerId, assignedTo, search],
    queryFn: () =>
      salesApi.listLeads({
        stage: stage || undefined,
        source: source || undefined,
        customer_id: customerId === "" ? undefined : customerId,
        assigned_to: assignedTo === "" ? undefined : assignedTo,
        search: search || undefined,
      }),
  });

  const { data: customers = [] } = useQuery({
    queryKey: ["field-customers"],
    queryFn: () => fieldApi.listCustomers(),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-active-leads"],
    queryFn: () => employeesApi.list(),
  });
  const empById = useMemo(() => {
    const m = new Map<number, EmployeeListItem>();
    employees.forEach((e) => m.set(e.id, e));
    return m;
  }, [employees]);
  const custById = useMemo(() => {
    const m = new Map<number, { id: number; name: string }>();
    customers.forEach((c) => m.set(c.id, { id: c.id, name: c.name }));
    return m;
  }, [customers]);

  const create = useMutation({
    mutationFn: () =>
      salesApi.createLead({
        customer_id: draft.customer_id,
        contact_name: draft.contact_name || null,
        contact_phone: draft.contact_phone || null,
        contact_email: draft.contact_email || null,
        source: draft.source,
        expected_value: draft.expected_value
          ? Number(draft.expected_value)
          : 0,
        expected_close_date: draft.expected_close_date || null,
        assigned_to: draft.assigned_to,
        next_action: draft.next_action || null,
        next_action_date: draft.next_action_date || null,
        notes: draft.notes || null,
      }),
    onSuccess: () => {
      toast.success("Lead created");
      setEditorOpen(false);
      setDraft(EMPTY_DRAFT);
      qc.invalidateQueries({ queryKey: ["sales-leads"] });
    },
    onError: () => toast.error("Could not create lead"),
  });

  const update = useMutation({
    mutationFn: () =>
      salesApi.updateLead(editing!.id, {
        customer_id: draft.customer_id,
        contact_name: draft.contact_name || null,
        contact_phone: draft.contact_phone || null,
        contact_email: draft.contact_email || null,
        source: draft.source,
        expected_value: draft.expected_value
          ? Number(draft.expected_value)
          : 0,
        expected_close_date: draft.expected_close_date || null,
        assigned_to: draft.assigned_to,
        next_action: draft.next_action || null,
        next_action_date: draft.next_action_date || null,
        notes: draft.notes || null,
        lost_reason: draft.lost_reason || null,
      }),
    onSuccess: () => {
      toast.success("Lead saved");
      setEditorOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["sales-leads"] });
    },
    onError: () => toast.error("Save failed"),
  });

  const stageMutation = useMutation({
    mutationFn: ({ id, stage }: { id: number; stage: string }) =>
      salesApi.updateStage(id, stage),
    onSuccess: () => {
      toast.success("Stage updated");
      qc.invalidateQueries({ queryKey: ["sales-leads"] });
    },
    onError: () => toast.error("Could not update stage"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => salesApi.deleteLead(id),
    onSuccess: () => {
      toast.success("Lead deleted");
      qc.invalidateQueries({ queryKey: ["sales-leads"] });
    },
    onError: () => toast.error("Could not delete"),
  });

  const openCreate = () => {
    setEditing(null);
    setDraft(EMPTY_DRAFT);
    setEditorOpen(true);
  };
  const openEdit = (l: Lead) => {
    setEditing(l);
    setDraft({
      customer_id: l.customer_id,
      contact_name: l.contact_name ?? "",
      contact_phone: l.contact_phone ?? "",
      contact_email: l.contact_email ?? "",
      source: l.source,
      stage: l.stage,
      expected_value: String(l.expected_value ?? ""),
      expected_close_date: l.expected_close_date ?? "",
      assigned_to: l.assigned_to,
      next_action: l.next_action ?? "",
      next_action_date: l.next_action_date ?? "",
      notes: l.notes ?? "",
      lost_reason: l.lost_reason ?? "",
    });
    setEditorOpen(true);
  };

  if (isLoading) return <LoadingScreen label="Loading leads…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Sales · Leads
          </div>
          <h1 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            Leads <span className="display-em">pipeline</span>
          </h1>
          <p className="text-sm text-brand-brown-light mt-1">
            {leads.length} lead{leads.length === 1 ? "" : "s"} matching the
            current filters.
          </p>
        </div>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4 mr-1" /> New lead
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filter</CardTitle>
          <CardDescription>
            Combine to narrow the list. Search hits name / phone / email /
            notes.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="md:col-span-2 relative">
            <Search className="h-4 w-4 absolute left-2 top-9 text-brand-brown-light" />
            <Label>Search</Label>
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Contact, phone, email, notes…"
              className="pl-8"
            />
          </div>
          <div>
            <Label>Stage</Label>
            <select
              value={stage}
              onChange={(e) => setStage(e.target.value)}
              className="w-full h-10 rounded-md border border-input bg-card px-3 text-sm"
            >
              <option value="">All</option>
              {STAGES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Source</Label>
            <select
              value={source}
              onChange={(e) => setSource(e.target.value)}
              className="w-full h-10 rounded-md border border-input bg-card px-3 text-sm"
            >
              <option value="">All</option>
              {SOURCES.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Customer</Label>
            <select
              value={customerId}
              onChange={(e) =>
                setCustomerId(e.target.value ? Number(e.target.value) : "")
              }
              className="w-full h-10 rounded-md border border-input bg-card px-3 text-sm"
            >
              <option value="">All</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <Label>Assigned to</Label>
            <select
              value={assignedTo}
              onChange={(e) =>
                setAssignedTo(e.target.value ? Number(e.target.value) : "")
              }
              className="w-full h-10 rounded-md border border-input bg-card px-3 text-sm"
            >
              <option value="">Anyone</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.employee_code} — {e.first_name} {e.last_name}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm min-w-[900px]">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Contact</th>
                <th className="px-4 py-3">Customer</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Stage</th>
                <th className="px-4 py-3 text-right">Value</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Owner</th>
                <th className="px-4 py-3">Next</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {leads.length === 0 ? (
                <tr>
                  <td
                    colSpan={9}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No leads match the filters.
                  </td>
                </tr>
              ) : (
                leads.map((ld) => {
                  const owner = ld.assigned_to
                    ? empById.get(ld.assigned_to)
                    : null;
                  const cust = ld.customer_id
                    ? custById.get(ld.customer_id)
                    : null;
                  return (
                    <tr
                      key={ld.id}
                      className="border-t border-brand-brown-50 hover:bg-brand-brown-50/30"
                    >
                      <td className="px-4 py-3 font-medium">
                        {ld.contact_name ?? `Lead #${ld.id}`}
                        {(ld.contact_phone || ld.contact_email) && (
                          <div className="text-xs text-brand-brown-light">
                            {ld.contact_phone}
                            {ld.contact_phone && ld.contact_email && " · "}
                            {ld.contact_email}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-brand-brown-light">
                        {cust?.name ?? "—"}
                      </td>
                      <td className="px-4 py-3 capitalize">
                        {ld.source.replace("_", " ")}
                      </td>
                      <td className="px-4 py-3">
                        <select
                          className={`text-xs px-2 py-1 rounded border-0 ${STAGE_COLOR[ld.stage]}`}
                          value={ld.stage}
                          onChange={(e) =>
                            stageMutation.mutate({
                              id: ld.id,
                              stage: e.target.value,
                            })
                          }
                        >
                          {STAGES.map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3 text-right">
                        ₹{Number(ld.expected_value).toLocaleString("en-IN")}
                      </td>
                      <td className="px-4 py-3">{ld.score}</td>
                      <td className="px-4 py-3 text-xs text-brand-brown-light">
                        {owner
                          ? `${owner.first_name} ${owner.last_name}`
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-xs text-brand-brown-light">
                        {ld.next_action ?? "—"}
                        {ld.next_action_date && (
                          <div className="text-[10px]">{ld.next_action_date}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => openEdit(ld)}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>{" "}
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            if (
                              confirm(
                                `Delete lead "${ld.contact_name ?? `#${ld.id}`}"?`,
                              )
                            )
                              remove.mutate(ld.id);
                          }}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {editorOpen && (
        <Editor
          mode={editing ? "edit" : "create"}
          draft={draft}
          setDraft={setDraft}
          customers={customers.map((c) => ({ id: c.id, name: c.name }))}
          employees={employees}
          onClose={() => {
            setEditorOpen(false);
            setEditing(null);
          }}
          onSubmit={() => (editing ? update.mutate() : create.mutate())}
          submitting={create.isPending || update.isPending}
        />
      )}
    </div>
  );
}

function Editor({
  mode,
  draft,
  setDraft,
  customers,
  employees,
  onClose,
  onSubmit,
  submitting,
}: {
  mode: "create" | "edit";
  draft: LeadDraft;
  setDraft: (v: LeadDraft) => void;
  customers: { id: number; name: string }[];
  employees: EmployeeListItem[];
  onClose: () => void;
  onSubmit: () => void;
  submitting: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-start md:items-center justify-center p-4 bg-black/40">
      <div className="bg-card rounded-xl border border-brand-brown-100 shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-brand-brown-100">
          <div className="font-display text-lg">
            {mode === "create" ? "New" : "Edit"} lead
          </div>
          <button
            onClick={onClose}
            className="h-8 w-8 grid place-items-center rounded-lg hover:bg-brand-brown-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="overflow-y-auto p-4 grid sm:grid-cols-2 gap-3">
          <div>
            <Label>Contact name</Label>
            <Input
              value={draft.contact_name}
              onChange={(e) =>
                setDraft({ ...draft, contact_name: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Contact phone</Label>
            <Input
              value={draft.contact_phone}
              onChange={(e) =>
                setDraft({ ...draft, contact_phone: e.target.value })
              }
            />
          </div>
          <div className="sm:col-span-2">
            <Label>Contact email</Label>
            <Input
              type="email"
              value={draft.contact_email}
              onChange={(e) =>
                setDraft({ ...draft, contact_email: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Customer</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.customer_id ?? ""}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  customer_id: e.target.value ? Number(e.target.value) : null,
                })
              }
            >
              <option value="">— Optional —</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Source</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.source}
              onChange={(e) => setDraft({ ...draft, source: e.target.value })}
            >
              {SOURCES.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Expected value (₹)</Label>
            <Input
              type="number"
              value={draft.expected_value}
              onChange={(e) =>
                setDraft({ ...draft, expected_value: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Expected close date</Label>
            <Input
              type="date"
              value={draft.expected_close_date}
              onChange={(e) =>
                setDraft({ ...draft, expected_close_date: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Assigned to</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.assigned_to ?? ""}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  assigned_to: e.target.value ? Number(e.target.value) : null,
                })
              }
            >
              <option value="">— Unassigned —</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.employee_code} — {e.first_name} {e.last_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Next action date</Label>
            <Input
              type="date"
              value={draft.next_action_date}
              onChange={(e) =>
                setDraft({ ...draft, next_action_date: e.target.value })
              }
            />
          </div>
          <div className="sm:col-span-2">
            <Label>Next action</Label>
            <Input
              value={draft.next_action}
              onChange={(e) =>
                setDraft({ ...draft, next_action: e.target.value })
              }
              placeholder="Call, schedule demo, send proposal…"
            />
          </div>
          <div className="sm:col-span-2">
            <Label>Notes</Label>
            <textarea
              rows={3}
              className="w-full border border-brand-brown-50 rounded p-2 text-sm bg-card"
              value={draft.notes}
              onChange={(e) => setDraft({ ...draft, notes: e.target.value })}
            />
          </div>
          {mode === "edit" && draft.stage === "lost" && (
            <div className="sm:col-span-2">
              <Label>Lost reason</Label>
              <Input
                value={draft.lost_reason}
                onChange={(e) =>
                  setDraft({ ...draft, lost_reason: e.target.value })
                }
              />
            </div>
          )}
        </div>
        <div className="p-4 border-t border-brand-brown-100 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button disabled={submitting} onClick={onSubmit}>
            {mode === "create" ? "Create" : "Save changes"}
          </Button>
        </div>
      </div>
    </div>
  );
}

// silence unused warnings on lints that don't notice JSX usage
void useEffect;
