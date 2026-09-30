import { useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  FileText,
  KeyRound,
  Pencil,
  ScrollText,
  ShieldOff,
  ShieldCheck,
  UserPlus,
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
import { PermissionGate } from "@/components/shared/PermissionGate";
import { useAuthStore } from "@/store/auth";
import {
  employeesApi,
  salaryTemplatesApi,
  type EmployeeDetail,
} from "@/lib/api/employees";
import { compensationApi, type SalaryRevision } from "@/lib/api/compensation";
import {
  payrollApi,
  pfCeilingApi,
  type GeneratedDocument,
} from "@/lib/api/payroll";
import { cn } from "@/lib/utils";
import { OnboardingDocsCard } from "./OnboardingDocsCard";
import { LettersDocsCard } from "./LettersDocsCard";
import { AttendanceLeaveCard } from "./AttendanceLeaveCard";
import { LifecycleDrawer } from "./LifecycleDrawer";
import {
  BankCard,
  FamilyCard,
  NomineesCard,
  PassportCard,
  StatutoryIdsCard,
} from "./EmployeeProfileExtras";
import { ProfileHeader } from "./profile/ProfileHeader";
import {
  ContactSection,
  JobSection,
  PersonalSection,
  SalarySection,
} from "./profile/sections";
import { LifecycleTimeline } from "./profile/LifecycleTimeline";
import { CompletenessCard, useCompleteness } from "./profile/CompletenessCard";
import { ExitBanner, hasLeft, isSeparated } from "./profile/ExitBanner";
import {
  EditableProvider,
  Field,
  FormActions,
  InfoGrid,
  InfoItem,
  SELECT_CLASS,
  SectionCard,
  useSaveEmployee,
} from "./profile/ui";
import { fmtIstDate } from "@/lib/datetime";

type TabKey = "overview" | "personal" | "pay" | "statutory" | "attendance" | "documents";

/** A tab shows when the user holds any one of its permissions. */
const TABS: { key: TabKey; label: string; anyOf?: string[] }[] = [
  { key: "overview", label: "Overview" },
  { key: "personal", label: "Personal" },
  { key: "pay", label: "Pay", anyOf: ["salary.view.team", "employee.update"] },
  { key: "statutory", label: "Statutory", anyOf: ["salary.view.team", "employee.update"] },
  { key: "attendance", label: "Attendance & leave", anyOf: ["attendance.view.all"] },
  { key: "documents", label: "Documents", anyOf: ["employee.update", "employee.create"] },
];

export default function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const employeeId = Number(id);
  const queryClient = useQueryClient();
  const [params, setParams] = useSearchParams();
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const tabBarRef = useRef<HTMLDivElement | null>(null);

  const { data: employee, isLoading } = useQuery({
    queryKey: ["employee", employeeId],
    queryFn: () => employeesApi.get(employeeId),
    enabled: Number.isFinite(employeeId),
  });
  const { data: completeness } = useCompleteness(employeeId);

  const [editOpen, setEditOpen] = useState(false);
  const [credentialOpen, setCredentialOpen] = useState(false);
  const [lifecycleOpen, setLifecycleOpen] = useState(false);
  const [editUnlocked, setEditUnlocked] = useState(false);

  const tabs = TABS.filter((t) => !t.anyOf || t.anyOf.some((p) => hasPermission(p)));
  const requested = params.get("tab") as TabKey | null;
  const tab: TabKey = tabs.some((t) => t.key === requested) ? requested! : "overview";
  const missingByTab = new Map<string, number>();
  for (const m of completeness?.missing ?? []) {
    missingByTab.set(m.section, (missingByTab.get(m.section) ?? 0) + 1);
  }

  const go = (key: string) => {
    const next = tabs.some((t) => t.key === key) ? key : "overview";
    setParams(
      (p) => {
        p.set("tab", next);
        return p;
      },
      { replace: true },
    );
    tabBarRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  if (isLoading || !employee) return <LoadingScreen label="Loading employee…" />;

  const canEdit =
    hasPermission("employee.update") && (!hasLeft(employee) || editUnlocked);
  const refreshEmployee = () => {
    queryClient.invalidateQueries({ queryKey: ["employee", employeeId] });
    queryClient.invalidateQueries({ queryKey: ["employee-completeness", employeeId] });
    queryClient.invalidateQueries({ queryKey: ["lifecycle", employeeId] });
    queryClient.invalidateQueries({ queryKey: ["employees"] });
  };

  return (
    <EditableProvider value={canEdit}>
      <div className="space-y-5">
        <button
          onClick={() => navigate("/employees")}
          className="flex items-center gap-2 text-sm text-brand-brown-light hover:text-brand-brown-darker"
        >
          <ArrowLeft className="h-4 w-4" /> Back to directory
        </button>

        {isSeparated(employee) && (
          <ExitBanner
            employee={employee}
            editUnlocked={editUnlocked}
            onToggleEdit={() => setEditUnlocked((u) => !u)}
          />
        )}

        <ProfileHeader
          employee={employee}
          onEdit={() => setEditOpen(true)}
          onCredentials={() => setCredentialOpen(true)}
          onManageLifecycle={() => setLifecycleOpen(true)}
          onOpenCompleteness={() => go("overview")}
        />

        <div
          ref={tabBarRef}
          className="sticky top-0 z-20 -mx-1 scroll-mt-4 bg-surface-cream/95 px-1 pt-1 backdrop-blur"
        >
          <nav
            role="tablist"
            aria-label="Profile sections"
            className="flex gap-1 overflow-x-auto border-b border-brand-brown-100"
          >
            {tabs.map((t) => {
              const missing = missingByTab.get(t.key) ?? 0;
              return (
                <button
                  key={t.key}
                  role="tab"
                  aria-selected={tab === t.key}
                  onClick={() => go(t.key)}
                  className={cn(
                    "-mb-px flex shrink-0 items-center gap-1.5 border-b-2 px-4 py-2.5 text-sm font-medium transition-colors",
                    tab === t.key
                      ? "border-brand-gold-dark text-brand-brown-darker"
                      : "border-transparent text-brand-brown-light hover:text-brand-brown-darker",
                  )}
                >
                  {t.label}
                  {missing > 0 && (
                    <span
                      className="grid h-4 min-w-4 place-items-center rounded-full bg-warning/15 px-1 text-[10px] font-semibold text-warning"
                      title={`${missing} item${missing === 1 ? "" : "s"} missing`}
                    >
                      {missing}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        <div role="tabpanel" className="space-y-4">
          {tab === "overview" && (
            <div className="grid items-start gap-4 lg:grid-cols-3">
              <div className="space-y-4 lg:col-span-2">
                <JobSection employee={employee} />
                <LifecycleTimeline employee={employee} />
              </div>
              <CompletenessCard employeeId={employee.id} onGo={go} />
            </div>
          )}

          {tab === "personal" && (
            <>
              <div className="grid items-start gap-4 lg:grid-cols-2">
                <PersonalSection employee={employee} />
                <ContactSection employee={employee} />
              </div>
              <PermissionGate permission="employee.update">
                <div className="grid items-start gap-4 lg:grid-cols-2">
                  <FamilyCard employeeId={employee.id} />
                  <NomineesCard employeeId={employee.id} />
                </div>
                <PassportCard employeeId={employee.id} />
              </PermissionGate>
            </>
          )}

          {tab === "pay" && (
            <>
              <PermissionGate permission="salary.view.team">
                <SalarySection employee={employee} />
                <CompensationHistoryCard employee={employee} />
              </PermissionGate>
              <PermissionGate permission="employee.update">
                <BankCard employeeId={employee.id} />
              </PermissionGate>
            </>
          )}

          {tab === "statutory" && (
            <>
              <PermissionGate permission="employee.update">
                <StatutoryIdsCard employee={employee} />
              </PermissionGate>
              <PermissionGate permission="salary.view.team">
                <StatutoryOverridesCard employee={employee} />
              </PermissionGate>
            </>
          )}

          {tab === "attendance" && <AttendanceLeaveCard employeeId={employee.id} />}

          {tab === "documents" && (
            <>
              <PermissionGate permission="employee.update">
                <OnboardingDocsCard employeeId={employee.id} />
                <LettersDocsCard
                  employeeId={employee.id}
                  employeeCode={employee.employee_code}
                />
              </PermissionGate>
              <PermissionGate permission="employee.create">
                <DocumentsCard employeeId={employee.id} />
              </PermissionGate>
            </>
          )}
        </div>

        {editOpen && (
          <EditEmployeeModal
            employee={employee}
            onClose={() => setEditOpen(false)}
            onSaved={() => {
              setEditOpen(false);
              refreshEmployee();
            }}
          />
        )}

        {credentialOpen && (
          <CredentialModal
            employeeId={employeeId}
            employeeName={`${employee.first_name} ${employee.last_name}`}
            defaultEmail={employee.personal_email ?? ""}
            onClose={() => setCredentialOpen(false)}
          />
        )}

        {lifecycleOpen && (
          <LifecycleDrawer
            employeeId={employee.id}
            employeeName={`${employee.first_name} ${employee.last_name}`}
            onClose={() => {
              setLifecycleOpen(false);
              refreshEmployee();
            }}
          />
        )}
      </div>
    </EditableProvider>
  );
}

function StatutoryOverridesCard({ employee }: { employee: EmployeeDetail }) {
  const [editing, setEditing] = useState(false);
  const { data: companyCap } = useQuery({
    queryKey: ["pf-cap-current"],
    queryFn: pfCeilingApi.current,
  });
  const companyCapLabel = companyCap
    ? `₹${Number(companyCap.pf_cap).toLocaleString("en-IN")}`
    : "the company cap";
  const epsMember = employee.eps_member ?? true;

  return (
    <SectionCard
      title="Statutory overrides"
      description="Per-employee exceptions to the salary template's PF, ESIC and PT rules."
      onEdit={() => setEditing(true)}
      editing={editing}
    >
      {editing ? (
        <StatutoryOverridesForm
          employee={employee}
          companyCapLabel={companyCapLabel}
          onDone={() => setEditing(false)}
        />
      ) : (
        <InfoGrid cols={3}>
          <InfoItem
            label="Provident fund"
            value={employee.pf_opt_out ? "Opted out (Form 11)" : "Contributes"}
          />
          <InfoItem
            label="PF wage cap"
            value={
              employee.pf_basic_cap_override
                ? `₹${Number(employee.pf_basic_cap_override).toLocaleString("en-IN")} (override)`
                : `${companyCapLabel} (company)`
            }
          />
          <InfoItem
            label="EPS (pension)"
            value={employee.pf_opt_out ? "—" : epsMember ? "Member" : "Not a member"}
          />
          <InfoItem
            label="ESIC"
            value={employee.esic_force_exempt ? "Exempt (forced)" : "As per gross (≤ ₹21,000)"}
          />
          <InfoItem
            label="Professional tax"
            value={employee.pt_state === "MH" ? "Maharashtra" : employee.pt_state || "No PT"}
          />
        </InfoGrid>
      )}
    </SectionCard>
  );
}

function StatutoryOverridesForm({
  employee,
  companyCapLabel,
  onDone,
}: {
  employee: EmployeeDetail;
  companyCapLabel: string;
  onDone: () => void;
}) {
  const [pfOptOut, setPfOptOut] = useState(employee.pf_opt_out);
  const [pfCap, setPfCap] = useState<string>(employee.pf_basic_cap_override ?? "");
  const [esicExempt, setEsicExempt] = useState(employee.esic_force_exempt);
  const [epsMember, setEpsMember] = useState(employee.eps_member ?? true);
  const [ptState, setPtState] = useState<string>(employee.pt_state ?? "");
  const save = useSaveEmployee(employee.id, "Statutory overrides saved");

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Check
        checked={pfOptOut}
        onChange={setPfOptOut}
        title="PF opt-out"
        help="Skips both employee and employer PF. Only with a valid Form 11 declaration."
      />
      <Check
        checked={esicExempt}
        onChange={setEsicExempt}
        title="ESIC force-exempt"
        help="Skips ESIC even when gross is ≤ ₹21,000 — e.g. international staff or contractors."
      />
      <Check
        checked={epsMember}
        onChange={setEpsMember}
        disabled={pfOptOut}
        title="EPS (pension) member"
        help="Untick for members who joined EPF on or after 1 Sep 2014 with basic above ₹15,000, or who are 58+. The PF challan then shows EPS as 0 and the full share goes to EPF."
      />
      <div />
      <Field
        label="PF wage cap override (₹)"
        help={`Leave blank to use the company cap (${companyCapLabel}) from Settings → Payroll.`}
      >
        <Input
          type="number"
          min={0}
          step={1}
          value={pfCap}
          placeholder={`Company cap ${companyCapLabel}`}
          onChange={(e) => setPfCap(e.target.value)}
        />
      </Field>
      <Field
        label="Professional tax state"
        help="Maharashtra: ₹175 (₹7,501–₹10,000), ₹200 above. Women up to ₹25,000/m are exempt."
      >
        <select
          value={ptState}
          onChange={(e) => setPtState(e.target.value)}
          className={SELECT_CLASS}
        >
          <option value="">— No PT —</option>
          <option value="MH">Maharashtra</option>
          {ptState && ptState !== "MH" && <option value={ptState}>{ptState}</option>}
        </select>
      </Field>
      <FormActions
        onCancel={onDone}
        saving={save.isPending}
        onSave={() =>
          save.mutate(
            {
              pf_opt_out: pfOptOut,
              pf_basic_cap_override: pfCap === "" ? null : pfCap,
              esic_force_exempt: esicExempt,
              eps_member: epsMember,
              pt_state: ptState === "" ? null : ptState,
            },
            { onSuccess: onDone },
          )
        }
      />
    </div>
  );
}

function Check({
  checked,
  onChange,
  title,
  help,
  disabled = false,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  title: string;
  help: string;
  disabled?: boolean;
}) {
  return (
    <label
      className={cn(
        "flex items-start gap-3 rounded-xl border border-brand-brown-50 p-3 text-sm",
        disabled && "opacity-50",
      )}
    >
      <input
        type="checkbox"
        className="mt-1 accent-brand-gold-dark"
        checked={checked}
        disabled={disabled}
        onChange={(e) => onChange(e.target.checked)}
      />
      <div>
        <div className="font-medium">{title}</div>
        <div className="text-xs text-brand-brown-light">{help}</div>
      </div>
    </label>
  );
}

function DocumentsCard({ employeeId }: { employeeId: number }) {
  const queryClient = useQueryClient();
  const todayStr = new Date().toISOString().slice(0, 10);
  const [letterDate, setLetterDate] = useState(todayStr);

  const { data: documents = [] } = useQuery({
    queryKey: ["employee-documents", employeeId],
    queryFn: () => payrollApi.listEmployeeDocuments(employeeId),
  });

  const generateOffer = useMutation({
    mutationFn: () => payrollApi.generateOfferLetter(employeeId, letterDate),
    onSuccess: (doc) => {
      toast.success(`Offer letter ${doc.letter_number} generated`);
      queryClient.invalidateQueries({ queryKey: ["employee-documents"] });
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not generate offer letter";
      toast.error(detail);
    },
  });
  const generateConfirmation = useMutation({
    mutationFn: () =>
      payrollApi.generateConfirmationLetter(employeeId, letterDate),
    onSuccess: (doc) => {
      toast.success(
        `Confirmation letter ${doc.letter_number} generated — employee confirmed`,
      );
      queryClient.invalidateQueries({ queryKey: ["employee-documents"] });
      queryClient.invalidateQueries({ queryKey: ["employee", employeeId] });
      queryClient.invalidateQueries({ queryKey: ["employees"] });
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not generate confirmation letter";
      toast.error(detail);
    },
  });
  const deleteConfirmation = useMutation({
    mutationFn: () => payrollApi.deleteConfirmationLetter(employeeId),
    onSuccess: () => {
      toast.success(
        "Confirmation letter deleted — employee back on probation",
      );
      queryClient.invalidateQueries({ queryKey: ["employee-documents"] });
      queryClient.invalidateQueries({ queryKey: ["employee", employeeId] });
      queryClient.invalidateQueries({ queryKey: ["employees"] });
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not delete confirmation letter";
      toast.error(detail);
    },
  });
  const hasConfirmation = documents.some(
    (d) => d.doc_type === "confirmation_letter",
  );

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>
          Letters & <span className="display-em">documents</span>
        </CardTitle>
        <CardDescription>
          Offer letter follows the Jaikalki <code className="font-mono">JKT/HR/AL/&lt;seq&gt;/&lt;year&gt;</code> format.
          The letter date below is printed on the PDF and saved with the
          document.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-end gap-3">
          <div className="space-y-1.5">
            <Label>Letter date</Label>
            <Input
              type="date"
              value={letterDate}
              onChange={(e) => setLetterDate(e.target.value)}
              className="w-44"
            />
          </div>
          <Button
            onClick={() => generateOffer.mutate()}
            disabled={generateOffer.isPending}
            variant="gold"
          >
            <ScrollText className="h-4 w-4" />
            Generate offer letter
          </Button>
          <Button
            asChild
            variant="outline"
          >
            <a
              href={payrollApi.offerLetterPreviewUrl(employeeId, letterDate)}
              target="_blank"
              rel="noreferrer"
            >
              <FileText className="h-4 w-4" />
              Preview PDF
            </a>
          </Button>
          <Button
            onClick={() => generateConfirmation.mutate()}
            disabled={generateConfirmation.isPending}
            variant="outline"
          >
            Generate confirmation
          </Button>
          {hasConfirmation && (
            <Button
              onClick={() => {
                if (
                  confirm(
                    "Delete the confirmation letter? This puts the employee back on probation and clears their confirmation date.",
                  )
                )
                  deleteConfirmation.mutate();
              }}
              disabled={deleteConfirmation.isPending}
              variant="outline"
              className="text-destructive"
            >
              Delete confirmation
            </Button>
          )}
        </div>
        <p className="text-xs text-brand-brown-light">
          Generating a confirmation letter also marks the employee
          confirmed: it sets the confirmation date and probation-end
          date to the letter date and ends probation. Deleting it
          reverts all three.
        </p>
        {documents.length > 0 && (
          <div className="space-y-1">
            {documents.map((d) => (
              <DocumentRow key={d.id} doc={d} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function DocumentRow({ doc }: { doc: GeneratedDocument }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-brand-brown-100/60 last:border-0">
      <div>
        <div className="text-sm font-medium">
          {doc.doc_type === "offer_letter"
            ? "Offer letter"
            : doc.doc_type === "confirmation_letter"
              ? "Confirmation letter"
              : doc.doc_type}
        </div>
        <div className="text-xs font-mono text-brand-brown-light">
          {doc.letter_number ?? "—"} · {fmtIstDate(doc.created_at)}
        </div>
      </div>
      {doc.file_url && !doc.file_url.startsWith("local://") && (
        <a
          href={doc.file_url}
          target="_blank"
          rel="noreferrer"
          className="text-xs font-mono uppercase tracking-[0.2em] text-brand-gold-dark hover:text-brand-brown-darker"
        >
          Open →
        </a>
      )}
    </div>
  );
}

interface EmployeeEditDraft {
  first_name: string;
  last_name: string;
  personal_email: string;
  personal_phone: string;
  date_of_birth: string;
  gender: string;
  marital_status: string;
  blood_group: string;
  work_location: string;
  work_mode: string;
  department_id: string;
  designation_id: string;
  salary_template_id: string;
  reporting_to: string;
  ctc_annual: string;
  date_of_joining: string;
}

function EditEmployeeModal({
  employee,
  onClose,
  onSaved,
}: {
  employee: import("@/lib/api/employees").EmployeeDetail;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: () => import("@/lib/api/employees").then((m) => m.lookupsApi.departments()),
  });
  const { data: designations = [] } = useQuery({
    queryKey: ["designations"],
    queryFn: () => import("@/lib/api/employees").then((m) => m.lookupsApi.designations()),
  });
  const { data: templates = [] } = useQuery({
    queryKey: ["salary-templates"],
    queryFn: () => salaryTemplatesApi.list(),
  });
  const { data: managers = [] } = useQuery({
    queryKey: ["employees-as-managers"],
    queryFn: () => employeesApi.list(),
  });

  const [draft, setDraft] = useState<EmployeeEditDraft>({
    first_name: employee.first_name,
    last_name: employee.last_name,
    personal_email: employee.personal_email ?? "",
    personal_phone: employee.personal_phone ?? "",
    date_of_birth: employee.date_of_birth ?? "",
    gender: employee.gender ?? "",
    marital_status: employee.marital_status ?? "",
    blood_group: employee.blood_group ?? "",
    work_location: employee.work_location ?? "",
    work_mode: employee.work_mode ?? "",
    department_id: employee.department?.id ? String(employee.department.id) : "",
    designation_id: employee.designation?.id ? String(employee.designation.id) : "",
    salary_template_id: employee.salary_template?.id
      ? String(employee.salary_template.id)
      : "",
    reporting_to: employee.reporting_to ? String(employee.reporting_to) : "",
    ctc_annual: employee.ctc_annual ?? "",
    date_of_joining: employee.date_of_joining ?? "",
  });
  const dojChanged =
    !!draft.date_of_joining &&
    draft.date_of_joining !== (employee.date_of_joining ?? "");

  const update = useMutation({
    mutationFn: () =>
      employeesApi.update(employee.id, {
        first_name: draft.first_name,
        last_name: draft.last_name,
        personal_email: draft.personal_email || null,
        personal_phone: draft.personal_phone || null,
        date_of_birth: draft.date_of_birth || null,
        gender: draft.gender || null,
        marital_status: draft.marital_status || null,
        blood_group: draft.blood_group || null,
        work_location: draft.work_location || undefined,
        work_mode: draft.work_mode || undefined,
        department_id: draft.department_id ? Number(draft.department_id) : null,
        designation_id: draft.designation_id ? Number(draft.designation_id) : null,
        salary_template_id: draft.salary_template_id
          ? Number(draft.salary_template_id)
          : null,
        reporting_to: draft.reporting_to ? Number(draft.reporting_to) : null,
        ...(dojChanged ? { date_of_joining: draft.date_of_joining } : {}),
        ctc_annual:
          draft.ctc_annual === "" || draft.ctc_annual === null
            ? null
            : Number(draft.ctc_annual),
      } as never),
    onSuccess: () => {
      toast.success("Employee updated");
      onSaved();
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not update";
      toast.error(detail);
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-3xl max-h-[92vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Edit employee</CardTitle>
            <CardDescription>
              Personal details, department, designation and salary
              template are editable here. Salary CTC changes are tracked
              separately under Compensation history below.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>First name *</Label>
            <Input
              value={draft.first_name}
              onChange={(e) =>
                setDraft({ ...draft, first_name: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Last name *</Label>
            <Input
              value={draft.last_name}
              onChange={(e) =>
                setDraft({ ...draft, last_name: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Personal email</Label>
            <Input
              type="email"
              value={draft.personal_email}
              onChange={(e) =>
                setDraft({ ...draft, personal_email: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Personal phone</Label>
            <Input
              value={draft.personal_phone}
              onChange={(e) =>
                setDraft({ ...draft, personal_phone: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Date of birth</Label>
            <Input
              type="date"
              value={draft.date_of_birth}
              onChange={(e) =>
                setDraft({ ...draft, date_of_birth: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Gender</Label>
            <select
              value={draft.gender}
              onChange={(e) => setDraft({ ...draft, gender: e.target.value })}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">—</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <Label>Marital status</Label>
            <select
              value={draft.marital_status}
              onChange={(e) =>
                setDraft({ ...draft, marital_status: e.target.value })
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">—</option>
              <option value="single">Single</option>
              <option value="married">Married</option>
              <option value="divorced">Divorced</option>
              <option value="widowed">Widowed</option>
            </select>
          </div>
          <div>
            <Label>Blood group</Label>
            <Input
              value={draft.blood_group}
              onChange={(e) =>
                setDraft({ ...draft, blood_group: e.target.value })
              }
              placeholder="O+, A-, …"
            />
          </div>
          <div>
            <Label>Work location</Label>
            <Input
              value={draft.work_location}
              onChange={(e) =>
                setDraft({ ...draft, work_location: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Work mode</Label>
            <select
              value={draft.work_mode}
              onChange={(e) =>
                setDraft({ ...draft, work_mode: e.target.value })
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">—</option>
              <option value="office">Office</option>
              <option value="hybrid">Hybrid</option>
              <option value="remote">Remote</option>
              <option value="field">Field</option>
            </select>
          </div>
          <div className="md:col-span-2 mt-2 text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Org placement
          </div>
          <div className="md:col-span-2">
            <Label>Date of joining *</Label>
            <Input
              type="date"
              value={draft.date_of_joining}
              onChange={(e) =>
                setDraft({ ...draft, date_of_joining: e.target.value })
              }
              className="md:w-1/2"
            />
            {dojChanged ? (
              <p className="text-xs text-warning mt-1">
                Changing from {employee.date_of_joining ?? "—"}. The open
                intern / probation period moves by the same number of days,
                attendance before the new date is hidden, and the next
                payroll run pro-rates from it. Blocked if a finalized payroll
                already pays a month before the new date.
              </p>
            ) : (
              <p className="text-xs text-brand-brown-light mt-1">
                Correct a wrong joining date here. It drives attendance,
                probation, leave and payroll pro-rating.
              </p>
            )}
          </div>
          <div>
            <Label>Department</Label>
            <select
              value={draft.department_id}
              onChange={(e) =>
                setDraft({ ...draft, department_id: e.target.value })
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">—</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Designation</Label>
            <select
              value={draft.designation_id}
              onChange={(e) =>
                setDraft({ ...draft, designation_id: e.target.value })
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">—</option>
              {designations.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} (L{d.level})
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Salary template</Label>
            <select
              value={draft.salary_template_id}
              onChange={(e) =>
                setDraft({ ...draft, salary_template_id: e.target.value })
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">—</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.template_code} · {t.template_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Reports to</Label>
            <select
              value={draft.reporting_to}
              onChange={(e) =>
                setDraft({ ...draft, reporting_to: e.target.value })
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">—</option>
              {managers
                .filter((m) => m.id !== employee.id)
                .map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.employee_code} · {m.first_name} {m.last_name}
                  </option>
                ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <Label>CTC (annual ₹)</Label>
            <Input
              type="number"
              min={0}
              step={1}
              value={draft.ctc_annual}
              onChange={(e) =>
                setDraft({ ...draft, ctc_annual: e.target.value })
              }
            />
            <p className="text-xs text-brand-brown-light mt-1">
              Direct edit — for typos or backfilling old data. For raises
              and increments use <strong>New revision</strong> below so the
              change shows up in compensation history.
            </p>
          </div>
          <div className="md:col-span-2 flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              disabled={
                !draft.first_name ||
                !draft.last_name ||
                !draft.date_of_joining ||
                update.isPending
              }
              onClick={() => update.mutate()}
            >
              {update.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function CredentialModal({
  employeeId,
  employeeName,
  defaultEmail,
  onClose,
}: {
  employeeId: number;
  employeeName: string;
  defaultEmail: string;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const { data: cred, isLoading } = useQuery({
    queryKey: ["employee-credential", employeeId],
    queryFn: () => employeesApi.getCredential(employeeId),
  });

  const [createEmail, setCreateEmail] = useState(defaultEmail);
  const [createPassword, setCreatePassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  const createCred = useMutation({
    mutationFn: () =>
      employeesApi.createCredential(employeeId, {
        email: createEmail,
        password: createPassword,
      }),
    onSuccess: () => {
      toast.success("Mobile login created");
      setCreatePassword("");
      queryClient.invalidateQueries({
        queryKey: ["employee-credential", employeeId],
      });
      queryClient.invalidateQueries({
        queryKey: ["employee", employeeId],
      });
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not create login";
      toast.error(detail);
    },
  });

  const resetPwd = useMutation({
    mutationFn: () =>
      employeesApi.resetCredentialPassword(employeeId, newPassword),
    onSuccess: () => {
      toast.success("Password reset");
      setNewPassword("");
      queryClient.invalidateQueries({
        queryKey: ["employee-credential", employeeId],
      });
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not reset";
      toast.error(detail);
    },
  });

  const setActive = useMutation({
    mutationFn: (active: boolean) =>
      employeesApi.setCredentialActive(employeeId, active),
    onSuccess: () => {
      toast.success("Account updated");
      queryClient.invalidateQueries({
        queryKey: ["employee-credential", employeeId],
      });
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-xl">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <KeyRound className="size-5 text-brand-gold-dark" />
              Mobile login
            </CardTitle>
            <CardDescription>{employeeName}</CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="text-sm text-brand-brown-light">Loading…</div>
          ) : !cred?.has_account ? (
            <div className="space-y-3">
              <div className="rounded-md bg-info/10 p-3 text-xs text-info">
                <UserPlus className="inline size-3 mr-1" />
                No mobile-app account exists for this employee yet. Set their
                login email and an initial password — they can change it after
                signing in.
              </div>
              <div>
                <Label>Login email *</Label>
                <Input
                  type="email"
                  value={createEmail}
                  onChange={(e) => setCreateEmail(e.target.value)}
                  placeholder="employee@jaikalki.com"
                />
              </div>
              <div>
                <Label>Initial password *</Label>
                <Input
                  type="text"
                  value={createPassword}
                  onChange={(e) => setCreatePassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                />
              </div>
              <div className="flex justify-end">
                <Button
                  disabled={
                    !createEmail ||
                    createPassword.length < 8 ||
                    createCred.isPending
                  }
                  onClick={() => createCred.mutate()}
                  className="gap-2"
                >
                  <UserPlus className="size-4" />
                  {createCred.isPending ? "Creating…" : "Create login"}
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-md border border-brand-brown-50 p-3 text-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                      Login email
                    </div>
                    <div className="font-medium">{cred.email}</div>
                  </div>
                  <span
                    className={`rounded-full px-2 py-1 text-xs ${cred.is_active ? "bg-success/15 text-success" : "bg-error/15 text-error"}`}
                  >
                    {cred.is_active ? "Active" : "Disabled"}
                  </span>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Reset password</Label>
                <Input
                  type="text"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Minimum 8 characters"
                />
                <div className="flex justify-end">
                  <Button
                    disabled={newPassword.length < 8 || resetPwd.isPending}
                    onClick={() => resetPwd.mutate()}
                    className="gap-2"
                  >
                    <KeyRound className="size-4" />
                    {resetPwd.isPending ? "Saving…" : "Set new password"}
                  </Button>
                </div>
              </div>

              <div className="flex justify-between items-center pt-2 border-t border-brand-brown-50">
                <div className="text-xs text-brand-brown-light">
                  {cred.is_active
                    ? "Disable to block mobile sign-in immediately."
                    : "Re-enable to restore mobile sign-in."}
                </div>
                {cred.is_active ? (
                  <Button
                    variant="outline"
                    className="gap-2 text-destructive"
                    onClick={() => setActive.mutate(false)}
                  >
                    <ShieldOff className="size-4" /> Disable
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    className="gap-2"
                    onClick={() => setActive.mutate(true)}
                  >
                    <ShieldCheck className="size-4" /> Re-enable
                  </Button>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

const REVISION_REASONS = [
  { value: "annual_review", label: "Annual review" },
  { value: "promotion", label: "Promotion" },
  { value: "market_correction", label: "Market correction" },
  { value: "retention", label: "Retention" },
  { value: "role_change", label: "Role change" },
  { value: "other", label: "Other" },
];

const REVISION_STATUS_TONE: Record<string, string> = {
  draft: "bg-brand-brown-50 text-brand-brown-darker",
  pending_approval: "bg-info/15 text-info",
  approved: "bg-brand-gold/15 text-brand-gold-dark",
  applied: "bg-success/15 text-success",
  rejected: "bg-error/15 text-error",
  cancelled: "bg-brand-brown-50 text-brand-brown-light",
};

function CompensationHistoryCard({
  employee,
}: {
  employee: import("@/lib/api/employees").EmployeeDetail;
}) {
  const qc = useQueryClient();
  const [proposeOpen, setProposeOpen] = useState(false);

  const { data: revisions = [] } = useQuery({
    queryKey: ["compensation-revisions", employee.id],
    queryFn: () => compensationApi.forEmployee(employee.id),
  });

  const sorted = [...revisions].sort((a, b) =>
    a.effective_date < b.effective_date ? 1 : -1,
  );
  const applied = sorted.filter((r) => r.status === "applied");
  const inFlight = sorted.filter(
    (r) =>
      r.status !== "applied" &&
      r.status !== "rejected" &&
      r.status !== "cancelled",
  );

  const activeCtc = Number(employee.ctc_annual);
  const previousCtc =
    applied.length > 0 ? Number(applied[0].previous_ctc_annual) : null;

  const inr = (n: number) => `₹${n.toLocaleString("en-IN")}`;

  return (
    <Card className="lg:col-span-2">
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle>
            Compensation <span className="display-em">history</span>
          </CardTitle>
          <CardDescription>
            Active CTC plus every salary revision applied to this employee.
            New revisions create an auditable record (old vs new CTC,
            increment %, reason, effective date).
          </CardDescription>
        </div>
        <Button onClick={() => setProposeOpen(true)} className="gap-2">
          <Pencil className="size-4" />
          New revision
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid sm:grid-cols-3 gap-3">
          <CompStat
            label="Active CTC"
            value={inr(activeCtc)}
            sub={`per year`}
            tone="gold"
          />
          <CompStat
            label={previousCtc !== null ? "Previous CTC" : "Joining CTC"}
            value={
              previousCtc !== null ? inr(previousCtc) : inr(activeCtc)
            }
            sub={
              previousCtc !== null
                ? `before ${applied[0]?.effective_date ?? ""}`
                : `no revision yet`
            }
          />
          <CompStat
            label="Total revisions"
            value={String(applied.length)}
            sub={
              inFlight.length
                ? `${inFlight.length} in progress`
                : "all applied"
            }
          />
        </div>

        {sorted.length === 0 ? (
          <p className="text-sm text-brand-brown-light">
            No salary revisions on record yet.
          </p>
        ) : (
          <div className="rounded-xl border border-brand-brown-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-brand-brown-50/60">
                <tr>
                  {[
                    "Effective",
                    "Old CTC",
                    "New CTC",
                    "Increment",
                    "Reason",
                    "Status",
                    "Actions",
                  ].map((h) => (
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
                {sorted.map((r) => (
                  <RevisionRow
                    key={r.id}
                    rev={r}
                    onChanged={() => {
                      qc.invalidateQueries({
                        queryKey: ["compensation-revisions", employee.id],
                      });
                      qc.invalidateQueries({
                        queryKey: ["employee", employee.id],
                      });
                      qc.invalidateQueries({ queryKey: ["salary-breakup"] });
                    }}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>

      {proposeOpen && (
        <ProposeRevisionModal
          employee={employee}
          onClose={() => setProposeOpen(false)}
          onDone={() => {
            setProposeOpen(false);
            qc.invalidateQueries({
              queryKey: ["compensation-revisions", employee.id],
            });
            qc.invalidateQueries({ queryKey: ["employee", employee.id] });
            qc.invalidateQueries({ queryKey: ["salary-breakup"] });
          }}
        />
      )}
    </Card>
  );
}

function CompStat({
  label,
  value,
  sub,
  tone = "muted",
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "muted" | "gold";
}) {
  const valueCls =
    tone === "gold" ? "text-brand-gold-dark" : "text-brand-brown-darker";
  return (
    <div className="rounded-md border border-brand-brown-100 p-3">
      <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
        {label}
      </div>
      <div className={`text-xl font-semibold ${valueCls}`}>{value}</div>
      {sub && (
        <div className="text-xs text-brand-brown-light mt-0.5">{sub}</div>
      )}
    </div>
  );
}

function RevisionRow({
  rev,
  onChanged,
}: {
  rev: SalaryRevision;
  onChanged: () => void;
}) {
  const inr = (n: number) => `₹${n.toLocaleString("en-IN")}`;
  const old = Number(rev.previous_ctc_annual);
  const neu = Number(rev.new_ctc_annual);
  const pct = Number(rev.increment_pct);
  const tone =
    REVISION_STATUS_TONE[rev.status] ??
    "bg-brand-brown-50 text-brand-brown-darker";

  const err = (e: unknown, fb: string) =>
    toast.error(
      (e as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail ?? fb,
    );

  const approve = useMutation({
    mutationFn: () => compensationApi.approve(rev.id),
    onSuccess: () => {
      toast.success("Revision approved");
      onChanged();
    },
    onError: (e) => err(e, "Could not approve"),
  });
  const apply = useMutation({
    mutationFn: () => compensationApi.apply(rev.id),
    onSuccess: () => {
      toast.success("Revision applied — CTC updated");
      onChanged();
    },
    onError: (e) => err(e, "Could not apply"),
  });
  const reject = useMutation({
    mutationFn: () => compensationApi.reject(rev.id),
    onSuccess: () => {
      toast.success("Revision rejected");
      onChanged();
    },
    onError: (e) => err(e, "Could not reject"),
  });
  const cancel = useMutation({
    mutationFn: () => compensationApi.cancel(rev.id),
    onSuccess: () => {
      toast.success("Revision cancelled");
      onChanged();
    },
    onError: (e) => err(e, "Could not cancel"),
  });
  const undo = useMutation({
    mutationFn: () => compensationApi.undoApply(rev.id),
    onSuccess: () => {
      toast.success("Revision undone — CTC restored");
      onChanged();
    },
    onError: (e) => err(e, "Could not undo"),
  });
  const [editOpen, setEditOpen] = useState(false);

  const busy =
    approve.isPending ||
    apply.isPending ||
    reject.isPending ||
    cancel.isPending ||
    undo.isPending;

  return (
    <tr className="border-t border-brand-brown-100/60">
      <td className="px-3 py-2 font-mono text-xs">{rev.effective_date}</td>
      <td className="px-3 py-2">{inr(old)}</td>
      <td className="px-3 py-2 font-medium text-brand-gold-dark">
        {inr(neu)}
      </td>
      <td
        className={`px-3 py-2 text-xs ${pct >= 0 ? "text-success" : "text-error"}`}
      >
        {pct >= 0 ? "+" : ""}
        {pct.toFixed(2)}%
      </td>
      <td className="px-3 py-2 text-xs text-brand-brown-light capitalize">
        {rev.reason.replace("_", " ")}
      </td>
      <td className="px-3 py-2">
        <span
          className={`text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded ${tone}`}
        >
          {rev.status.replace("_", " ")}
        </span>
      </td>
      <td className="px-3 py-2">
        <div className="flex flex-wrap gap-1.5">
          {(rev.status === "draft" ||
            rev.status === "pending_approval") && (
            <Button
              size="sm"
              className="h-7"
              disabled={busy}
              onClick={() => approve.mutate()}
            >
              Approve
            </Button>
          )}
          {rev.status === "approved" && (
            <Button
              size="sm"
              className="h-7"
              disabled={busy}
              onClick={() => apply.mutate()}
            >
              Apply
            </Button>
          )}
          {(rev.status === "draft" ||
            rev.status === "pending_approval") && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-destructive"
              disabled={busy}
              onClick={() => reject.mutate()}
            >
              Reject
            </Button>
          )}
          {(rev.status === "draft" ||
            rev.status === "pending_approval") && (
            <Button
              size="sm"
              variant="outline"
              className="h-7"
              disabled={busy}
              onClick={() => setEditOpen(true)}
            >
              Edit
            </Button>
          )}
          {(rev.status === "draft" ||
            rev.status === "pending_approval" ||
            rev.status === "approved") && (
            <Button
              size="sm"
              variant="outline"
              className="h-7"
              disabled={busy}
              onClick={() => cancel.mutate()}
            >
              Cancel
            </Button>
          )}
          {rev.status === "applied" && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-destructive"
              disabled={busy}
              onClick={() => {
                if (
                  confirm(
                    "Undo this applied revision? The employee's CTC / template / designation will be restored to their pre-revision values.",
                  )
                )
                  undo.mutate();
              }}
            >
              Undo
            </Button>
          )}
          {(rev.status === "rejected" ||
            rev.status === "cancelled") && (
            <span className="text-[11px] text-brand-brown-light">—</span>
          )}
        </div>
      </td>
      {editOpen && (
        <EditRevisionModal
          rev={rev}
          onClose={() => setEditOpen(false)}
          onDone={() => {
            setEditOpen(false);
            onChanged();
          }}
        />
      )}
    </tr>
  );
}

function EditRevisionModal({
  rev,
  onClose,
  onDone,
}: {
  rev: SalaryRevision;
  onClose: () => void;
  onDone: () => void;
}) {
  const [newCtc, setNewCtc] = useState(String(rev.new_ctc_annual));
  const [effective, setEffective] = useState(rev.effective_date);
  const [reason, setReason] = useState(rev.reason);
  const [notes, setNotes] = useState(rev.notes ?? "");

  const save = useMutation({
    mutationFn: () =>
      compensationApi.update(rev.id, {
        new_ctc_annual: Number(newCtc),
        effective_date: effective,
        reason,
        notes: notes || undefined,
      }),
    onSuccess: () => {
      toast.success("Revision updated");
      onDone();
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not update";
      toast.error(detail);
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Edit revision</CardTitle>
            <CardDescription>
              Only draft / pending revisions can be edited.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>New CTC (₹/yr)</Label>
            <Input
              type="number"
              min={0}
              value={newCtc}
              onChange={(e) => setNewCtc(e.target.value)}
            />
          </div>
          <div>
            <Label>Effective date</Label>
            <Input
              type="date"
              value={effective}
              onChange={(e) => setEffective(e.target.value)}
            />
          </div>
          <div>
            <Label>Reason</Label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {REVISION_REASONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Notes</Label>
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              disabled={!Number(newCtc) || !effective || save.isPending}
              onClick={() => save.mutate()}
            >
              {save.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ProposeRevisionModal({
  employee,
  onClose,
  onDone,
}: {
  employee: import("@/lib/api/employees").EmployeeDetail;
  onClose: () => void;
  onDone: () => void;
}) {
  const todayStr = new Date().toISOString().slice(0, 10);
  const [newCtc, setNewCtc] = useState<string>(String(employee.ctc_annual));
  const [effective, setEffective] = useState<string>(todayStr);
  const [reason, setReason] = useState("annual_review");
  const [notes, setNotes] = useState("");
  const [autoApply, setAutoApply] = useState(true);
  const [templateId, setTemplateId] = useState<string>(
    employee.salary_template?.id ? String(employee.salary_template.id) : "",
  );

  const { data: templates = [] } = useQuery({
    queryKey: ["salary-templates"],
    queryFn: () => salaryTemplatesApi.list(),
  });

  const oldCtc = Number(employee.ctc_annual);
  const newCtcNum = Number(newCtc);
  const pct = oldCtc > 0 ? ((newCtcNum - oldCtc) / oldCtc) * 100 : 0;
  const currentTemplateId = employee.salary_template?.id ?? null;
  const templateChanged =
    !!templateId && Number(templateId) !== currentTemplateId;

  const submit = useMutation({
    mutationFn: async () => {
      const proposed = await compensationApi.propose({
        employee_id: employee.id,
        new_ctc_annual: newCtcNum,
        effective_date: effective,
        reason,
        notes: notes || undefined,
        new_salary_template_id: templateChanged
          ? Number(templateId)
          : undefined,
      });
      if (autoApply) {
        try {
          await compensationApi.approve(proposed.id);
        } catch {
          /* some flows auto-approve on propose */
        }
        await compensationApi.apply(proposed.id);
      }
      return proposed;
    },
    onSuccess: () => {
      toast.success(
        autoApply
          ? "Salary revision applied"
          : "Salary revision saved as draft",
      );
      onDone();
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not save revision";
      toast.error(detail);
    },
  });

  const valid =
    newCtcNum > 0 &&
    Number.isFinite(newCtcNum) &&
    newCtcNum !== oldCtc &&
    !!effective;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-xl">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>New salary revision</CardTitle>
            <CardDescription>
              {employee.first_name} {employee.last_name} ·{" "}
              <code>{employee.employee_code}</code>
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Old CTC (₹/yr)</Label>
              <Input value={oldCtc.toLocaleString("en-IN")} disabled />
            </div>
            <div>
              <Label>New CTC (₹/yr) *</Label>
              <Input
                type="number"
                min={0}
                value={newCtc}
                onChange={(e) => setNewCtc(e.target.value)}
              />
            </div>
          </div>
          {newCtcNum > 0 && oldCtc > 0 && newCtcNum !== oldCtc && (
            <div
              className={`text-xs font-mono ${pct >= 0 ? "text-success" : "text-error"}`}
            >
              Change: {pct >= 0 ? "+" : ""}
              {pct.toFixed(2)}% · ₹
              {(newCtcNum - oldCtc).toLocaleString("en-IN")} per year
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Effective date *</Label>
              <Input
                type="date"
                value={effective}
                onChange={(e) => setEffective(e.target.value)}
              />
              {effective < todayStr && (
                <p className="text-xs text-brand-brown-light mt-1">
                  Back-dated — allowed unless payroll for that period is
                  already finalized/paid.
                </p>
              )}
            </div>
            <div>
              <Label>Reason</Label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {REVISION_REASONS.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <Label>Salary template</Label>
            <select
              value={templateId}
              onChange={(e) => setTemplateId(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">Keep current template</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.template_code} · {t.template_name}
                  {t.id === currentTemplateId ? " (current)" : ""}
                </option>
              ))}
            </select>
            <p className="text-xs text-brand-brown-light mt-1">
              {templateChanged
                ? "Template will switch when this revision is applied. The old template stays on every prior payslip/revision record."
                : "Leave as current unless this revision also changes the salary structure."}
            </p>
          </div>
          <div>
            <Label>Notes</Label>
            <Input
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional context"
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="accent-brand-gold-dark"
              checked={autoApply}
              onChange={(e) => setAutoApply(e.target.checked)}
            />
            Apply immediately (skip approval queue)
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              disabled={!valid || submit.isPending}
              onClick={() => submit.mutate()}
            >
              {submit.isPending
                ? "Saving…"
                : autoApply
                  ? "Apply revision"
                  : "Save draft"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
