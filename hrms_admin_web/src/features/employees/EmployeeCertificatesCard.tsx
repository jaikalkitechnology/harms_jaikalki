// Certificates for one employee — create one (rendered as a PDF, e.g. an
// appreciation certificate) or upload a ready-made one. The employee
// downloads them from More → Certificates in the app.
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Award, Sparkles, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { EmployeeDetail } from "@/lib/api/employees";
import { examApi, type Certificate, type CertificateType } from "@/lib/api/exam";
import { Modal } from "@/features/polish/assets/AssetDialogs";
import {
  Chip,
  EmptyState,
  Field,
  FormActions,
  SELECT_CLASS,
  SectionCard,
  errDetail,
  fmtDate,
  todayIso,
  useCanEdit,
} from "./profile/ui";

const TYPES: { value: CertificateType; label: string; title: string }[] = [
  { value: "appreciation", label: "Appreciation", title: "Certificate of Appreciation" },
  { value: "achievement", label: "Achievement", title: "Certificate of Achievement" },
  { value: "excellence", label: "Excellence", title: "Certificate of Excellence" },
  { value: "completion", label: "Completion", title: "Certificate of Completion" },
  { value: "participation", label: "Participation", title: "Certificate of Participation" },
  { value: "training", label: "Training", title: "Training Certificate" },
  { value: "custom", label: "Custom", title: "" },
];
const typeLabel = (t: string | null) => TYPES.find((x) => x.value === (t ?? "achievement"))?.label ?? t;

export function EmployeeCertificatesCard({ employee }: { employee: EmployeeDetail }) {
  const canEdit = useCanEdit();
  const [dialog, setDialog] = useState<"create" | "upload" | null>(null);
  const { data: certs = [], isLoading } = useQuery({
    queryKey: ["employee-certificates", employee.id],
    queryFn: () => examApi.listCertificates({ employee_id: employee.id, limit: 200 }),
  });

  return (
    <SectionCard
      title="Certificates"
      description="Appreciation, achievement and training certificates. The employee downloads them from More → Certificates in the app."
      action={
        canEdit && (
          <>
            <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setDialog("upload")}>
              <Upload className="size-3.5" /> Upload
            </Button>
            <Button size="sm" className="gap-1.5" onClick={() => setDialog("create")}>
              <Sparkles className="size-3.5" /> Create certificate
            </Button>
          </>
        )
      }
    >
      {isLoading ? (
        <p className="text-sm text-brand-brown-light">Loading…</p>
      ) : certs.length === 0 ? (
        <EmptyState
          message="No certificates yet."
          actionLabel="Create certificate"
          onAction={() => setDialog("create")}
        />
      ) : (
        <ul className="divide-y divide-brand-brown-50">
          {certs.map((c) => (
            <CertificateRow key={c.id} cert={c} />
          ))}
        </ul>
      )}
      {dialog && (
        <CertificateModal
          mode={dialog}
          employee={employee}
          onClose={() => setDialog(null)}
        />
      )}
    </SectionCard>
  );
}

function CertificateRow({ cert: c }: { cert: Certificate }) {
  return (
    <li className="flex flex-wrap items-center gap-3 py-3">
      <div className="grid size-9 shrink-0 place-items-center rounded-lg bg-brand-gold/15 text-brand-gold-dark">
        <Award className="size-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-brand-brown-darker">{c.title}</span>
          <Chip tone="gold">{typeLabel(c.certificate_type)}</Chip>
          {c.file_name && <Chip>Uploaded</Chip>}
          {c.is_revoked && <Chip tone="error">Revoked</Chip>}
        </div>
        <div className="mt-0.5 font-mono text-xs text-brand-brown-light">
          {c.certificate_number} · {fmtDate(c.issued_date)}
        </div>
      </div>
      <Button asChild variant="outline" size="sm">
        <a href={examApi.certificatePdfUrl(c.id)} target="_blank" rel="noreferrer">
          Open
        </a>
      </Button>
    </li>
  );
}

function CertificateModal({
  mode,
  employee,
  onClose,
}: {
  mode: "create" | "upload";
  employee: EmployeeDetail;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [type, setType] = useState<CertificateType>("appreciation");
  const [title, setTitle] = useState(TYPES[0].title);
  const [titleTouched, setTitleTouched] = useState(false);
  const [body, setBody] = useState("");
  const [issued, setIssued] = useState(todayIso());
  const [file, setFile] = useState<File | null>(null);

  const save = useMutation({
    mutationFn: () =>
      mode === "upload"
        ? examApi.uploadCertificate(
            {
              employee_id: employee.id,
              title: title.trim(),
              certificate_type: type,
              issued_date: issued,
            },
            file!,
          )
        : examApi.issueCertificate({
            employee_id: employee.id,
            title: title.trim(),
            certificate_type: type,
            body_text: body.trim() || null,
            issued_date: issued,
          }),
    onSuccess: (c) => {
      toast.success(`${c.title} given to ${employee.first_name}`, {
        action: {
          label: "Open",
          onClick: () => window.open(examApi.certificatePdfUrl(c.id), "_blank", "noopener"),
        },
      });
      qc.invalidateQueries({ queryKey: ["employee-certificates", employee.id] });
      qc.invalidateQueries({ queryKey: ["certificates"] });
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not save the certificate")),
  });

  return (
    <Modal
      title={mode === "upload" ? "Upload certificate" : "Create certificate"}
      description={
        mode === "upload"
          ? "A certificate designed elsewhere — PDF, JPG, PNG or WEBP, up to 10 MB."
          : `Generated as a PDF with ${employee.first_name}'s name and the company seal.`
      }
      onClose={onClose}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Type">
          <select
            className={SELECT_CLASS}
            value={type}
            onChange={(e) => {
              const t = e.target.value as CertificateType;
              setType(t);
              if (!titleTouched) setTitle(TYPES.find((x) => x.value === t)?.title ?? "");
            }}
          >
            {TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Issued on">
          <Input type="date" value={issued} onChange={(e) => setIssued(e.target.value)} />
        </Field>
        <Field label="Title" className="col-span-full">
          <Input
            value={title}
            maxLength={200}
            placeholder="e.g. Outstanding Customer Support"
            onChange={(e) => {
              setTitle(e.target.value);
              setTitleTouched(true);
            }}
          />
        </Field>
        {mode === "create" ? (
          <Field
            label="Message (optional)"
            className="col-span-full"
            help="Printed on the certificate. Leave blank for the standard wording."
          >
            <textarea
              className="flex w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
              rows={3}
              maxLength={1000}
              value={body}
              placeholder="e.g. In recognition of your dedication during the Q2 launch."
              onChange={(e) => setBody(e.target.value)}
            />
          </Field>
        ) : (
          <Field label="File" className="col-span-full">
            <Input
              type="file"
              accept="application/pdf,image/jpeg,image/png,image/webp"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </Field>
        )}
        <FormActions
          onCancel={onClose}
          onSave={() => save.mutate()}
          saving={save.isPending}
          disabled={title.trim().length < 2 || (mode === "upload" && !file)}
          saveLabel={mode === "upload" ? "Upload" : "Create"}
        />
      </div>
    </Modal>
  );
}
