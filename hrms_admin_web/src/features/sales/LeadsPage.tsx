import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus } from "lucide-react";

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

const STAGE_COLOR: Record<Lead["stage"], string> = {
  new: "bg-info/15 text-info",
  contacted: "bg-brand-gold/15 text-brand-gold-dark",
  qualified: "bg-brand-gold/25 text-brand-gold-dark",
  proposal: "bg-warning/15 text-warning",
  negotiation: "bg-warning/25 text-warning",
  won: "bg-success/15 text-success",
  lost: "bg-error/15 text-error",
};

export default function LeadsPage() {
  const qc = useQueryClient();
  const [stage, setStage] = useState<string>("");
  const [showForm, setShowForm] = useState(false);

  const [customerId, setCustomerId] = useState<number | "">("");
  const [contactName, setContactName] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [source, setSource] = useState("other");
  const [expectedValue, setExpectedValue] = useState("");
  const [notes, setNotes] = useState("");

  const { data: leads = [], isLoading } = useQuery({
    queryKey: ["sales-leads", stage],
    queryFn: () =>
      salesApi.listLeads(stage ? { stage } : undefined),
  });
  const { data: customers = [] } = useQuery({
    queryKey: ["field-customers"],
    queryFn: () => fieldApi.listCustomers(),
  });

  const create = useMutation({
    mutationFn: () =>
      salesApi.createLead({
        customer_id: customerId || null,
        contact_name: contactName || null,
        contact_phone: contactPhone || null,
        source,
        expected_value: expectedValue ? Number(expectedValue) : 0,
        notes: notes || null,
      }),
    onSuccess: () => {
      toast.success("Lead created");
      setCustomerId("");
      setContactName("");
      setContactPhone("");
      setExpectedValue("");
      setNotes("");
      setShowForm(false);
      qc.invalidateQueries({ queryKey: ["sales-leads"] });
      qc.invalidateQueries({ queryKey: ["sales-pipeline"] });
    },
    onError: () => toast.error("Could not create lead"),
  });

  if (isLoading) return <LoadingScreen label="Loading leads…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Leads
          </h1>
          <p className="text-sm text-brand-brown-light">
            CRM-lite — track every prospect from first contact to closed deal.
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
          <Plus className="size-4" />
          {showForm ? "Cancel" : "New lead"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create lead</CardTitle>
            <CardDescription>
              Will auto-assign to your employee record.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Customer</Label>
              <select
                value={customerId}
                onChange={(e) =>
                  setCustomerId(e.target.value ? Number(e.target.value) : "")
                }
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">— Select (optional) —</option>
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
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {SOURCES.map((s) => (
                  <option key={s} value={s}>
                    {s.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Contact name</Label>
              <Input
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
              />
            </div>
            <div>
              <Label>Contact phone</Label>
              <Input
                value={contactPhone}
                onChange={(e) => setContactPhone(e.target.value)}
              />
            </div>
            <div>
              <Label>Expected value (₹)</Label>
              <Input
                type="number"
                value={expectedValue}
                onChange={(e) => setExpectedValue(e.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Label>Notes</Label>
              <Input value={notes} onChange={(e) => setNotes(e.target.value)} />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                disabled={create.isPending}
                onClick={() => create.mutate()}
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-2">
        <Label className="text-xs">Stage:</Label>
        <select
          value={stage}
          onChange={(e) => setStage(e.target.value)}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All</option>
          <option value="new">New</option>
          <option value="contacted">Contacted</option>
          <option value="qualified">Qualified</option>
          <option value="proposal">Proposal</option>
          <option value="negotiation">Negotiation</option>
          <option value="won">Won</option>
          <option value="lost">Lost</option>
        </select>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Contact</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Stage</th>
                <th className="px-4 py-3 text-right">Value</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Next action</th>
              </tr>
            </thead>
            <tbody>
              {leads.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No leads yet.
                  </td>
                </tr>
              ) : (
                leads.map((ld) => (
                  <tr
                    key={ld.id}
                    className="border-t border-brand-brown-50"
                  >
                    <td className="px-4 py-3 font-medium">
                      {ld.contact_name ?? `Lead #${ld.id}`}
                      {ld.contact_phone && (
                        <div className="text-xs text-brand-brown-light">
                          {ld.contact_phone}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 capitalize">
                      {ld.source.replace("_", " ")}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2 py-1 text-xs ${STAGE_COLOR[ld.stage]}`}
                      >
                        {ld.stage}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      ₹
                      {Number(ld.expected_value).toLocaleString("en-IN")}
                    </td>
                    <td className="px-4 py-3">{ld.score}</td>
                    <td className="px-4 py-3 text-xs text-brand-brown-light">
                      {ld.next_action ?? "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
