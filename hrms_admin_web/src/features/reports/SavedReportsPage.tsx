import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  FileText,
  Lock,
  Pencil,
  Plus,
  Search,
  Share2,
  Trash2,
  Upload,
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
import { reportsApi, type SavedReport } from "@/lib/api/reports";

const TYPES = [
  "headcount",
  "attrition",
  "attendance",
  "payroll_cost",
  "compliance",
  "sales",
  "performance",
  "verification",
  "training",
  "custom",
];

const PAGE_SIZE = 12;

interface CreateDraft {
  code: string;
  name: string;
  description: string;
  report_type: string;
  is_shared: boolean;
}

interface EditDraft {
  name: string;
  description: string;
  report_type: string;
  is_shared: boolean;
}

const EMPTY_CREATE: CreateDraft = {
  code: "",
  name: "",
  description: "",
  report_type: "custom",
  is_shared: false,
};

function fmtBytes(n: number | null): string {
  if (!n) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export default function SavedReportsPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [page, setPage] = useState(1);

  const [createOpen, setCreateOpen] = useState(false);
  const [createDraft, setCreateDraft] = useState<CreateDraft>(EMPTY_CREATE);

  const [editing, setEditing] = useState<SavedReport | null>(null);
  const [editDraft, setEditDraft] = useState<EditDraft>({
    name: "",
    description: "",
    report_type: "custom",
    is_shared: false,
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadFor, setUploadFor] = useState<number | null>(null);

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["saved-reports", search, typeFilter],
    queryFn: () =>
      reportsApi.listSaved({
        search: search.trim() || undefined,
        report_type: typeFilter || undefined,
      }),
  });

  const create = useMutation({
    mutationFn: () =>
      reportsApi.createSaved({
        code: createDraft.code,
        name: createDraft.name,
        description: createDraft.description || null,
        report_type: createDraft.report_type,
        is_shared: createDraft.is_shared,
      }),
    onSuccess: () => {
      toast.success("Saved");
      setCreateOpen(false);
      setCreateDraft(EMPTY_CREATE);
      qc.invalidateQueries({ queryKey: ["saved-reports"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not save"),
  });

  const update = useMutation({
    mutationFn: () =>
      reportsApi.updateSaved(editing!.id, {
        name: editDraft.name,
        description: editDraft.description || null,
        report_type: editDraft.report_type,
        is_shared: editDraft.is_shared,
      }),
    onSuccess: () => {
      toast.success("Updated");
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["saved-reports"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not update"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => reportsApi.deleteSaved(id),
    onSuccess: () => {
      toast.success("Deleted");
      qc.invalidateQueries({ queryKey: ["saved-reports"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not delete"),
  });

  const upload = useMutation({
    mutationFn: ({ id, file }: { id: number; file: File }) =>
      reportsApi.uploadSavedFile(id, file),
    onSuccess: () => {
      toast.success("File attached");
      qc.invalidateQueries({ queryKey: ["saved-reports"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Upload failed"),
  });

  const onFileChosen = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || uploadFor == null) return;
    upload.mutate({ id: uploadFor, file });
    setUploadFor(null);
  };

  const triggerUpload = (id: number) => {
    setUploadFor(id);
    setTimeout(() => fileInputRef.current?.click(), 0);
  };

  const openEdit = (r: SavedReport) => {
    setEditing(r);
    setEditDraft({
      name: r.name,
      description: r.description ?? "",
      report_type: r.report_type,
      is_shared: r.is_shared,
    });
  };

  const pageCount = Math.max(1, Math.ceil(reports.length / PAGE_SIZE));
  const pageRows = reports.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (isLoading) return <LoadingScreen label="Loading saved reports…" />;

  return (
    <div className="space-y-6">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.zip,.csv,.xls,.xlsx,.png,.jpg,.jpeg"
        className="hidden"
        onChange={onFileChosen}
      />

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Saved Reports
          </h1>
          <p className="text-sm text-brand-brown-light">
            {reports.length} report{reports.length === 1 ? "" : "s"} match
            current filters. Attach PDFs, ZIPs or spreadsheets to share
            generated artefacts.
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} className="gap-2">
          <Plus className="size-4" /> New report
        </Button>
      </div>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-3">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search code / name / description…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All types</option>
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Sharing</th>
                <th className="px-4 py-3">Attachment</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No saved reports match these filters.
                  </td>
                </tr>
              ) : (
                pageRows.map((r) => (
                  <tr key={r.id} className="border-t border-brand-brown-50">
                    <td className="px-4 py-3 font-mono text-xs">{r.code}</td>
                    <td className="px-4 py-3">
                      {r.name}
                      {r.description && (
                        <div className="text-[11px] text-brand-brown-light line-clamp-1">
                          {r.description}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 capitalize">{r.report_type}</td>
                    <td className="px-4 py-3">
                      {r.is_shared ? (
                        <span className="inline-flex items-center gap-1 text-success text-xs">
                          <Share2 className="size-3" /> Shared
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-brand-brown-light text-xs">
                          <Lock className="size-3" /> Private
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {r.file_url ? (
                        <a
                          href={reportsApi.savedFileUrl(r.file_url)}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-brand-gold-dark hover:underline"
                        >
                          <FileText className="size-3" />
                          {r.file_name ?? "file"} ({fmtBytes(r.file_size)})
                        </a>
                      ) : (
                        <span className="text-brand-brown-light text-xs">
                          —
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right whitespace-nowrap">
                      <Button
                        size="sm"
                        variant="ghost"
                        title="Upload file"
                        onClick={() => triggerUpload(r.id)}
                      >
                        <Upload className="size-4" />
                      </Button>
                      {r.file_url && (
                        <a
                          href={reportsApi.savedFileUrl(r.file_url)}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center justify-center px-2 py-1 hover:bg-brand-brown-50/50 rounded"
                          title="Download"
                        >
                          <Download className="size-4" />
                        </a>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        title="Edit"
                        onClick={() => openEdit(r)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        title="Delete"
                        onClick={() => {
                          if (confirm(`Delete "${r.name}"?`))
                            remove.mutate(r.id);
                        }}
                      >
                        <Trash2 className="size-4 text-destructive" />
                      </Button>
                    </td>
                  </tr>
                ))
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

      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card className="w-full max-w-2xl">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Save a report</CardTitle>
                <CardDescription>
                  Pick a base report type. After saving, attach a generated
                  artefact (PDF / ZIP / XLSX / image) from the list.
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCreateOpen(false)}
              >
                <X className="size-4" />
              </Button>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Code *</Label>
                <Input
                  value={createDraft.code}
                  placeholder="RPT-XYZ"
                  onChange={(e) =>
                    setCreateDraft({ ...createDraft, code: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>Name *</Label>
                <Input
                  value={createDraft.name}
                  onChange={(e) =>
                    setCreateDraft({ ...createDraft, name: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>Type</Label>
                <select
                  value={createDraft.report_type}
                  onChange={(e) =>
                    setCreateDraft({
                      ...createDraft,
                      report_type: e.target.value,
                    })
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <label className="flex items-center gap-2 mt-7">
                <input
                  type="checkbox"
                  checked={createDraft.is_shared}
                  onChange={(e) =>
                    setCreateDraft({
                      ...createDraft,
                      is_shared: e.target.checked,
                    })
                  }
                />
                <span className="text-sm">Share with teammates</span>
              </label>
              <div className="md:col-span-2">
                <Label>Description</Label>
                <Input
                  value={createDraft.description}
                  onChange={(e) =>
                    setCreateDraft({
                      ...createDraft,
                      description: e.target.value,
                    })
                  }
                />
              </div>
              <div className="md:col-span-2 flex justify-end gap-2">
                <Button variant="outline" onClick={() => setCreateOpen(false)}>
                  Cancel
                </Button>
                <Button
                  disabled={
                    !createDraft.code ||
                    !createDraft.name ||
                    create.isPending
                  }
                  onClick={() => create.mutate()}
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
                <CardTitle>Edit report</CardTitle>
                <CardDescription className="font-mono text-xs">
                  {editing.code}
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
                <Label>Name</Label>
                <Input
                  value={editDraft.name}
                  onChange={(e) =>
                    setEditDraft({ ...editDraft, name: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>Type</Label>
                <select
                  value={editDraft.report_type}
                  onChange={(e) =>
                    setEditDraft({
                      ...editDraft,
                      report_type: e.target.value,
                    })
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <div className="md:col-span-2">
                <Label>Description</Label>
                <Input
                  value={editDraft.description}
                  onChange={(e) =>
                    setEditDraft({
                      ...editDraft,
                      description: e.target.value,
                    })
                  }
                />
              </div>
              <label className="flex items-center gap-2 md:col-span-2">
                <input
                  type="checkbox"
                  checked={editDraft.is_shared}
                  onChange={(e) =>
                    setEditDraft({
                      ...editDraft,
                      is_shared: e.target.checked,
                    })
                  }
                />
                <span className="text-sm">Share with teammates</span>
              </label>
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
