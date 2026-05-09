import { useRef, useState } from "react";
import { toast } from "sonner";
import {
  AlertTriangle,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  UploadCloud,
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
import {
  attendanceApi,
  type AttendanceUploadResult,
} from "@/lib/api/attendance";

const ACCEPTED = ".csv,.xls,.xlsx,text/csv";

export default function AttendanceUploadPage() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AttendanceUploadResult | null>(null);
  const [dragOver, setDragOver] = useState(false);

  function pick(f: File | undefined | null) {
    if (!f) return;
    if (f.size > 10 * 1024 * 1024) {
      toast.error("File too large (max 10 MB)");
      return;
    }
    setFile(f);
    setResult(null);
  }

  async function submit() {
    if (!file) return;
    setBusy(true);
    try {
      const r = await attendanceApi.upload(file);
      setResult(r);
      const ok = r.rows_imported + r.rows_updated;
      if (ok > 0) {
        toast.success(
          `${ok} row${ok === 1 ? "" : "s"} processed (${r.rows_imported} new, ${r.rows_updated} updated)`,
        );
      }
      if (r.errors.length > 0) {
        toast.warning(
          `${r.errors.length} row${r.errors.length === 1 ? "" : "s"} skipped — see error list below`,
        );
      }
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Upload failed";
      toast.error(detail);
    } finally {
      setBusy(false);
    }
  }

  function clear() {
    setFile(null);
    setResult(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Bulk import
        </div>
        <h1 className="font-display text-3xl font-bold text-brand-brown-darker">
          Upload <span className="display-em">attendance</span>
        </h1>
        <p className="mt-1 text-sm text-brand-brown-light">
          Drop a CSV (or Excel) file of attendance rows. Existing
          (employee, date) pairs are updated in place.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Expected format</CardTitle>
          <CardDescription>
            Required columns: <code>employee_code</code>, <code>date</code>.
            Optional: <code>status</code>, <code>check_in</code>,
            {" "}<code>check_out</code>, <code>work_mode</code>,{" "}
            <code>notes</code>.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md border border-brand-brown-100 bg-brand-brown-50/40 p-3 text-xs font-mono text-brand-brown-darker overflow-x-auto">
            <pre>{`employee_code,date,status,check_in,check_out,work_mode,notes
JKT001,2026-05-01,present,09:30,18:15,office,
JKT001,2026-05-02,half_day,10:30,15:00,office,Late grace
JKT002,2026-05-01,wfh,09:45,18:30,wfh,Working from home`}</pre>
          </div>
          <ul className="text-xs text-brand-brown-light space-y-1 list-disc pl-5">
            <li>
              <code>date</code> accepts <code>YYYY-MM-DD</code>,{" "}
              <code>DD/MM/YYYY</code>, or <code>DD-MM-YYYY</code>.
            </li>
            <li>
              <code>check_in</code> / <code>check_out</code> accept{" "}
              <code>HH:MM</code> (combined with the row's date) or a full
              ISO timestamp.
            </li>
            <li>
              <code>status</code> ∈ {`{present, absent, half_day, wfh, leave, holiday}`}.
              Defaults to <code>present</code> when a check-in time is set,
              else <code>absent</code>.
            </li>
            <li>
              Existing rows for the same (employee, date) are{" "}
              <strong>updated</strong>, not duplicated.
            </li>
          </ul>
          <div>
            <Button asChild variant="outline" size="sm" className="gap-2">
              <a href={attendanceApi.uploadTemplateUrl()} download>
                <Download className="h-4 w-4" />
                Download template
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Upload file</CardTitle>
          <CardDescription>
            CSV preferred. Excel (.xlsx) supported when{" "}
            <code>openpyxl</code> is installed on the server.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!file && (
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                pick(e.dataTransfer.files?.[0]);
              }}
              className={`w-full rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors ${
                dragOver
                  ? "border-brand-gold-dark bg-brand-gold/10"
                  : "border-brand-brown-100 bg-card hover:border-brand-gold-dark/60"
              }`}
            >
              <UploadCloud className="h-10 w-10 mx-auto text-brand-gold-dark" />
              <div className="mt-3 text-sm font-medium text-brand-brown-darker">
                Drop your file here, or click to browse
              </div>
              <div className="mt-1 text-xs text-brand-brown-light">
                CSV, XLS, or XLSX · max 10 MB
              </div>
            </button>
          )}
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED}
            className="hidden"
            onChange={(e) => pick(e.target.files?.[0])}
          />

          {file && (
            <div className="rounded-xl border border-brand-brown-100 p-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-3 min-w-0">
                <FileSpreadsheet className="h-6 w-6 text-brand-gold-dark shrink-0" />
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">
                    {file.name}
                  </div>
                  <div className="text-xs text-brand-brown-light">
                    {(file.size / 1024).toFixed(1)} KB
                  </div>
                </div>
              </div>
              <div className="flex gap-2 shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clear}
                  disabled={busy}
                >
                  <X className="h-4 w-4" /> Remove
                </Button>
                <Button onClick={submit} disabled={busy}>
                  {busy ? "Uploading…" : "Upload"}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-success" />
              Import summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <Stat label="Total rows" value={result.rows_total} />
              <Stat
                label="New"
                value={result.rows_imported}
                tone="success"
              />
              <Stat
                label="Updated"
                value={result.rows_updated}
                tone="info"
              />
              <Stat
                label="Skipped"
                value={result.rows_skipped}
                tone={result.rows_skipped > 0 ? "error" : "muted"}
              />
            </div>

            {result.errors.length > 0 && (
              <div>
                <div className="flex items-center gap-2 text-sm font-medium text-error mb-2">
                  <AlertTriangle className="h-4 w-4" />
                  {result.errors.length} row
                  {result.errors.length === 1 ? "" : "s"} skipped
                </div>
                <div className="rounded-xl border border-brand-brown-100 overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-brand-brown-50/60">
                      <tr>
                        {["Row", "Employee", "Date", "Error"].map((h) => (
                          <th
                            key={h}
                            className="text-left px-3 py-2 text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light"
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.errors.map((e, i) => (
                        <tr
                          key={i}
                          className="border-t border-brand-brown-100/60"
                        >
                          <td className="px-3 py-2 font-mono text-xs">
                            {e.row}
                          </td>
                          <td className="px-3 py-2 font-mono text-xs">
                            {e.employee_code ?? "—"}
                          </td>
                          <td className="px-3 py-2 font-mono text-xs">
                            {e.date ?? "—"}
                          </td>
                          <td className="px-3 py-2 text-error text-xs">
                            {e.error}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  tone = "muted",
}: {
  label: string;
  value: number;
  tone?: "muted" | "success" | "info" | "error";
}) {
  const toneClass =
    tone === "success"
      ? "text-success"
      : tone === "info"
        ? "text-info"
        : tone === "error"
          ? "text-error"
          : "text-brand-brown-darker";
  return (
    <div className="rounded-md border border-brand-brown-100 p-3">
      <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
        {label}
      </div>
      <div className={`text-2xl font-semibold ${toneClass}`}>{value}</div>
    </div>
  );
}
