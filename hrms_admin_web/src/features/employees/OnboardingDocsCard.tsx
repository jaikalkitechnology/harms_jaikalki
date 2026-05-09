import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  CheckCircle2,
  CircleDashed,
  ExternalLink,
  ShieldCheck,
  Trash2,
  UploadCloud,
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
  documentsApi,
  type EmployeeDocType,
  type EmployeeDocument,
} from "@/lib/api/documents";

interface DocSpec {
  type: EmployeeDocType;
  label: string;
  required?: boolean;
}

interface DocSection {
  label: string;
  description: string;
  items: DocSpec[];
}

const SECTIONS: DocSection[] = [
  {
    label: "KYC / Identity",
    description:
      "Government-issued IDs and proof of address. PAN and Aadhaar are mandatory for payroll.",
    items: [
      { type: "aadhaar", label: "Aadhaar Card", required: true },
      { type: "pan", label: "PAN Card", required: true },
      { type: "photo", label: "Passport-size Photo", required: true },
      { type: "address_proof", label: "Address Proof" },
      { type: "passport", label: "Passport" },
      { type: "voter_id", label: "Voter ID" },
      { type: "driving_license", label: "Driving License" },
    ],
  },
  {
    label: "Banking",
    description:
      "Required for salary credit. Either passbook or cancelled cheque is enough.",
    items: [
      { type: "bank_passbook", label: "Bank Passbook", required: true },
      { type: "cancelled_cheque", label: "Cancelled Cheque" },
    ],
  },
  {
    label: "Education / Marksheets",
    description:
      "Upload the highest qualifications. Marksheets and degree certificates are accepted.",
    items: [
      { type: "ssc_marksheet", label: "SSC (Class 10) Marksheet" },
      { type: "hsc_marksheet", label: "HSC (Class 12) Marksheet" },
      { type: "graduation_marksheet", label: "Graduation Marksheet" },
      { type: "post_graduation_marksheet", label: "Post-Graduation Marksheet" },
      { type: "diploma_certificate", label: "Diploma Certificate" },
      { type: "professional_certificate", label: "Professional Certificate" },
    ],
  },
  {
    label: "Employment History",
    description:
      "Optional but recommended for experienced hires. Speeds up onboarding & exit checks.",
    items: [
      { type: "prev_offer_letter", label: "Previous Offer Letter" },
      { type: "prev_relieving_letter", label: "Relieving Letter" },
      { type: "prev_payslip", label: "Last 3 Payslips" },
      { type: "experience", label: "Experience Certificate" },
      { type: "form16", label: "Form 16 (current FY)" },
    ],
  },
];

const ACCEPT = ".pdf,application/pdf,image/jpeg,image/png,image/webp";

function fmtBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(2)} MB`;
}

export function OnboardingDocsCard({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const { data: documents = [] } = useQuery({
    queryKey: ["onboarding-docs", employeeId],
    queryFn: () => documentsApi.list(employeeId),
  });

  // Group documents by type so the row can show the latest upload.
  const byType = new Map<string, EmployeeDocument[]>();
  for (const d of documents) {
    const arr = byType.get(d.doc_type) ?? [];
    arr.push(d);
    byType.set(d.doc_type, arr);
  }

  const requiredTypes = SECTIONS.flatMap((s) =>
    s.items.filter((i) => i.required).map((i) => i.type as string),
  );
  const requiredUploaded = requiredTypes.filter((t) => byType.has(t)).length;
  const requiredTotal = requiredTypes.length;

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-brand-gold-dark" />
          Onboarding <span className="display-em">documents</span>
          <span className="ml-auto text-xs font-mono text-brand-brown-light">
            {requiredUploaded} / {requiredTotal} required
          </span>
        </CardTitle>
        <CardDescription>
          KYC, banking, marksheets and prior-employment papers. Files are
          stored encrypted; HR can mark each one verified after physical
          checks. PDF or image only, max 10 MB.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {SECTIONS.map((s) => (
          <div key={s.label}>
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-gold-dark mb-1">
              {s.label}
            </div>
            <div className="text-xs text-brand-brown-light mb-3">
              {s.description}
            </div>
            <div className="rounded-xl border border-brand-brown-100 divide-y divide-brand-brown-100/60">
              {s.items.map((spec) => (
                <DocRow
                  key={spec.type}
                  spec={spec}
                  uploads={byType.get(spec.type) ?? []}
                  employeeId={employeeId}
                  onChange={() =>
                    qc.invalidateQueries({
                      queryKey: ["onboarding-docs", employeeId],
                    })
                  }
                />
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function DocRow({
  spec,
  uploads,
  employeeId,
  onChange,
}: {
  spec: DocSpec;
  uploads: EmployeeDocument[];
  employeeId: number;
  onChange: () => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [busy, setBusy] = useState(false);
  const latest = uploads[0];

  const upload = useMutation({
    mutationFn: (file: File) =>
      documentsApi.upload(employeeId, spec.type, file),
    onSuccess: () => {
      toast.success(`${spec.label} uploaded`);
      onChange();
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Upload failed";
      toast.error(detail);
    },
  });

  const verify = useMutation({
    mutationFn: () => documentsApi.verify(latest.id),
    onSuccess: () => {
      toast.success("Marked verified");
      onChange();
    },
  });

  const remove = useMutation({
    mutationFn: () => documentsApi.remove(latest.id),
    onSuccess: () => {
      toast.success(`${spec.label} removed`);
      onChange();
    },
  });

  async function pick(f: File | undefined | null) {
    if (!f) return;
    if (f.size > 10 * 1024 * 1024) {
      toast.error("File too large (max 10 MB)");
      return;
    }
    setBusy(true);
    try {
      await upload.mutateAsync(f);
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="flex items-center justify-between gap-3 px-4 py-3">
      <div className="flex items-center gap-3 min-w-0">
        {latest ? (
          latest.verified ? (
            <CheckCircle2 className="h-5 w-5 text-success shrink-0" />
          ) : (
            <CheckCircle2 className="h-5 w-5 text-brand-gold-dark shrink-0" />
          )
        ) : (
          <CircleDashed className="h-5 w-5 text-brand-brown-light shrink-0" />
        )}
        <div className="min-w-0">
          <div className="text-sm font-medium text-brand-brown-darker flex items-center gap-2">
            {spec.label}
            {spec.required && (
              <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-error">
                required
              </span>
            )}
            {latest?.verified && (
              <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-success">
                verified
              </span>
            )}
          </div>
          {latest ? (
            <div className="text-xs text-brand-brown-light truncate">
              {latest.file_name} · {fmtBytes(latest.file_size)} ·{" "}
              {new Date(latest.created_at).toLocaleDateString()}
            </div>
          ) : (
            <div className="text-xs text-brand-brown-light">Not uploaded</div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        {latest && (
          <a
            href={latest.file_url}
            target="_blank"
            rel="noreferrer"
            className="text-[11px] font-mono uppercase tracking-[0.2em] text-brand-gold-dark hover:text-brand-brown-darker flex items-center gap-1"
          >
            <ExternalLink className="h-3.5 w-3.5" /> View
          </a>
        )}
        {latest && !latest.verified && (
          <Button
            size="sm"
            variant="outline"
            disabled={verify.isPending}
            onClick={() => verify.mutate()}
            className="h-8"
          >
            <ShieldCheck className="h-3.5 w-3.5" />
            Verify
          </Button>
        )}
        {latest && (
          <Button
            size="sm"
            variant="outline"
            disabled={remove.isPending}
            onClick={() => {
              if (confirm(`Remove ${spec.label}?`)) remove.mutate();
            }}
            className="h-8 text-destructive"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        )}
        <Button
          size="sm"
          variant={latest ? "outline" : "default"}
          disabled={busy || upload.isPending}
          onClick={() => inputRef.current?.click()}
          className="h-8"
        >
          <UploadCloud className="h-3.5 w-3.5" />
          {latest ? "Replace" : "Upload"}
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={(e) => pick(e.target.files?.[0])}
        />
      </div>
    </div>
  );
}
