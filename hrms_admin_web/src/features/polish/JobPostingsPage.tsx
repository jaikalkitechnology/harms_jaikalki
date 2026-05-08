import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ChevronLeft,
  ChevronRight,
  Pencil,
  Plus,
  Search,
  Smartphone,
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
import { polishApi, type JobPosting } from "@/lib/api/polish";
import { fmtIst } from "@/lib/datetime";

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

const PAGE_SIZE = 8;

const EMPLOYMENT_TYPES = ["full_time", "part_time", "contract", "intern"];

interface Draft {
  code: string;
  title: string;
  description: string;
  requirements: string;
  location: string;
  employment_type: string;
  referral_bonus: string;
  is_internal_only: boolean;
  closes_on: string;
}

const EMPTY_DRAFT: Draft = {
  code: "",
  title: "",
  description: "",
  requirements: "",
  location: "",
  employment_type: "full_time",
  referral_bonus: "",
  is_internal_only: true,
  closes_on: "",
};

export default function JobPostingsPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [appFilter, setAppFilter] = useState<"" | "true" | "false">("");
  const [page, setPage] = useState(1);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<JobPosting | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);

  const [selected, setSelected] = useState<JobPosting | null>(null);

  const { data: postings = [], isLoading } = useQuery({
    queryKey: ["job-postings", search, statusFilter, appFilter],
    queryFn: () =>
      polishApi.listPostings({
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        published_to_app:
          appFilter === "" ? undefined : appFilter === "true",
      }),
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
        code: draft.code,
        title: draft.title,
        description: draft.description || null,
        requirements: draft.requirements || null,
        location: draft.location || null,
        employment_type: draft.employment_type,
        referral_bonus: draft.referral_bonus
          ? Number(draft.referral_bonus)
          : null,
        is_internal_only: draft.is_internal_only,
        closes_on: draft.closes_on || null,
      }),
    onSuccess: () => {
      toast.success("Posted as draft");
      setEditorOpen(false);
      setDraft(EMPTY_DRAFT);
      qc.invalidateQueries({ queryKey: ["job-postings"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not post"),
  });

  const update = useMutation({
    mutationFn: () =>
      polishApi.updatePosting(editing!.id, {
        title: draft.title,
        description: draft.description || null,
        requirements: draft.requirements || null,
        location: draft.location || null,
        employment_type: draft.employment_type,
        referral_bonus: draft.referral_bonus
          ? Number(draft.referral_bonus)
          : null,
        is_internal_only: draft.is_internal_only,
        closes_on: draft.closes_on || null,
      }),
    onSuccess: () => {
      toast.success("Posting updated");
      setEditorOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["job-postings"] });
    },
    onError: () => toast.error("Could not update"),
  });

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      polishApi.setPostingStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job-postings"] }),
  });

  const setApp = useMutation({
    mutationFn: ({ id, on }: { id: number; on: boolean }) =>
      polishApi.updatePosting(id, { published_to_app: on }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["job-postings"] });
    },
    onError: () => toast.error("Could not toggle app visibility"),
  });

  const setAppStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      polishApi.setApplicationStatus(id, status),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["job-applications"] }),
  });

  const openCreate = () => {
    setEditing(null);
    setDraft(EMPTY_DRAFT);
    setEditorOpen(true);
  };
  const openEdit = (p: JobPosting) => {
    setEditing(p);
    setDraft({
      code: p.code,
      title: p.title,
      description: p.description ?? "",
      requirements: p.requirements ?? "",
      location: p.location ?? "",
      employment_type: p.employment_type,
      referral_bonus: p.referral_bonus ?? "",
      is_internal_only: p.is_internal_only,
      closes_on: p.closes_on ?? "",
    });
    setEditorOpen(true);
  };

  const pageCount = Math.max(1, Math.ceil(postings.length / PAGE_SIZE));
  const pageRows = postings.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (isLoading) return <LoadingScreen label="Loading postings…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Internal Job Postings
          </h1>
          <p className="text-sm text-brand-brown-light">
            {postings.length} posting{postings.length === 1 ? "" : "s"} match
            current filters · referral bonuses paid on hire.
          </p>
        </div>
        <Button onClick={openCreate} className="gap-2">
          <Plus className="size-4" /> New posting
        </Button>
      </div>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-3">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search code / title / location / description…"
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
                {s}
              </option>
            ))}
          </select>
          <select
            value={appFilter}
            onChange={(e) => {
              setAppFilter(e.target.value as "" | "true" | "false");
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm md:col-span-3"
          >
            <option value="">All postings</option>
            <option value="true">Visible in mobile app</option>
            <option value="false">Hidden from mobile app</option>
          </select>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {pageRows.length === 0 ? (
          <Card className="md:col-span-2">
            <CardContent className="py-10 text-center text-brand-brown-light">
              No postings match these filters.
            </CardContent>
          </Card>
        ) : (
          pageRows.map((p) => (
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
                  {p.location && ` · ${p.location}`}
                  {p.referral_bonus && (
                    <>
                      {" · "}₹
                      {Number(p.referral_bonus).toLocaleString("en-IN")} referral
                    </>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {p.description && (
                  <p className="text-brand-brown-light line-clamp-3">
                    {p.description}
                  </p>
                )}

                {/* Publish-to-app switch */}
                <label className="flex items-center justify-between rounded border border-brand-brown-50 px-3 py-2 cursor-pointer">
                  <span className="inline-flex items-center gap-2 text-xs">
                    <Smartphone className="size-4 text-brand-gold-dark" />
                    Visible in mobile app
                  </span>
                  <span
                    className={`relative inline-flex h-5 w-10 items-center rounded-full transition ${p.published_to_app ? "bg-success" : "bg-brand-brown-50"}`}
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={p.published_to_app}
                      onChange={(e) =>
                        setApp.mutate({ id: p.id, on: e.target.checked })
                      }
                    />
                    <span
                      className={`inline-block size-4 rounded-full bg-white transition ${p.published_to_app ? "translate-x-5" : "translate-x-1"}`}
                    />
                  </span>
                </label>

                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openEdit(p)}
                  >
                    <Pencil className="size-3" /> Edit
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setSelected(selected?.id === p.id ? null : p)}
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
          ))
        )}
      </div>

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

      {selected && (
        <Card>
          <CardHeader>
            <CardTitle>Applications · {selected.title}</CardTitle>
            <CardDescription>
              {applications.length} applicant
              {applications.length === 1 ? "" : "s"}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0 overflow-x-auto">
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
                        {fmtIst(a.submitted_at)}
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

      {editorOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card className="w-full max-w-3xl max-h-[92vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>
                  {editing ? "Edit posting" : "New posting"}
                </CardTitle>
                <CardDescription>
                  Saved as draft. Publish from the list, then flip the "Visible
                  in mobile app" switch to surface it inside the employee app.
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setEditorOpen(false);
                  setEditing(null);
                }}
              >
                <X className="size-4" />
              </Button>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Code *</Label>
                <Input
                  value={draft.code}
                  disabled={!!editing}
                  onChange={(e) => setDraft({ ...draft, code: e.target.value })}
                />
              </div>
              <div>
                <Label>Title *</Label>
                <Input
                  value={draft.title}
                  onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                />
              </div>
              <div>
                <Label>Location</Label>
                <Input
                  value={draft.location}
                  onChange={(e) =>
                    setDraft({ ...draft, location: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>Employment type</Label>
                <select
                  value={draft.employment_type}
                  onChange={(e) =>
                    setDraft({ ...draft, employment_type: e.target.value })
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {EMPLOYMENT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <Label>Description</Label>
                <textarea
                  value={draft.description}
                  rows={3}
                  onChange={(e) =>
                    setDraft({ ...draft, description: e.target.value })
                  }
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div className="md:col-span-2">
                <Label>Requirements</Label>
                <textarea
                  value={draft.requirements}
                  rows={3}
                  onChange={(e) =>
                    setDraft({ ...draft, requirements: e.target.value })
                  }
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div>
                <Label>Referral bonus (₹)</Label>
                <Input
                  type="number"
                  value={draft.referral_bonus}
                  onChange={(e) =>
                    setDraft({ ...draft, referral_bonus: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>Closes on</Label>
                <Input
                  type="date"
                  value={draft.closes_on}
                  onChange={(e) =>
                    setDraft({ ...draft, closes_on: e.target.value })
                  }
                />
              </div>
              <label className="flex items-center gap-2 text-sm md:col-span-2">
                <input
                  type="checkbox"
                  checked={draft.is_internal_only}
                  onChange={(e) =>
                    setDraft({ ...draft, is_internal_only: e.target.checked })
                  }
                />
                Internal employees only
              </label>
              <div className="md:col-span-2 flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditorOpen(false);
                    setEditing(null);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  disabled={
                    create.isPending ||
                    update.isPending ||
                    !draft.title ||
                    (!editing && !draft.code)
                  }
                  onClick={() => (editing ? update.mutate() : create.mutate())}
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
