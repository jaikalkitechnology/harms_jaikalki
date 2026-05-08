import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  BadgeCheck,
  Building,
  Calendar,
  Clock,
  FileText,
  KeyRound,
  Mail,
  Pencil,
  Phone,
  ScrollText,
  ShieldOff,
  ShieldCheck,
  User,
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
import {
  employeesApi,
  salaryTemplatesApi,
  type SalaryBreakup,
} from "@/lib/api/employees";
import { payrollApi, type GeneratedDocument } from "@/lib/api/payroll";
import { launchApi } from "@/lib/api/launch";
import { CategoryBadge } from "./CategoryBadge";
import { fmtIstDate } from "@/lib/datetime";

export default function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const employeeId = Number(id);
  const queryClient = useQueryClient();

  const { data: employee, isLoading } = useQuery({
    queryKey: ["employee", employeeId],
    queryFn: () => employeesApi.get(employeeId),
    enabled: Number.isFinite(employeeId),
  });

  const { data: breakup } = useQuery({
    queryKey: ["salary-breakup", employee?.salary_template?.id, employee?.ctc_annual],
    queryFn: () =>
      salaryTemplatesApi.calculate(
        employee!.salary_template!.id,
        Number(employee!.ctc_annual),
      ),
    enabled: !!employee?.salary_template,
  });

  const confirmMutation = useMutation({
    mutationFn: () => employeesApi.confirm(employeeId, null),
    onSuccess: () => {
      toast.success("Employee confirmed");
      queryClient.invalidateQueries({ queryKey: ["employee", employeeId] });
      queryClient.invalidateQueries({ queryKey: ["employees"] });
    },
    onError: () => toast.error("Failed to confirm"),
  });

  const [editOpen, setEditOpen] = useState(false);
  const [credentialOpen, setCredentialOpen] = useState(false);

  const [extendMonths, setExtendMonths] = useState(2);
  const [extendReason, setExtendReason] = useState("");
  const extendMutation = useMutation({
    mutationFn: () =>
      employeesApi.extendProbation(employeeId, extendMonths, extendReason),
    onSuccess: () => {
      toast.success("Probation extended");
      setExtendReason("");
      queryClient.invalidateQueries({ queryKey: ["employee", employeeId] });
    },
    onError: () => toast.error("Failed to extend probation"),
  });

  const resignationUnlock = useMutation({
    mutationFn: (unlocked: boolean) =>
      launchApi.setResignationUnlock(employeeId, unlocked),
    onSuccess: (r) => {
      toast.success(
        r.resignation_unlocked
          ? "Resignation submission unlocked for this employee"
          : "Resignation submission locked again",
      );
      queryClient.invalidateQueries({ queryKey: ["employee", employeeId] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not toggle"),
  });

  if (isLoading || !employee) return <LoadingScreen label="Loading employee…" />;

  const probationDaysLeft = employee.probation_end_date
    ? Math.ceil(
        (new Date(employee.probation_end_date).getTime() - Date.now()) /
          (1000 * 60 * 60 * 24),
      )
    : null;

  return (
    <div className="space-y-6">
      <button
        onClick={() => navigate("/employees")}
        className="flex items-center gap-2 text-sm text-brand-brown-light hover:text-brand-brown-darker"
      >
        <ArrowLeft className="h-4 w-4" /> Back to directory
      </button>

      <div className="flex items-start gap-6 flex-wrap">
        <div className="h-24 w-24 rounded-2xl bg-brand-gold/15 grid place-items-center text-brand-brown-darker shrink-0">
          {employee.photo_url ? (
            <img
              src={employee.photo_url}
              alt=""
              className="h-full w-full object-cover rounded-2xl"
            />
          ) : (
            <User className="h-10 w-10" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ {employee.employee_code}
          </div>
          <h1 className="font-display text-3xl font-bold text-brand-brown-darker">
            {employee.first_name} {employee.last_name}
          </h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-brand-brown-light">
            {employee.designation && <span>{employee.designation.name}</span>}
            {employee.department && <span>· {employee.department.name}</span>}
          </div>
          <div className="mt-3 flex items-center gap-2">
            <CategoryBadge code={employee.category?.code} />
            {employee.is_on_probation ? (
              <span className="text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded bg-warning/10 text-warning">
                On Probation
                {probationDaysLeft !== null &&
                  ` · ${probationDaysLeft} days left`}
              </span>
            ) : (
              <span className="text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded bg-success/10 text-success">
                Confirmed
              </span>
            )}
          </div>
        </div>
        <PermissionGate permission="employee.update">
          <div className="flex flex-col gap-2 shrink-0">
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => setEditOpen(true)}
            >
              <Pencil className="size-4" /> Edit
            </Button>
            <Button
              variant="outline"
              className="gap-2"
              onClick={() => setCredentialOpen(true)}
            >
              <KeyRound className="size-4" /> Credentials
            </Button>
          </div>
        </PermissionGate>
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Work info</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row icon={Building} label="Department" value={employee.department?.name} />
            <Row icon={BadgeCheck} label="Designation" value={employee.designation?.name} />
            <Row
              icon={Calendar}
              label="Date of joining"
              value={employee.date_of_joining}
            />
            <Row
              icon={Clock}
              label="Probation ends"
              value={employee.probation_end_date}
            />
            <Row
              icon={Calendar}
              label="Confirmed on"
              value={employee.confirmation_date ?? "—"}
            />
            <Row icon={Building} label="Work location" value={employee.work_location} />
            <Row icon={Building} label="Work mode" value={employee.work_mode} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Contact</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row icon={Mail} label="Personal email" value={employee.personal_email} />
            <Row icon={Phone} label="Personal phone" value={employee.personal_phone} />
            <Row icon={User} label="Date of birth" value={employee.date_of_birth} />
            <Row icon={User} label="Gender" value={employee.gender} />
            <Row icon={User} label="Marital status" value={employee.marital_status} />
            <Row icon={User} label="Blood group" value={employee.blood_group} />
          </CardContent>
        </Card>

        <PermissionGate permission="salary.view.team">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>
                Salary <span className="display-em">breakup</span>
              </CardTitle>
              <CardDescription>
                {employee.salary_template?.template_name ?? "No template"}
                {breakup &&
                  ` · CTC ₹${(breakup.total_ctc_annual / 100000).toFixed(2)}L`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!breakup ? (
                <p className="text-sm text-brand-brown-light">
                  No salary template assigned.
                </p>
              ) : breakup.is_intern ? (
                <div className="space-y-2">
                  <p className="text-sm">
                    Intern — receives travel reimbursement only (max ₹
                    {breakup.travel_expense_max.toLocaleString()}/mo).
                  </p>
                </div>
              ) : (
                <SalaryGrid breakup={breakup} />
              )}
            </CardContent>
          </Card>
        </PermissionGate>

        <PermissionGate permission="employee.create">
          <DocumentsCard employeeId={employee.id} />
        </PermissionGate>

        {editOpen && (
          <EditEmployeeModal
            employee={employee}
            onClose={() => setEditOpen(false)}
            onSaved={() => {
              setEditOpen(false);
              queryClient.invalidateQueries({
                queryKey: ["employee", employeeId],
              });
              queryClient.invalidateQueries({ queryKey: ["employees"] });
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

        {employee.is_on_probation && (
          <PermissionGate permission="employee.update">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>
                  Probation <span className="display-em">actions</span>
                </CardTitle>
                <CardDescription>
                  HR can confirm the employee or extend the probation by up to 2 months.
                </CardDescription>
              </CardHeader>
              <CardContent className="grid md:grid-cols-2 gap-6">
                <div>
                  <Label className="mb-2 block">Confirm</Label>
                  <Button
                    onClick={() => confirmMutation.mutate()}
                    disabled={confirmMutation.isPending}
                  >
                    Mark as confirmed
                  </Button>
                </div>
                <div>
                  <Label className="mb-2 block">Extend probation</Label>
                  <div className="space-y-2">
                    <div className="flex gap-2 items-center">
                      <Input
                        type="number"
                        min={1}
                        max={6}
                        value={extendMonths}
                        onChange={(e) =>
                          setExtendMonths(Number(e.target.value || 1))
                        }
                        className="w-20"
                      />
                      <span className="text-sm text-brand-brown-light">months</span>
                    </div>
                    <Input
                      placeholder="Reason for extension"
                      value={extendReason}
                      onChange={(e) => setExtendReason(e.target.value)}
                    />
                    <Button
                      variant="outline"
                      onClick={() => extendMutation.mutate()}
                      disabled={
                        extendMutation.isPending || extendReason.length < 5
                      }
                    >
                      Extend probation
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </PermissionGate>
        )}

        <PermissionGate permission="approval.act">
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>
                Resignation <span className="display-em">access</span>
              </CardTitle>
              <CardDescription>
                Resignation submission from the mobile app is locked by
                default. Toggle this on when the employee has formally
                requested to resign (e.g. via email). The lock auto-resets
                once they submit, so this is a one-shot per request.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center justify-between gap-3">
              <div className="text-sm">
                Current state:{" "}
                {employee.resignation_unlocked ? (
                  <span className="font-semibold text-success">
                    Unlocked — employee can submit
                  </span>
                ) : (
                  <span className="font-semibold text-brand-brown-light">
                    Locked
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant={
                    employee.resignation_unlocked ? "outline" : "default"
                  }
                  onClick={() => resignationUnlock.mutate(true)}
                  disabled={
                    resignationUnlock.isPending || employee.resignation_unlocked
                  }
                >
                  Unlock submission
                </Button>
                <Button
                  variant="outline"
                  onClick={() => resignationUnlock.mutate(false)}
                  disabled={
                    resignationUnlock.isPending ||
                    !employee.resignation_unlocked
                  }
                >
                  Lock again
                </Button>
              </div>
            </CardContent>
          </Card>
        </PermissionGate>
      </div>
    </div>
  );
}

function Row({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="flex items-start gap-3">
      <Icon className="h-4 w-4 text-brand-gold-dark mt-0.5" />
      <div className="min-w-0">
        <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
          {label}
        </div>
        <div className="text-brand-brown-darker">{value || "—"}</div>
      </div>
    </div>
  );
}

function SalaryGrid({ breakup }: { breakup: SalaryBreakup }) {
  const inr = (n: number) => `₹${n.toLocaleString("en-IN")}`;
  const earnings = (
    [
      ["Basic", breakup.basic],
      ["HRA", breakup.hra],
      ["Other Allowance", breakup.other_allowance],
      ["Special Allowance", breakup.special_allowance],
      ["Conveyance", breakup.conveyance],
      ["Medical Allowance", breakup.medical_allowance],
      ["LTA", breakup.lta],
      ["Food Coupon", breakup.food_coupon],
    ] as [string, number][]
  ).filter(([, v]) => v > 0);

  return (
    <div className="grid md:grid-cols-3 gap-6 text-sm">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-2">
          Earnings (monthly)
        </div>
        <dl className="space-y-1.5">
          {earnings.map(([k, v]) => (
            <div key={k} className="flex justify-between">
              <dt className="text-brand-brown-light">{k}</dt>
              <dd className="font-medium">{inr(v)}</dd>
            </div>
          ))}
          <div className="flex justify-between pt-2 border-t border-brand-brown-100 font-semibold">
            <dt>Gross</dt>
            <dd>{inr(breakup.gross)}</dd>
          </div>
        </dl>
      </div>

      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-2">
          Deductions
        </div>
        <dl className="space-y-1.5">
          <div className="flex justify-between">
            <dt className="text-brand-brown-light">PF (Employee)</dt>
            <dd>{inr(breakup.pf_employee)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-brand-brown-light">ESIC (Employee)</dt>
            <dd>{inr(breakup.esic_employee)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-brand-brown-light">Professional Tax</dt>
            <dd>{inr(breakup.professional_tax)}</dd>
          </div>
          <div className="flex justify-between pt-2 border-t border-brand-brown-100 font-semibold">
            <dt>Total</dt>
            <dd>{inr(breakup.total_deductions)}</dd>
          </div>
          <div className="flex justify-between pt-2 border-t border-brand-brown-100 text-brand-gold-dark font-semibold">
            <dt>Net Salary</dt>
            <dd>{inr(breakup.net_salary)}</dd>
          </div>
        </dl>
      </div>

      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-2">
          Employer cost
        </div>
        <dl className="space-y-1.5">
          <div className="flex justify-between">
            <dt className="text-brand-brown-light">PF (Employer)</dt>
            <dd>{inr(breakup.pf_employer)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-brand-brown-light">ESIC (Employer)</dt>
            <dd>{inr(breakup.esic_employer)}</dd>
          </div>
          <div className="flex justify-between pt-2 border-t border-brand-brown-100 font-semibold">
            <dt>CTC / month</dt>
            <dd>{inr(breakup.total_ctc_monthly)}</dd>
          </div>
          <div className="flex justify-between pt-2 border-t border-brand-brown-100 text-brand-gold-dark font-semibold">
            <dt>CTC / year</dt>
            <dd>{inr(breakup.total_ctc_annual)}</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}

function DocumentsCard({ employeeId }: { employeeId: number }) {
  const queryClient = useQueryClient();
  const { data: documents = [] } = useQuery({
    queryKey: ["employee-documents", employeeId],
    queryFn: () => payrollApi.listEmployeeDocuments(employeeId),
  });

  const generateOffer = useMutation({
    mutationFn: () => payrollApi.generateOfferLetter(employeeId),
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
    mutationFn: () => payrollApi.generateConfirmationLetter(employeeId),
    onSuccess: (doc) => {
      toast.success(`Confirmation letter ${doc.letter_number} generated`);
      queryClient.invalidateQueries({ queryKey: ["employee-documents"] });
    },
  });

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>
          Letters & <span className="display-em">documents</span>
        </CardTitle>
        <CardDescription>
          Offer letter follows the Jaikalki <code className="font-mono">JKT/HR/AL/&lt;seq&gt;/&lt;year&gt;</code> format.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
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
              href={payrollApi.offerLetterPreviewUrl(employeeId)}
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
        </div>
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
  });

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
      }),
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
              Editable details. Department / designation / salary changes go
              through the Salary Revisions flow.
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
          <div className="md:col-span-2 flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              disabled={
                !draft.first_name ||
                !draft.last_name ||
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
