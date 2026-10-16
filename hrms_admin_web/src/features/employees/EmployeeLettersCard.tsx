// Letters on the employee's file — created from a template on the
// letterhead, or uploaded (e.g. a signed scan). Visible ones show in the
// employee's app under More → Documents.
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Eye, EyeOff, FilePlus2, FileText, Trash2, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { EmployeeDetail } from "@/lib/api/employees";
import {
  LETTER_TYPES,
  fmtBytes,
  hrDocumentsApi,
  letterTypeLabel,
  openBlob,
  type EmployeeLetter,
  type LetterType,
} from "@/lib/api/hrDocuments";
import { letterTemplatesApi, type LetterTemplate } from "@/lib/api/letterTemplates";
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

const ACCEPT = "application/pdf,image/jpeg,image/png,image/webp";

// Template category → letter type (templates use a slightly different set).
const CATEGORY_TYPE: Record<string, LetterType> = {
  offer: "offer",
  appointment: "appointment",
  confirmation: "confirmation",
  experience: "experience",
  increment: "increment",
  termination: "termination",
  warning: "warning",
};

function useLetters(employeeId: number) {
  return useQuery({
    queryKey: ["employee-letters", employeeId],
    queryFn: () => hrDocumentsApi.letters(employeeId),
  });
}

export function EmployeeLettersCard({ employee }: { employee: EmployeeDetail }) {
  const canEdit = useCanEdit();
  const { data: letters = [], isLoading } = useLetters(employee.id);
  const [dialog, setDialog] = useState<"create" | "upload" | null>(null);

  return (
    <SectionCard
      title="Letters"
      description="Offer, appointment, confirmation and other letters. Letters marked visible appear in the employee's app under More → Documents."
      action={
        canEdit && (
          <>
            <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setDialog("upload")}>
              <Upload className="size-3.5" /> Upload
            </Button>
            <Button size="sm" className="gap-1.5" onClick={() => setDialog("create")}>
              <FilePlus2 className="size-3.5" /> Create from template
            </Button>
          </>
        )
      }
    >
      {isLoading ? (
        <p className="text-sm text-brand-brown-light">Loading…</p>
      ) : letters.length === 0 ? (
        <EmptyState
          message="No letters on file yet. Create one on the letterhead, or upload a signed copy."
          actionLabel="Create from template"
          onAction={() => setDialog("create")}
        />
      ) : (
        <ul className="divide-y divide-brand-brown-50">
          {letters.map((l) => (
            <LetterRow key={l.id} letter={l} />
          ))}
        </ul>
      )}

      {dialog === "create" && (
        <CreateLetterModal employee={employee} onClose={() => setDialog(null)} />
      )}
      {dialog === "upload" && (
        <UploadLetterModal employeeId={employee.id} onClose={() => setDialog(null)} />
      )}
    </SectionCard>
  );
}

function LetterRow({ letter: l }: { letter: EmployeeLetter }) {
  const qc = useQueryClient();
  const canEdit = useCanEdit();
  const refresh = () => qc.invalidateQueries({ queryKey: ["employee-letters", l.employee_id] });
  const toggle = useMutation({
    mutationFn: () =>
      hrDocumentsApi.updateLetter(l.id, { visible_to_employee: !l.visible_to_employee }),
    onSuccess: (u) => {
      toast.success(u.visible_to_employee ? "Now visible in the employee's app" : "Hidden from the employee");
      refresh();
    },
    onError: (e) => toast.error(errDetail(e, "Could not change")),
  });
  const remove = useMutation({
    mutationFn: () => hrDocumentsApi.deleteLetter(l.id),
    onSuccess: () => {
      toast.success("Letter removed");
      refresh();
    },
    onError: (e) => toast.error(errDetail(e, "Could not remove")),
  });

  return (
    <li className="flex flex-wrap items-center gap-3 py-3">
      <div className="grid size-9 shrink-0 place-items-center rounded-lg bg-brand-gold/15 text-brand-gold-dark">
        <FileText className="size-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-brand-brown-darker">{l.title}</span>
          <Chip tone="gold">{letterTypeLabel(l.letter_type)}</Chip>
          <Chip tone={l.source === "generated" ? "info" : "neutral"}>
            {l.source === "generated" ? "On letterhead" : "Uploaded"}
          </Chip>
          {!l.visible_to_employee && <Chip tone="warning">Hidden from employee</Chip>}
        </div>
        <div className="mt-0.5 text-xs text-brand-brown-light">
          {[l.letter_number, fmtDate(l.issued_on), fmtBytes(l.file_size)].filter(Boolean).join(" · ")}
          {l.notes ? ` · ${l.notes}` : ""}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        <Button asChild variant="outline" size="sm">
          <a href={hrDocumentsApi.letterFileUrl(l.id)} target="_blank" rel="noreferrer">
            Open
          </a>
        </Button>
        {canEdit && (
          <>
            <Button
              variant="ghost"
              size="sm"
              title={l.visible_to_employee ? "Hide from employee" : "Show to employee"}
              aria-label={l.visible_to_employee ? "Hide from employee" : "Show to employee"}
              disabled={toggle.isPending}
              onClick={() => toggle.mutate()}
            >
              {l.visible_to_employee ? <Eye className="size-4" /> : <EyeOff className="size-4" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-error"
              aria-label="Remove letter"
              disabled={remove.isPending}
              onClick={() => {
                if (window.confirm(`Remove "${l.title}" from this employee's file?`)) remove.mutate();
              }}
            >
              <Trash2 className="size-4" />
            </Button>
          </>
        )}
      </div>
    </li>
  );
}

function VisibleCheckbox({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="col-span-full flex items-center gap-2 text-sm">
      <input type="checkbox" checked={value} onChange={(e) => onChange(e.target.checked)} />
      Show in the employee's app (More → Documents)
    </label>
  );
}

function CreateLetterModal({
  employee,
  onClose,
}: {
  employee: EmployeeDetail;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const { data: templates = [] } = useQuery({
    queryKey: ["letter-templates"],
    queryFn: () => letterTemplatesApi.list(false),
  });
  const [templateId, setTemplateId] = useState<number | "">("");
  const [letterType, setLetterType] = useState<LetterType>("other");
  const [title, setTitle] = useState("");
  const [letterNo, setLetterNo] = useState("");
  const [onDate, setOnDate] = useState(todayIso());
  const [lwd, setLwd] = useState("");
  const [ctc, setCtc] = useState("");
  const [ctcWords, setCtcWords] = useState("");
  const [visible, setVisible] = useState(true);
  const [notes, setNotes] = useState("");
  const [previewing, setPreviewing] = useState(false);

  const { data: nextNo } = useQuery({
    queryKey: ["next-letter-number", letterType, onDate.slice(0, 4)],
    queryFn: () => hrDocumentsApi.nextLetterNumber(letterType, onDate),
    enabled: !!templateId,
  });

  const tmpl = useMemo<LetterTemplate | undefined>(
    () => templates.find((t) => t.id === templateId),
    [templates, templateId],
  );
  const needsLwd =
    !!tmpl && (tmpl.category === "experience" || tmpl.body.includes("{{last_working_date}}"));
  const needsCtc =
    !!tmpl &&
    (tmpl.body.includes("{{ctc_amount}}") ||
      ["offer", "appointment", "increment"].includes(tmpl.category));

  const pick = (id: number | "") => {
    setTemplateId(id);
    const t = templates.find((x) => x.id === id);
    if (t) {
      setLetterType(CATEGORY_TYPE[t.category] ?? "other");
      setTitle(t.name);
    }
  };

  const options = () => ({
    letter_no: letterNo.trim() || undefined,
    last_working_date: lwd ? fmtDate(lwd) : undefined,
    ctc_amount: ctc.trim() || undefined,
    ctc_amount_words: ctcWords.trim() || undefined,
  });

  async function preview() {
    if (!tmpl) return;
    setPreviewing(true);
    try {
      openBlob(
        await letterTemplatesApi.generate(employee.id, tmpl.id, {
          ...options(),
          // Show the number it will get; the real one is taken on save.
          letter_no: letterNo.trim() || nextNo,
          on_date: fmtDate(onDate),
        }),
      );
    } catch (e) {
      toast.error(errDetail(e, "Could not preview"));
    } finally {
      setPreviewing(false);
    }
  }

  const issue = useMutation({
    mutationFn: () =>
      hrDocumentsApi.issueFromTemplate(employee.id, Number(templateId), {
        ...options(),
        letter_type: letterType,
        title: title.trim() || undefined,
        on_date: onDate,
        visible_to_employee: visible,
        notes: notes.trim() || undefined,
      }),
    onSuccess: (l) => {
      toast.success(`${l.title} saved${l.visible_to_employee ? " and shared with the employee" : ""}`);
      qc.invalidateQueries({ queryKey: ["employee-letters", employee.id] });
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not create the letter")),
  });

  return (
    <Modal
      wide
      title="Create letter from template"
      description={
        <>
          Printed on the company letterhead —{" "}
          <Link to="/settings?tab=letterhead" className="text-brand-gold-dark hover:underline">
            edit header, footer &amp; logo
          </Link>
          . Edit the wording in{" "}
          <Link to="/letters" className="text-brand-gold-dark hover:underline">
            Letters
          </Link>
          .
        </>
      }
      onClose={onClose}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Template" className="col-span-full">
          <select
            className={SELECT_CLASS}
            value={templateId}
            onChange={(e) => pick(e.target.value ? Number(e.target.value) : "")}
          >
            <option value="">Choose a letter…</option>
            {templates.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </Field>
        {tmpl && (
          <>
            <Field label="Letter type">
              <select
                className={SELECT_CLASS}
                value={letterType}
                onChange={(e) => setLetterType(e.target.value as LetterType)}
              >
                {LETTER_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {letterTypeLabel(t)}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Title (as the employee sees it)">
              <Input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} />
            </Field>
            <Field
              label="Letter no."
              help={letterNo.trim() ? "Using your number." : "Blank: numbered automatically."}
            >
              <Input
                value={letterNo}
                onChange={(e) => setLetterNo(e.target.value)}
                placeholder={nextNo ?? "Automatic"}
                maxLength={64}
              />
            </Field>
            <Field label="Letter date">
              <Input type="date" value={onDate} onChange={(e) => setOnDate(e.target.value)} />
            </Field>
            {needsLwd && (
              <Field label="Last working date">
                <Input type="date" value={lwd} onChange={(e) => setLwd(e.target.value)} />
              </Field>
            )}
            {needsCtc && (
              <>
                <Field label="CTC (figures)" help="Blank uses the CTC on the profile.">
                  <Input value={ctc} onChange={(e) => setCtc(e.target.value)} placeholder="6,00,000" />
                </Field>
                <Field label="CTC (words)">
                  <Input
                    value={ctcWords}
                    onChange={(e) => setCtcWords(e.target.value)}
                    placeholder="Six Lakh Only"
                  />
                </Field>
              </>
            )}
            <Field label="Note for HR (optional)" className="col-span-full">
              <Input value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={500} />
            </Field>
            <VisibleCheckbox value={visible} onChange={setVisible} />
          </>
        )}
        <FormActions
          onCancel={onClose}
          onSave={() => issue.mutate()}
          saving={issue.isPending}
          disabled={!tmpl || !title.trim()}
          saveLabel="Save letter"
          extra={
            <Button variant="outline" onClick={preview} disabled={!tmpl || previewing}>
              {previewing ? "Preparing…" : "Preview PDF"}
            </Button>
          }
        />
      </div>
    </Modal>
  );
}

function UploadLetterModal({ employeeId, onClose }: { employeeId: number; onClose: () => void }) {
  const qc = useQueryClient();
  const [letterType, setLetterType] = useState<LetterType>("offer");
  const [title, setTitle] = useState(letterTypeLabel("offer"));
  const [titleTouched, setTitleTouched] = useState(false);
  const [letterNo, setLetterNo] = useState("");
  const [issuedOn, setIssuedOn] = useState(todayIso());
  const [file, setFile] = useState<File | null>(null);
  const [visible, setVisible] = useState(true);
  const [notes, setNotes] = useState("");

  const upload = useMutation({
    mutationFn: () =>
      hrDocumentsApi.uploadLetter(
        employeeId,
        {
          letter_type: letterType,
          title: title.trim(),
          letter_number: letterNo.trim() || undefined,
          issued_on: issuedOn,
          visible_to_employee: visible,
          notes: notes.trim() || undefined,
        },
        file!,
      ),
    onSuccess: (l) => {
      toast.success(`${l.title} uploaded`);
      qc.invalidateQueries({ queryKey: ["employee-letters", employeeId] });
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not upload")),
  });

  return (
    <Modal
      title="Upload letter"
      description="A signed or scanned copy — PDF, JPG, PNG or WEBP, up to 10 MB."
      onClose={onClose}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Letter type">
          <select
            className={SELECT_CLASS}
            value={letterType}
            onChange={(e) => {
              const t = e.target.value as LetterType;
              setLetterType(t);
              if (!titleTouched) setTitle(letterTypeLabel(t));
            }}
          >
            {LETTER_TYPES.map((t) => (
              <option key={t} value={t}>
                {letterTypeLabel(t)}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Issued on">
          <Input type="date" value={issuedOn} onChange={(e) => setIssuedOn(e.target.value)} />
        </Field>
        <Field label="Title" className="col-span-full">
          <Input
            value={title}
            onChange={(e) => {
              setTitle(e.target.value);
              setTitleTouched(true);
            }}
            maxLength={200}
          />
        </Field>
        <Field label="Letter no. (optional)">
          <Input value={letterNo} onChange={(e) => setLetterNo(e.target.value)} maxLength={64} />
        </Field>
        <Field label="Note for HR (optional)">
          <Input value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={500} />
        </Field>
        <Field label="File" className="col-span-full">
          <Input type="file" accept={ACCEPT} onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </Field>
        <VisibleCheckbox value={visible} onChange={setVisible} />
        <FormActions
          onCancel={onClose}
          onSave={() => upload.mutate()}
          saving={upload.isPending}
          disabled={!file || title.trim().length < 2}
          saveLabel="Upload"
        />
      </div>
    </Modal>
  );
}
