import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  FileText,
  Image as ImageIcon,
  PenLine,
  RefreshCcw,
  Search,
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
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { verificationApi } from "@/lib/api/verification";
import { fmtIst } from "@/lib/datetime";

const PAGE_SIZE = 6;
const TYPES = [
  "address",
  "employment",
  "document",
  "business",
  "education",
  "criminal",
  "bank",
  "other",
];

function isImageUrl(u: string): boolean {
  return /\.(jpe?g|png|gif|webp|heic|bmp)(\?|#|$)/i.test(u);
}
function isPdfUrl(u: string): boolean {
  return /\.pdf(\?|#|$)/i.test(u);
}
function looksLikeUrl(v: unknown): v is string {
  return (
    typeof v === "string" &&
    (v.startsWith("http://") || v.startsWith("https://") || v.startsWith("/"))
  );
}

interface FileEntry {
  url: string;
  label: string;
  kind: "image" | "pdf" | "link";
}

function collectFiles(v: any): FileEntry[] {
  const out: FileEntry[] = [];
  (v.photos as string[] | null | undefined)?.forEach((u, i) => {
    if (!u) return;
    out.push({
      url: u,
      label: `Photo ${i + 1}`,
      kind: isPdfUrl(u) ? "pdf" : "image",
    });
  });
  if (v.signature_url) {
    out.push({
      url: v.signature_url,
      label: "Signature",
      kind: isImageUrl(v.signature_url) ? "image" : "link",
    });
  }
  if (v.form_data && typeof v.form_data === "object") {
    for (const [k, val] of Object.entries(v.form_data)) {
      if (looksLikeUrl(val)) {
        out.push({
          url: val,
          label: k,
          kind: isImageUrl(val) ? "image" : isPdfUrl(val) ? "pdf" : "link",
        });
      }
    }
  }
  return out;
}

export default function VerificationAuditPage() {
  const qc = useQueryClient();
  const [comments, setComments] = useState<Record<number, string>>({});
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [fraudOnly, setFraudOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [lightbox, setLightbox] = useState<FileEntry | null>(null);

  const { data: list = [], isLoading } = useQuery({
    queryKey: ["verification-audit-queue", search, typeFilter, fraudOnly],
    queryFn: () =>
      verificationApi.auditQueue({
        search: search || undefined,
        type: typeFilter || undefined,
        fraud_only: fraudOnly || undefined,
      }),
  });

  const pageCount = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
  const pageRows = list.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const decide = useMutation({
    mutationFn: ({
      id,
      action,
    }: {
      id: number;
      action: "approved" | "rejected" | "rework";
    }) => verificationApi.audit(id, action, comments[id]),
    onSuccess: () => {
      toast.success("Decision recorded");
      qc.invalidateQueries({ queryKey: ["verification-audit-queue"] });
      qc.invalidateQueries({ queryKey: ["verifications"] });
    },
    onError: () => toast.error("Could not save decision"),
  });

  if (isLoading) return <LoadingScreen label="Loading audit queue…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Verification Audit Queue
        </h1>
        <p className="text-sm text-brand-brown-light">
          {list.length} submission{list.length === 1 ? "" : "s"} awaiting QA review.
        </p>
      </div>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-4">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search ticket / subject / phone / address…"
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
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={fraudOnly}
              onChange={(e) => {
                setFraudOnly(e.target.checked);
                setPage(1);
              }}
            />
            Fraud-flagged only
          </label>
        </CardContent>
      </Card>

      {pageRows.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-brand-brown-light">
            {list.length === 0
              ? "Nothing to audit. Newly submitted verifications appear here."
              : "No results match these filters."}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {pageRows.map((v) => (
            <Card key={v.id}>
              <CardHeader className="flex flex-row items-start justify-between gap-4">
                <div>
                  <CardTitle className="font-mono text-base">
                    {v.ticket_number}
                  </CardTitle>
                  <CardDescription>
                    {v.subject_name} · {v.type}
                  </CardDescription>
                </div>
                {v.fraud_flags.length > 0 && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-error/15 px-3 py-1 text-xs text-error">
                    <AlertTriangle className="size-3" />
                    {v.fraud_flags.length} fraud flag
                    {v.fraud_flags.length === 1 ? "" : "s"}
                  </span>
                )}
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-brand-brown-light">Address: </span>
                    {v.address ?? "—"}
                  </div>
                  <div>
                    <span className="text-brand-brown-light">Phone: </span>
                    {v.contact_phone ?? "—"}
                  </div>
                  <div>
                    <span className="text-brand-brown-light">Result: </span>
                    <span className="capitalize">
                      {v.result?.replace("_", " ") ?? "—"}
                    </span>
                  </div>
                  <div>
                    <span className="text-brand-brown-light">Submitted: </span>
                    {v.submitted_at
                      ? fmtIst(v.submitted_at)
                      : "—"}
                  </div>
                </div>

                {v.form_data && (
                  <div className="rounded-md border border-brand-brown-50 bg-cream p-3 text-sm">
                    <div className="text-xs font-semibold uppercase text-brand-gold-dark mb-2">
                      Findings
                    </div>
                    <dl className="grid grid-cols-2 gap-2">
                      {Object.entries(v.form_data)
                        .filter(([, val]) => !looksLikeUrl(val))
                        .map(([k, val]) => (
                          <div key={k}>
                            <dt className="text-xs text-brand-brown-light">
                              {k}
                            </dt>
                            <dd>{String(val)}</dd>
                          </div>
                        ))}
                    </dl>
                  </div>
                )}

                <FilesPanel
                  files={collectFiles(v)}
                  reportUrl={
                    v.status === "completed" || v.status === "audit_pending"
                      ? verificationApi.reportUrl(v.id)
                      : null
                  }
                  onPreview={setLightbox}
                />

                {v.remarks && (
                  <div className="text-sm">
                    <span className="text-brand-brown-light">Remarks: </span>
                    {v.remarks}
                  </div>
                )}

                {v.fraud_flags.length > 0 && (
                  <div className="rounded-md border border-error/30 bg-error/5 p-3 text-xs space-y-1">
                    {v.fraud_flags.map((f) => (
                      <div key={f.id}>
                        <span className="font-semibold">{f.flag_type}</span> ·{" "}
                        {f.severity} · {f.detected_by}
                        {f.notes && ` — ${f.notes}`}
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center">
                  <Input
                    placeholder="Audit comments…"
                    value={comments[v.id] ?? ""}
                    onChange={(e) =>
                      setComments({ ...comments, [v.id]: e.target.value })
                    }
                    className="flex-1"
                  />
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1"
                      disabled={decide.isPending}
                      onClick={() =>
                        decide.mutate({ id: v.id, action: "rework" })
                      }
                    >
                      <RefreshCcw className="size-4" />
                      Rework
                    </Button>
                    <Button
                      variant="destructive"
                      size="sm"
                      className="gap-1"
                      disabled={decide.isPending}
                      onClick={() =>
                        decide.mutate({ id: v.id, action: "rejected" })
                      }
                    >
                      <XCircle className="size-4" />
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      className="gap-1"
                      disabled={decide.isPending}
                      onClick={() =>
                        decide.mutate({ id: v.id, action: "approved" })
                      }
                    >
                      <CheckCircle2 className="size-4" />
                      Approve
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
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

      {lightbox && (
        <Lightbox file={lightbox} onClose={() => setLightbox(null)} />
      )}
    </div>
  );
}

function FilesPanel({
  files,
  reportUrl,
  onPreview,
}: {
  files: FileEntry[];
  reportUrl: string | null;
  onPreview: (f: FileEntry) => void;
}) {
  if (files.length === 0 && !reportUrl) {
    return (
      <div className="rounded-md border border-brand-brown-50 bg-cream p-3 text-xs text-brand-brown-light">
        No photos / signature / attachments uploaded by the rep.
      </div>
    );
  }
  return (
    <div className="rounded-md border border-brand-brown-50 bg-cream p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="text-xs font-semibold uppercase text-brand-gold-dark">
          Files ({files.length})
        </div>
        {reportUrl && (
          <a
            href={reportUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs text-brand-gold-dark hover:underline"
          >
            <FileText className="size-3" /> Generated report PDF
          </a>
        )}
      </div>
      {files.length > 0 && (
        <div className="grid gap-2 sm:grid-cols-3 md:grid-cols-4">
          {files.map((f, i) => (
            <FileTile
              key={`${f.url}-${i}`}
              file={f}
              onPreview={() => onPreview(f)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function FileTile({
  file,
  onPreview,
}: {
  file: FileEntry;
  onPreview: () => void;
}) {
  const isSignature = file.label.toLowerCase().includes("signature");
  return (
    <button
      type="button"
      onClick={onPreview}
      className="group text-left rounded-md border border-brand-brown-50 bg-white overflow-hidden hover:border-brand-gold-dark transition"
    >
      <div className="aspect-square bg-brand-brown-50/50 flex items-center justify-center overflow-hidden">
        {file.kind === "image" ? (
          <img
            src={file.url}
            alt={file.label}
            loading="lazy"
            className="w-full h-full object-cover group-hover:scale-105 transition"
          />
        ) : file.kind === "pdf" ? (
          <FileText className="size-10 text-brand-gold-dark" />
        ) : isSignature ? (
          <PenLine className="size-10 text-brand-gold-dark" />
        ) : (
          <ImageIcon className="size-10 text-brand-gold-dark" />
        )}
      </div>
      <div className="p-2 flex items-center justify-between gap-2">
        <div className="text-xs font-medium truncate" title={file.label}>
          {file.label}
        </div>
        <a
          href={file.url}
          target="_blank"
          rel="noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-brand-brown-light hover:text-brand-gold-dark"
          title="Open in new tab"
        >
          <ExternalLink className="size-3" />
        </a>
      </div>
    </button>
  );
}

function Lightbox({
  file,
  onClose,
}: {
  file: FileEntry;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
      onClick={onClose}
    >
      <div
        className="max-w-5xl w-full max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-2 text-white">
          <div className="font-medium">{file.label}</div>
          <div className="flex items-center gap-3">
            <a
              href={file.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-xs hover:underline"
            >
              <ExternalLink className="size-3" /> Open in new tab
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
        <div className="flex-1 bg-black/40 rounded overflow-auto flex items-center justify-center">
          {file.kind === "image" ? (
            <img
              src={file.url}
              alt={file.label}
              className="max-w-full max-h-[80vh] object-contain"
            />
          ) : file.kind === "pdf" ? (
            <iframe
              src={file.url}
              title={file.label}
              className="w-full h-[80vh] bg-white"
            />
          ) : (
            <div className="p-12 text-white/80 text-center">
              No inline preview for this file type.
              <br />
              <a
                href={file.url}
                target="_blank"
                rel="noreferrer"
                className="text-brand-gold underline"
              >
                Open it in a new tab
              </a>
              .
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
