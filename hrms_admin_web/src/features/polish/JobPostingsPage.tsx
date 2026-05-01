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
import { polishApi, type JobPosting } from "@/lib/api/polish";

const STATUS_COLOR: Record<string, string> = {
  draft: "bg-brand-brown-50 text-brand-brown-darker",
  published: "bg-success/15 text-success",
  closed: "bg-error/15 text-error",
  filled: "bg-info/15 text-info",
};

const NEXT_STATUS: Record<string, string[]> = {
  draft: ["published", "closed"],
  published: ["closed", "filled"],
  closed: ["published"],
  filled: [],
};

export default function JobPostingsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [bonus, setBonus] = useState("");
  const [selected, setSelected] = useState<JobPosting | null>(null);

  const { data: postings = [], isLoading } = useQuery({
    queryKey: ["job-postings"],
    queryFn: () => polishApi.listPostings(),
  });
  const { data: applications = [] } = useQuery({
    queryKey: ["job-applications", selected?.id],
    queryFn: () =>
      selected ? polishApi.applicationsForPosting(selected.id) : [],
    enabled: !!selected,
  });

  const create = useMutation({
    mutationFn: () =>
      polishApi.createPosting({
        code,
        title,
        description: description || null,
        referral_bonus: bonus ? Number(bonus) : null,
        employment_type: "full_time",
        is_internal_only: true,
      }),
    onSuccess: () => {
      toast.success("Posted");
      setShowForm(false);
      setCode("");
      setTitle("");
      setDescription("");
      setBonus("");
      qc.invalidateQueries({ queryKey: ["job-postings"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Could not post"),
  });

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      polishApi.setPostingStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["job-postings"] });
    },
  });

  const setAppStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      polishApi.setApplicationStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["job-applications"] });
    },
  });

  if (isLoading) return <LoadingScreen label="Loading postings…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Internal Job Postings
          </h1>
          <p className="text-sm text-brand-brown-light">
            {postings.length} posting{postings.length === 1 ? "" : "s"} ·
            referral bonuses paid on hire.
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
          <Plus className="size-4" />
          {showForm ? "Cancel" : "New posting"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create posting</CardTitle>
            <CardDescription>
              Saved as draft — publish from the list to open applications.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Code *</Label>
              <Input value={code} onChange={(e) => setCode(e.target.value)} />
            </div>
            <div>
              <Label>Title *</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="md:col-span-2">
              <Label>Description</Label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div>
              <Label>Referral bonus (₹)</Label>
              <Input
                type="number"
                value={bonus}
                onChange={(e) => setBonus(e.target.value)}
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                disabled={!code || !title || create.isPending}
                onClick={() => create.mutate()}
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {postings.map((p) => (
          <Card
            key={p.id}
            className={selected?.id === p.id ? "border-brand-gold-dark" : ""}
          >
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-base">{p.title}</CardTitle>
                <span
                  className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${STATUS_COLOR[p.status] ?? ""}`}
                >
                  {p.status}
                </span>
              </div>
              <CardDescription className="font-mono text-xs">
                {p.code} · {p.employment_type}
                {p.referral_bonus && (
                  <>
                    {" · "}₹{Number(p.referral_bonus).toLocaleString("en-IN")}{" "}
                    referral bonus
                  </>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {p.description && (
                <p className="text-brand-brown-light">{p.description}</p>
              )}
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    setSelected(selected?.id === p.id ? null : p)
                  }
                >
                  {selected?.id === p.id ? "Hide" : "View"} applications
                </Button>
                {(NEXT_STATUS[p.status] ?? []).map((next) => (
                  <Button
                    key={next}
                    size="sm"
                    variant={next === "closed" ? "destructive" : "outline"}
                    onClick={() =>
                      setStatus.mutate({ id: p.id, status: next })
                    }
                  >
                    {next}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {selected && (
        <Card>
          <CardHeader>
            <CardTitle>Applications · {selected.title}</CardTitle>
            <CardDescription>
              {applications.length} applicant
              {applications.length === 1 ? "" : "s"}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead className="bg-brand-brown-50/40 text-left">
                <tr>
                  <th className="px-4 py-3">Applicant</th>
                  <th className="px-4 py-3">Referrer</th>
                  <th className="px-4 py-3">Submitted</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {applications.length === 0 ? (
                  <tr>
                    <td
                      colSpan={5}
                      className="px-4 py-10 text-center text-brand-brown-light"
                    >
                      No applications yet.
                    </td>
                  </tr>
                ) : (
                  applications.map((a) => (
                    <tr key={a.id} className="border-t border-brand-brown-50">
                      <td className="px-4 py-3">
                        {a.applicant_employee_id
                          ? `Employee #${a.applicant_employee_id}`
                          : a.external_applicant_name ?? "External"}
                      </td>
                      <td className="px-4 py-3">
                        {a.referrer_employee_id
                          ? `#${a.referrer_employee_id}`
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {new Date(a.submitted_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 capitalize">
                        {a.status.replaceAll("_", " ")}
                      </td>
                      <td className="px-4 py-3">
                        <select
                          value={a.status}
                          onChange={(e) =>
                            setAppStatus.mutate({
                              id: a.id,
                              status: e.target.value,
                            })
                          }
                          className="h-8 rounded-md border border-input bg-background px-2 text-xs"
                        >
                          {[
                            "submitted",
                            "shortlisted",
                            "interviewing",
                            "offered",
                            "hired",
                            "rejected",
                            "withdrawn",
                          ].map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
