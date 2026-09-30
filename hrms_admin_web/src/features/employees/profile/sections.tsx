// Profile sections built on employee fields (PUT /employees/{id}). Each
// one reads as a label/value grid and switches to its own small form.
import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Copy, Mail, Phone } from "lucide-react";
import { toast } from "sonner";

import { Input } from "@/components/ui/input";
import {
  employeesApi,
  lookupsApi,
  salaryTemplatesApi,
  type EmployeeDetail,
  type SalaryBreakup,
} from "@/lib/api/employees";
import {
  Field,
  FormActions,
  InfoGrid,
  InfoItem,
  SELECT_CLASS,
  SectionCard,
  age,
  fmtDate,
  tenure,
  titleCase,
  useSaveEmployee,
} from "./ui";

const EMPLOYMENT_TYPES = ["full_time", "part_time", "contract", "intern"];
const WORK_MODES = ["office", "hybrid", "remote", "field"];
const inr = (n: number) => `₹${Math.round(n).toLocaleString("en-IN")}`;

function withCurrent(options: string[], current: string | null | undefined) {
  return current && !options.includes(current) ? [...options, current] : options;
}

// ── Job & placement ────────────────────────────────────────────────────
export function JobSection({ employee }: { employee: EmployeeDetail }) {
  const [editing, setEditing] = useState(false);
  const { data: managers = [] } = useQuery({
    queryKey: ["employees-as-managers"],
    queryFn: () => employeesApi.list(),
  });
  const manager = managers.find((m) => m.id === employee.reporting_to);
  const exited = employee.exit_date && employee.status !== "active";

  return (
    <SectionCard
      title="Job & placement"
      description="Where this person sits in the organisation."
      onEdit={() => setEditing(true)}
      editing={editing}
    >
      {editing ? (
        <JobForm employee={employee} onDone={() => setEditing(false)} />
      ) : (
        <InfoGrid cols={3}>
          <InfoItem label="Employee code" value={employee.employee_code} mono />
          <InfoItem label="Category" value={employee.category?.name} />
          <InfoItem
            label="Employment type"
            value={titleCase(employee.employment_type)}
          />
          <InfoItem
            label="Department"
            value={employee.department?.name}
            onAdd={() => setEditing(true)}
          />
          <InfoItem
            label="Designation"
            value={employee.designation?.name}
            onAdd={() => setEditing(true)}
          />
          <InfoItem
            label="Reports to"
            value={
              manager && (
                <Link
                  to={`/employees/${manager.id}`}
                  className="text-brand-gold-dark hover:underline"
                >
                  {manager.first_name} {manager.last_name}
                </Link>
              )
            }
            hint={manager?.employee_code}
            onAdd={() => setEditing(true)}
          />
          <InfoItem
            label="Date of joining"
            value={fmtDate(employee.date_of_joining)}
            hint={tenure(employee.date_of_joining, exited ? employee.exit_date : null)}
          />
          <InfoItem label="Work mode" value={titleCase(employee.work_mode)} />
          <InfoItem label="Work location" value={employee.work_location} />
        </InfoGrid>
      )}
    </SectionCard>
  );
}

function JobForm({
  employee,
  onDone,
}: {
  employee: EmployeeDetail;
  onDone: () => void;
}) {
  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: lookupsApi.departments,
  });
  const { data: designations = [] } = useQuery({
    queryKey: ["designations"],
    queryFn: lookupsApi.designations,
  });
  const { data: managers = [] } = useQuery({
    queryKey: ["employees-as-managers"],
    queryFn: () => employeesApi.list(),
  });
  const [d, setD] = useState({
    department_id: employee.department?.id ? String(employee.department.id) : "",
    designation_id: employee.designation?.id ? String(employee.designation.id) : "",
    reporting_to: employee.reporting_to ? String(employee.reporting_to) : "",
    date_of_joining: employee.date_of_joining ?? "",
    employment_type: employee.employment_type ?? "full_time",
    work_mode: employee.work_mode ?? "office",
    work_location: employee.work_location ?? "",
  });
  const save = useSaveEmployee(employee.id, "Job details saved");
  const dojChanged =
    !!d.date_of_joining && d.date_of_joining !== (employee.date_of_joining ?? "");

  const submit = () =>
    save.mutate(
      {
        department_id: d.department_id ? Number(d.department_id) : null,
        designation_id: d.designation_id ? Number(d.designation_id) : null,
        reporting_to: d.reporting_to ? Number(d.reporting_to) : null,
        employment_type: d.employment_type,
        work_mode: d.work_mode,
        work_location: d.work_location,
        ...(dojChanged ? { date_of_joining: d.date_of_joining } : {}),
      },
      { onSuccess: onDone },
    );

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Field label="Department">
        <select
          className={SELECT_CLASS}
          value={d.department_id}
          onChange={(e) => setD({ ...d, department_id: e.target.value })}
        >
          <option value="">—</option>
          {departments.map((x) => (
            <option key={x.id} value={x.id}>
              {x.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Designation">
        <select
          className={SELECT_CLASS}
          value={d.designation_id}
          onChange={(e) => setD({ ...d, designation_id: e.target.value })}
        >
          <option value="">—</option>
          {designations.map((x) => (
            <option key={x.id} value={x.id}>
              {x.name} (L{x.level})
            </option>
          ))}
        </select>
      </Field>
      <Field label="Reports to">
        <select
          className={SELECT_CLASS}
          value={d.reporting_to}
          onChange={(e) => setD({ ...d, reporting_to: e.target.value })}
        >
          <option value="">—</option>
          {managers
            .filter((m) => m.id !== employee.id)
            .map((m) => (
              <option key={m.id} value={m.id}>
                {m.first_name} {m.last_name} · {m.employee_code}
              </option>
            ))}
        </select>
      </Field>
      <Field
        label="Date of joining"
        help={
          dojChanged ? (
            <span className="text-warning">
              Moves the open intern / probation period by the same number of
              days. Blocked if a finalized payroll already pays a month before
              the new date.
            </span>
          ) : undefined
        }
      >
        <Input
          type="date"
          value={d.date_of_joining}
          onChange={(e) => setD({ ...d, date_of_joining: e.target.value })}
        />
      </Field>
      <Field label="Employment type">
        <select
          className={SELECT_CLASS}
          value={d.employment_type}
          onChange={(e) => setD({ ...d, employment_type: e.target.value })}
        >
          {withCurrent(EMPLOYMENT_TYPES, employee.employment_type).map((t) => (
            <option key={t} value={t}>
              {titleCase(t)}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Work mode">
        <select
          className={SELECT_CLASS}
          value={d.work_mode}
          onChange={(e) => setD({ ...d, work_mode: e.target.value })}
        >
          {withCurrent(WORK_MODES, employee.work_mode).map((t) => (
            <option key={t} value={t}>
              {titleCase(t)}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Work location" className="sm:col-span-2 lg:col-span-3">
        <Input
          value={d.work_location}
          onChange={(e) => setD({ ...d, work_location: e.target.value })}
        />
      </Field>
      <FormActions
        onCancel={onDone}
        onSave={submit}
        saving={save.isPending}
        disabled={!d.date_of_joining || !d.work_location}
      />
    </div>
  );
}

// ── Personal details ───────────────────────────────────────────────────
export function PersonalSection({ employee }: { employee: EmployeeDetail }) {
  const [editing, setEditing] = useState(false);
  const [d, setD] = useState(() => draftOf(employee));
  const save = useSaveEmployee(employee.id, "Personal details saved");
  const open = () => {
    setD(draftOf(employee));
    setEditing(true);
  };

  return (
    <SectionCard
      title="Personal details"
      onEdit={open}
      editing={editing}
    >
      {editing ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="First name">
            <Input
              value={d.first_name}
              onChange={(e) => setD({ ...d, first_name: e.target.value })}
            />
          </Field>
          <Field label="Last name">
            <Input
              value={d.last_name}
              onChange={(e) => setD({ ...d, last_name: e.target.value })}
            />
          </Field>
          <Field label="Date of birth">
            <Input
              type="date"
              value={d.date_of_birth}
              onChange={(e) => setD({ ...d, date_of_birth: e.target.value })}
            />
          </Field>
          <Field label="Gender">
            <select
              className={SELECT_CLASS}
              value={d.gender}
              onChange={(e) => setD({ ...d, gender: e.target.value })}
            >
              <option value="">—</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </Field>
          <Field label="Marital status">
            <select
              className={SELECT_CLASS}
              value={d.marital_status}
              onChange={(e) => setD({ ...d, marital_status: e.target.value })}
            >
              <option value="">—</option>
              <option value="single">Single</option>
              <option value="married">Married</option>
              <option value="divorced">Divorced</option>
              <option value="widowed">Widowed</option>
            </select>
          </Field>
          <Field label="Blood group">
            <select
              className={SELECT_CLASS}
              value={d.blood_group}
              onChange={(e) => setD({ ...d, blood_group: e.target.value })}
            >
              <option value="">—</option>
              {Array.from(
                new Set([
                  "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-",
                  ...(d.blood_group ? [d.blood_group] : []),
                ]),
              ).map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </Field>
          <FormActions
            onCancel={() => setEditing(false)}
            saving={save.isPending}
            disabled={!d.first_name.trim() || !d.last_name.trim()}
            onSave={() =>
              save.mutate(
                {
                  first_name: d.first_name.trim(),
                  last_name: d.last_name.trim(),
                  date_of_birth: d.date_of_birth || null,
                  gender: d.gender || null,
                  marital_status: d.marital_status || null,
                  blood_group: d.blood_group || null,
                },
                { onSuccess: () => setEditing(false) },
              )
            }
          />
        </div>
      ) : (
        <InfoGrid>
          <InfoItem
            label="Full name"
            value={`${employee.first_name} ${employee.last_name}`}
          />
          <InfoItem
            label="Date of birth"
            value={fmtDate(employee.date_of_birth)}
            hint={age(employee.date_of_birth)}
            onAdd={open}
          />
          <InfoItem label="Gender" value={titleCase(employee.gender)} onAdd={open} />
          <InfoItem
            label="Marital status"
            value={titleCase(employee.marital_status)}
            onAdd={open}
          />
          <InfoItem label="Blood group" value={employee.blood_group} onAdd={open} />
        </InfoGrid>
      )}
    </SectionCard>
  );
}

function draftOf(e: EmployeeDetail) {
  return {
    first_name: e.first_name,
    last_name: e.last_name,
    date_of_birth: e.date_of_birth ?? "",
    gender: e.gender ?? "",
    marital_status: e.marital_status ?? "",
    blood_group: e.blood_group ?? "",
  };
}

// ── Contact ────────────────────────────────────────────────────────────
export function ContactSection({ employee }: { employee: EmployeeDetail }) {
  const [editing, setEditing] = useState(false);
  const [email, setEmail] = useState(employee.personal_email ?? "");
  const [phone, setPhone] = useState(employee.personal_phone ?? "");
  const save = useSaveEmployee(employee.id, "Contact details saved");
  const open = () => {
    setEmail(employee.personal_email ?? "");
    setPhone(employee.personal_phone ?? "");
    setEditing(true);
  };

  return (
    <SectionCard title="Contact" onEdit={open} editing={editing}>
      {editing ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Personal email">
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </Field>
          <Field label="Personal phone">
            <Input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </Field>
          <FormActions
            onCancel={() => setEditing(false)}
            saving={save.isPending}
            onSave={() =>
              save.mutate(
                {
                  personal_email: email.trim() || null,
                  personal_phone: phone.trim() || null,
                },
                { onSuccess: () => setEditing(false) },
              )
            }
          />
        </div>
      ) : (
        <InfoGrid>
          <InfoItem
            label="Personal email"
            value={
              employee.personal_email && (
                <ContactValue
                  href={`mailto:${employee.personal_email}`}
                  icon={<Mail className="h-3.5 w-3.5" />}
                  text={employee.personal_email}
                />
              )
            }
            onAdd={open}
          />
          <InfoItem
            label="Personal phone"
            value={
              employee.personal_phone && (
                <ContactValue
                  href={`tel:${employee.personal_phone}`}
                  icon={<Phone className="h-3.5 w-3.5" />}
                  text={employee.personal_phone}
                />
              )
            }
            onAdd={open}
          />
        </InfoGrid>
      )}
    </SectionCard>
  );
}

export function ContactValue({
  href,
  icon,
  text,
}: {
  href: string;
  icon: ReactNode;
  text: string;
}) {
  return (
    <span className="inline-flex max-w-full items-center gap-1.5">
      <a
        href={href}
        className="inline-flex min-w-0 items-center gap-1.5 hover:text-brand-gold-dark"
      >
        {icon && <span className="shrink-0 text-brand-brown-light">{icon}</span>}
        <span className="truncate">{text}</span>
      </a>
      <button
        type="button"
        title="Copy"
        aria-label={`Copy ${text}`}
        className="shrink-0 rounded p-0.5 text-brand-brown-light hover:text-brand-brown-darker"
        onClick={() => {
          navigator.clipboard
            ?.writeText(text)
            .then(() => toast.success("Copied"))
            .catch(() => toast.error("Could not copy"));
        }}
      >
        <Copy className="h-3 w-3" />
      </button>
    </span>
  );
}

// ── Salary structure ───────────────────────────────────────────────────
export function SalarySection({ employee }: { employee: EmployeeDetail }) {
  const [editing, setEditing] = useState(false);
  const { data: breakup } = useQuery({
    queryKey: [
      "salary-breakup",
      employee.salary_template?.id,
      employee.ctc_annual,
      employee.id,
      employee.pf_opt_out,
      employee.pf_basic_cap_override,
      employee.esic_force_exempt,
      employee.pt_state,
    ],
    queryFn: () =>
      salaryTemplatesApi.calculate(
        employee.salary_template!.id,
        Number(employee.ctc_annual),
        employee.id,
      ),
    enabled: !!employee.salary_template,
  });

  const ctc = Number(employee.ctc_annual || 0);
  return (
    <SectionCard
      title="Salary structure"
      description={
        employee.salary_template
          ? `${employee.salary_template.template_code} · ${employee.salary_template.template_name}`
          : "No salary template assigned"
      }
      onEdit={() => setEditing(true)}
      editing={editing}
    >
      {editing ? (
        <SalaryForm employee={employee} onDone={() => setEditing(false)} />
      ) : !employee.salary_template ? (
        <InfoGrid>
          <InfoItem label="Salary template" value="" onAdd={() => setEditing(true)} />
          <InfoItem label="Annual CTC" value={ctc ? inr(ctc) : ""} />
        </InfoGrid>
      ) : !breakup ? (
        <p className="text-sm text-brand-brown-light">Calculating…</p>
      ) : breakup.is_intern ? (
        <InternPay breakup={breakup} />
      ) : (
        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-3">
            <Stat label="Annual CTC" value={inr(breakup.total_ctc_annual)} strong />
            <Stat label="Monthly gross" value={inr(breakup.gross)} />
            <Stat label="Monthly take-home" value={inr(breakup.net_salary)} />
          </div>
          <SalaryGrid breakup={breakup} />
        </div>
      )}
    </SectionCard>
  );
}

function SalaryForm({
  employee,
  onDone,
}: {
  employee: EmployeeDetail;
  onDone: () => void;
}) {
  const { data: templates = [] } = useQuery({
    queryKey: ["salary-templates"],
    queryFn: () => salaryTemplatesApi.list(),
  });
  const [templateId, setTemplateId] = useState(
    employee.salary_template?.id ? String(employee.salary_template.id) : "",
  );
  const [ctc, setCtc] = useState(employee.ctc_annual ?? "");
  const save = useSaveEmployee(employee.id, "Salary structure saved");
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Field label="Salary template">
        <select
          className={SELECT_CLASS}
          value={templateId}
          onChange={(e) => setTemplateId(e.target.value)}
        >
          <option value="">—</option>
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.template_code} · {t.template_name}
            </option>
          ))}
        </select>
      </Field>
      <Field
        label="Annual CTC (₹)"
        help="For corrections only. Use New revision under Compensation history for raises so they are tracked."
      >
        <Input
          type="number"
          min={0}
          step={1}
          value={ctc}
          onChange={(e) => setCtc(e.target.value)}
        />
      </Field>
      <FormActions
        onCancel={onDone}
        saving={save.isPending}
        onSave={() =>
          save.mutate(
            {
              salary_template_id: templateId ? Number(templateId) : null,
              ctc_annual: ctc === "" ? null : Number(ctc),
            },
            { onSuccess: onDone },
          )
        }
      />
    </div>
  );
}

function InternPay({ breakup }: { breakup: SalaryBreakup }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Stat
        label="Pay type"
        value={breakup.is_paid_internship ? "Paid internship" : "Unpaid internship"}
      />
      <Stat
        label="Travel reimbursement"
        value={`Up to ${inr(breakup.travel_expense_max)} / month`}
      />
      {breakup.is_paid_internship && breakup.gross > 0 && (
        <Stat label="Monthly stipend" value={inr(breakup.gross)} strong />
      )}
      <p className="text-xs text-brand-brown-light sm:col-span-2">
        Interns are paid through the intern reimbursement flow, not the
        monthly payroll run.
      </p>
    </div>
  );
}

function Stat({
  label,
  value,
  strong = false,
}: {
  label: string;
  value: string;
  strong?: boolean;
}) {
  return (
    <div className="rounded-xl border border-brand-brown-50 bg-brand-brown-50/30 px-4 py-3">
      <div className="text-[11px] font-medium uppercase tracking-[0.12em] text-brand-brown-light">
        {label}
      </div>
      <div
        className={
          strong
            ? "mt-1 font-display text-2xl font-bold text-brand-gold-dark"
            : "mt-1 text-lg font-semibold text-brand-brown-darker"
        }
      >
        {value}
      </div>
    </div>
  );
}

function SalaryGrid({ breakup }: { breakup: SalaryBreakup }) {
  const earnings = (
    [
      ["Basic", breakup.basic],
      ["HRA", breakup.hra],
      ["Other allowance", breakup.other_allowance],
      ["Special allowance", breakup.special_allowance],
      ["Conveyance", breakup.conveyance],
      ["Medical allowance", breakup.medical_allowance],
      ["LTA", breakup.lta],
      ["Food coupon", breakup.food_coupon],
    ] as [string, number][]
  ).filter(([, v]) => v > 0);

  return (
    <div className="grid gap-6 text-sm md:grid-cols-3">
      <Column
        title="Earnings · monthly"
        rows={earnings}
        total={["Gross", breakup.gross]}
      />
      <Column
        title="Deductions · monthly"
        rows={[
          ["PF (employee)", breakup.pf_employee],
          ["ESIC (employee)", breakup.esic_employee],
          ["Professional tax", breakup.professional_tax],
        ]}
        total={["Total", breakup.total_deductions]}
        highlight={["Net salary", breakup.net_salary]}
      />
      <Column
        title="Employer cost · monthly"
        rows={[
          ["PF (employer)", breakup.pf_employer],
          ["ESIC (employer)", breakup.esic_employer],
        ]}
        total={["CTC / month", breakup.total_ctc_monthly]}
        highlight={["CTC / year", breakup.total_ctc_annual]}
      />
    </div>
  );
}

function Column({
  title,
  rows,
  total,
  highlight,
}: {
  title: string;
  rows: [string, number][];
  total: [string, number];
  highlight?: [string, number];
}) {
  return (
    <div>
      <div className="mb-2 text-[11px] font-medium uppercase tracking-[0.12em] text-brand-brown-light">
        {title}
      </div>
      <dl className="space-y-1.5">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-2">
            <dt className="text-brand-brown-light">{k}</dt>
            <dd className="font-medium tabular-nums">{inr(v)}</dd>
          </div>
        ))}
        <div className="flex justify-between border-t border-brand-brown-100 pt-2 font-semibold">
          <dt>{total[0]}</dt>
          <dd className="tabular-nums">{inr(total[1])}</dd>
        </div>
        {highlight && (
          <div className="flex justify-between font-semibold text-brand-gold-dark">
            <dt>{highlight[0]}</dt>
            <dd className="tabular-nums">{inr(highlight[1])}</dd>
          </div>
        )}
      </dl>
    </div>
  );
}
