import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Eye, EyeOff, Pencil, Plus, Trash2, X } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { type EmployeeDetail } from "@/lib/api/employees";
import {
  attendanceCyclesApi,
  bankApi,
  employeeProfileApi,
  type AttendanceCycle,
  type AttendanceCycleInput,
  type BankDetailsInput,
  type FamilyMember,
  type FamilyMemberInput,
  type Nominee,
  type NomineeInput,
  type NomineeType,
  type PassportInput,
} from "@/lib/api/employeeProfile";
import {
  Chip,
  EmptyState,
  Field,
  FormActions,
  InfoGrid,
  InfoItem,
  SELECT_CLASS,
  SectionCard,
  daysUntil,
  errDetail,
  fmtDate,
  titleCase,
  useCanEdit,
  useSaveEmployee,
} from "./profile/ui";

const RELATIONS = ["spouse", "child", "father", "mother", "sibling", "other"];

function useInvalidateCompleteness(employeeId: number) {
  const qc = useQueryClient();
  return () =>
    qc.invalidateQueries({ queryKey: ["employee-completeness", employeeId] });
}

// ── Statutory IDs + Insurance + Attendance cycle ───────────────────────
export function StatutoryIdsCard({ employee }: { employee: EmployeeDetail }) {
  const [editing, setEditing] = useState(false);
  const [manageCyclesOpen, setManageCyclesOpen] = useState(false);
  const { data: cycles = [] } = useQuery({
    queryKey: ["attendance-cycles"],
    queryFn: () => attendanceCyclesApi.list(),
  });
  const cycleStart = employee.attendance_cycle_start_day || 1;
  const cycleName =
    cycles.find((c) => c.start_day === cycleStart)?.name ??
    (cycleStart === 1 ? "Calendar month" : `From day ${cycleStart}`);

  return (
    <SectionCard
      title="Statutory IDs & insurance"
      description="PF / UAN / ESIC numbers, group insurance and the attendance cycle."
      onEdit={() => setEditing(true)}
      editing={editing}
    >
      {editing ? (
        <StatutoryIdsForm
          employee={employee}
          cycles={cycles}
          onManageCycles={() => setManageCyclesOpen(true)}
          onDone={() => setEditing(false)}
        />
      ) : (
        <InfoGrid cols={3}>
          <InfoItem
            label="UAN"
            value={employee.uan_number}
            mono
            onAdd={() => setEditing(true)}
            hint={
              employee.uan_number && !/^\d{12}$/.test(employee.uan_number) ? (
                <span className="text-error">Must be 12 digits</span>
              ) : undefined
            }
          />
          <InfoItem
            label="PF number"
            value={employee.pf_number}
            mono
            onAdd={() => setEditing(true)}
          />
          <InfoItem
            label="ESIC number"
            value={employee.esic_number}
            mono
            onAdd={() => setEditing(true)}
          />
          <InfoItem
            label="Insurance company"
            value={employee.insurance_company}
            onAdd={() => setEditing(true)}
          />
          <InfoItem
            label="Insurance policy"
            value={employee.insurance_policy_no}
            mono
            onAdd={() => setEditing(true)}
          />
          <InfoItem label="Attendance cycle" value={cycleName} />
        </InfoGrid>
      )}
      {manageCyclesOpen && (
        <ManageCyclesModal onClose={() => setManageCyclesOpen(false)} />
      )}
    </SectionCard>
  );
}

function StatutoryIdsForm({
  employee,
  cycles,
  onManageCycles,
  onDone,
}: {
  employee: EmployeeDetail;
  cycles: AttendanceCycle[];
  onManageCycles: () => void;
  onDone: () => void;
}) {
  const [pf, setPf] = useState(employee.pf_number ?? "");
  const [uan, setUan] = useState(employee.uan_number ?? "");
  const [esic, setEsic] = useState(employee.esic_number ?? "");
  const [insCo, setInsCo] = useState(employee.insurance_company ?? "");
  const [insNo, setInsNo] = useState(employee.insurance_policy_no ?? "");
  const [cycleStart, setCycleStart] = useState<number>(
    employee.attendance_cycle_start_day || 1,
  );
  const save = useSaveEmployee(employee.id, "Statutory IDs saved");

  // Keep a saved cycle visible even if it was deactivated later.
  const options = cycles.map((c) => ({ start_day: c.start_day, label: c.name }));
  if (!options.some((o) => o.start_day === cycleStart)) {
    options.push({ start_day: cycleStart, label: `Day ${cycleStart} (legacy / inactive)` });
  }
  options.sort((a, b) => a.start_day - b.start_day);
  const uanBad = uan !== "" && !/^\d{12}$/.test(uan);

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Field
        label="UAN"
        help={
          uanBad ? (
            <span className="text-error">
              UAN is 12 digits — the PF challan skips invalid ones.
            </span>
          ) : undefined
        }
      >
        <Input
          value={uan}
          inputMode="numeric"
          onChange={(e) => setUan(e.target.value.trim())}
          placeholder="100000000000"
        />
      </Field>
      <Field label="PF number">
        <Input value={pf} onChange={(e) => setPf(e.target.value)} placeholder="MH/BAN/00012345/678" />
      </Field>
      <Field label="ESIC number">
        <Input value={esic} onChange={(e) => setEsic(e.target.value)} placeholder="3100000000" />
      </Field>
      <Field label="Insurance company">
        <Input
          value={insCo}
          onChange={(e) => setInsCo(e.target.value)}
          placeholder="HDFC ERGO General Insurance"
        />
      </Field>
      <Field label="Insurance policy">
        <Input value={insNo} onChange={(e) => setInsNo(e.target.value)} placeholder="2950 1234 5678" />
      </Field>
      <Field
        label="Attendance cycle"
        help="Drives the calendar slice and payroll cut-off for this employee."
      >
        <div className="flex gap-2">
          <select
            value={cycleStart}
            onChange={(e) => setCycleStart(Number(e.target.value))}
            className={SELECT_CLASS}
          >
            {options.map((o) => (
              <option key={o.start_day} value={o.start_day}>
                {o.label}
              </option>
            ))}
          </select>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-10 gap-1"
            onClick={onManageCycles}
          >
            <Pencil className="h-3.5 w-3.5" /> Manage
          </Button>
        </div>
      </Field>
      <FormActions
        onCancel={onDone}
        saving={save.isPending}
        onSave={() =>
          save.mutate(
            {
              pf_number: pf.trim() || null,
              uan_number: uan || null,
              esic_number: esic.trim() || null,
              insurance_company: insCo.trim() || null,
              insurance_policy_no: insNo.trim() || null,
              attendance_cycle_start_day: cycleStart,
            },
            { onSuccess: onDone },
          )
        }
      />
    </div>
  );
}

function ManageCyclesModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const { data: cycles = [] } = useQuery({
    queryKey: ["attendance-cycles", "all"],
    queryFn: () => attendanceCyclesApi.list(false),
  });
  const [adding, setAdding] = useState<AttendanceCycleInput | null>(null);

  const create = useMutation({
    mutationFn: (input: AttendanceCycleInput) => attendanceCyclesApi.create(input),
    onSuccess: () => {
      toast.success("Cycle added");
      qc.invalidateQueries({ queryKey: ["attendance-cycles"] });
      qc.invalidateQueries({ queryKey: ["attendance-cycles", "all"] });
      setAdding(null);
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not add";
      toast.error(detail);
    },
  });
  const update = useMutation({
    mutationFn: ({
      id,
      body,
    }: {
      id: number;
      body: Partial<AttendanceCycleInput>;
    }) => attendanceCyclesApi.update(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["attendance-cycles"] });
      qc.invalidateQueries({ queryKey: ["attendance-cycles", "all"] });
    },
  });
  const del = useMutation({
    mutationFn: (id: number) => attendanceCyclesApi.remove(id),
    onSuccess: () => {
      toast.success("Cycle removed");
      qc.invalidateQueries({ queryKey: ["attendance-cycles"] });
      qc.invalidateQueries({ queryKey: ["attendance-cycles", "all"] });
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not delete";
      toast.error(detail);
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Manage attendance cycles</CardTitle>
            <CardDescription>
              Cycles are shared across the company. Disable instead of
              deleting if a cycle is in use.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {cycles.map((c) => (
            <CycleRow
              key={c.id}
              cycle={c}
              onSave={(body) => update.mutate({ id: c.id, body })}
              onDelete={() => del.mutate(c.id)}
            />
          ))}
          {adding && (
            <CycleRow
              cycle={{ id: -1, ...adding }}
              isNew
              onSave={(body) => create.mutate(body as AttendanceCycleInput)}
              onDelete={() => setAdding(null)}
            />
          )}
          {!adding && (
            <div className="flex justify-between pt-2">
              <Button
                variant="outline"
                className="gap-2"
                onClick={() =>
                  setAdding({
                    code: "",
                    name: "",
                    start_day: 1,
                    description: null,
                    is_default: false,
                    is_active: true,
                  })
                }
              >
                <Plus className="h-4 w-4" /> Add cycle
              </Button>
              <Button onClick={onClose}>Done</Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function CycleRow({
  cycle,
  isNew = false,
  onSave,
  onDelete,
}: {
  cycle: AttendanceCycle;
  isNew?: boolean;
  onSave: (body: Partial<AttendanceCycleInput>) => void;
  onDelete: () => void;
}) {
  const [draft, setDraft] = useState<AttendanceCycleInput>({
    code: cycle.code,
    name: cycle.name,
    start_day: cycle.start_day,
    description: cycle.description,
    is_default: cycle.is_default,
    is_active: cycle.is_active,
  });
  return (
    <div className="rounded-md border border-brand-brown-100/60 p-3 grid grid-cols-1 md:grid-cols-[1fr_2fr_5rem_auto_auto_auto] gap-2 items-end">
      <Field label="Code">
        <Input
          value={draft.code}
          disabled={!isNew}
          onChange={(e) => setDraft({ ...draft, code: e.target.value })}
          placeholder="C11_10"
        />
      </Field>
      <Field label="Name">
        <Input
          value={draft.name}
          onChange={(e) => setDraft({ ...draft, name: e.target.value })}
          placeholder="11th of prev → 10th of current"
        />
      </Field>
      <Field label="Start day">
        <Input
          type="number"
          min={1}
          max={28}
          value={draft.start_day}
          onChange={(e) =>
            setDraft({ ...draft, start_day: Number(e.target.value) })
          }
        />
      </Field>
      <label className="flex items-center gap-1 text-xs">
        <input
          type="checkbox"
          checked={draft.is_default}
          onChange={(e) => setDraft({ ...draft, is_default: e.target.checked })}
        />
        Default
      </label>
      <label className="flex items-center gap-1 text-xs">
        <input
          type="checkbox"
          checked={draft.is_active}
          onChange={(e) => setDraft({ ...draft, is_active: e.target.checked })}
        />
        Active
      </label>
      <div className="flex gap-1">
        <Button
          size="sm"
          onClick={() => onSave(draft)}
          disabled={!draft.code || !draft.name}
        >
          {isNew ? "Add" : "Save"}
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="text-destructive"
          onClick={onDelete}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
}

// ── Bank account ───────────────────────────────────────────────────────
const EMPTY_BANK: BankDetailsInput = {
  account_no: "",
  ifsc: "",
  bank_name: "",
  branch: null,
  account_holder_name: null,
};

export function BankCard({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const refreshCompleteness = useInvalidateCompleteness(employeeId);
  const { data, isLoading } = useQuery({
    queryKey: ["employee-bank", employeeId],
    queryFn: () => bankApi.get(employeeId),
  });
  const [editing, setEditing] = useState(false);
  const [showNo, setShowNo] = useState(false);
  const [draft, setDraft] = useState<BankDetailsInput>(EMPTY_BANK);

  const open = () => {
    setDraft(
      data
        ? {
            account_no: data.account_no,
            ifsc: data.ifsc,
            bank_name: data.bank_name,
            branch: data.branch,
            account_holder_name: data.account_holder_name,
          }
        : EMPTY_BANK,
    );
    setEditing(true);
  };

  const save = useMutation({
    mutationFn: () => bankApi.upsert(employeeId, draft),
    onSuccess: () => {
      toast.success("Bank account saved");
      qc.invalidateQueries({ queryKey: ["employee-bank", employeeId] });
      refreshCompleteness();
      setEditing(false);
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });
  const remove = useMutation({
    mutationFn: () => bankApi.remove(employeeId),
    onSuccess: () => {
      toast.success("Bank account removed");
      qc.invalidateQueries({ queryKey: ["employee-bank", employeeId] });
      refreshCompleteness();
      setEditing(false);
    },
    onError: (e) => toast.error(errDetail(e, "Could not remove")),
  });

  const masked = data?.account_no
    ? showNo
      ? data.account_no
      : `•••• ${data.account_no.slice(-4)}`
    : "";

  return (
    <SectionCard
      title="Bank account"
      description="Salary is credited here; used by the payroll bank file."
      onEdit={data ? open : undefined}
      editing={editing}
    >
      {isLoading ? (
        <p className="text-sm text-brand-brown-light">Loading…</p>
      ) : editing ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Account holder name">
            <Input
              value={draft.account_holder_name ?? ""}
              onChange={(e) =>
                setDraft({ ...draft, account_holder_name: e.target.value || null })
              }
            />
          </Field>
          <Field label="Account number">
            <Input
              value={draft.account_no}
              inputMode="numeric"
              onChange={(e) => setDraft({ ...draft, account_no: e.target.value.trim() })}
            />
          </Field>
          <Field label="IFSC">
            <Input
              value={draft.ifsc}
              onChange={(e) => setDraft({ ...draft, ifsc: e.target.value.toUpperCase().trim() })}
              placeholder="HDFC0001234"
            />
          </Field>
          <Field label="Bank name">
            <Input
              value={draft.bank_name}
              onChange={(e) => setDraft({ ...draft, bank_name: e.target.value })}
            />
          </Field>
          <Field label="Branch" className="sm:col-span-2">
            <Input
              value={draft.branch ?? ""}
              onChange={(e) => setDraft({ ...draft, branch: e.target.value || null })}
            />
          </Field>
          <FormActions
            onCancel={() => setEditing(false)}
            onSave={() => save.mutate()}
            saving={save.isPending}
            disabled={!draft.account_no || !draft.ifsc || !draft.bank_name}
            extra={
              data && (
                <Button
                  variant="ghost"
                  className="text-destructive"
                  disabled={remove.isPending}
                  onClick={() => {
                    if (window.confirm("Remove this bank account?")) remove.mutate();
                  }}
                >
                  <Trash2 className="mr-1 h-4 w-4" /> Remove
                </Button>
              )
            }
          />
        </div>
      ) : !data ? (
        <EmptyState
          message="No bank account yet — salary can't be paid by bank transfer."
          actionLabel="Add bank account"
          onAction={open}
        />
      ) : (
        <InfoGrid>
          <InfoItem label="Account holder" value={data.account_holder_name} onAdd={open} />
          <InfoItem
            label="Account number"
            value={
              <span className="inline-flex items-center gap-2 font-mono">
                {masked}
                <button
                  type="button"
                  className="text-brand-brown-light hover:text-brand-brown-darker"
                  onClick={() => setShowNo((s) => !s)}
                  aria-label={showNo ? "Hide account number" : "Show account number"}
                >
                  {showNo ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
                </button>
              </span>
            }
          />
          <InfoItem label="Bank" value={data.bank_name} />
          <InfoItem label="IFSC" value={data.ifsc} mono />
          <InfoItem label="Branch" value={data.branch} onAdd={open} />
        </InfoGrid>
      )}
    </SectionCard>
  );
}

// ── Family ─────────────────────────────────────────────────────────────
export function FamilyCard({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const canEdit = useCanEdit();
  const { data: members = [] } = useQuery({
    queryKey: ["employee-family", employeeId],
    queryFn: () => employeeProfileApi.listFamily(employeeId),
  });
  const [adding, setAdding] = useState<FamilyMemberInput | null>(null);
  const refresh = () => qc.invalidateQueries({ queryKey: ["employee-family", employeeId] });

  const create = useMutation({
    mutationFn: (input: FamilyMemberInput) =>
      employeeProfileApi.createFamily(employeeId, input),
    onSuccess: () => {
      toast.success("Family member added");
      refresh();
      setAdding(null);
    },
    onError: (e) => toast.error(errDetail(e, "Could not add")),
  });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Partial<FamilyMemberInput> }) =>
      employeeProfileApi.updateFamily(id, body),
    onSuccess: () => {
      toast.success("Saved");
      refresh();
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });
  const del = useMutation({
    mutationFn: (id: number) => employeeProfileApi.deleteFamily(id),
    onSuccess: refresh,
    onError: (e) => toast.error(errDetail(e, "Could not delete")),
  });

  const startAdd = () =>
    setAdding({ name: "", relation: "spouse", dob: null, is_dependent: false });

  return (
    <SectionCard
      title="Family"
      description="Spouse, children and parents — dependents for insurance and benefits."
      action={
        canEdit &&
        !adding && (
          <Button variant="ghost" size="sm" className="h-8 gap-1.5" onClick={startAdd}>
            <Plus className="h-3.5 w-3.5" /> Add
          </Button>
        )
      }
    >
      <div className="space-y-2">
        {members.length === 0 && !adding && (
          <EmptyState message="No family members on record." />
        )}
        {members.map((m) => (
          <FamilyRow
            key={m.id}
            member={m}
            saving={update.isPending}
            onSave={(body, done) => update.mutate({ id: m.id, body }, { onSuccess: done })}
            onDelete={() => {
              if (window.confirm(`Remove ${m.name}?`)) del.mutate(m.id);
            }}
          />
        ))}
        {adding && (
          <FamilyForm
            initial={adding}
            saving={create.isPending}
            saveLabel="Add"
            onSave={(body) => create.mutate(body)}
            onCancel={() => setAdding(null)}
          />
        )}
      </div>
    </SectionCard>
  );
}

function FamilyRow({
  member,
  saving,
  onSave,
  onDelete,
}: {
  member: FamilyMember;
  saving: boolean;
  onSave: (body: FamilyMemberInput, done: () => void) => void;
  onDelete: () => void;
}) {
  const canEdit = useCanEdit();
  const [editing, setEditing] = useState(false);
  if (editing) {
    return (
      <FamilyForm
        initial={member}
        saving={saving}
        onSave={(body) => onSave(body, () => setEditing(false))}
        onCancel={() => setEditing(false)}
      />
    );
  }
  return (
    <PersonRow
      name={member.name}
      meta={[titleCase(member.relation), member.dob && `Born ${fmtDate(member.dob)}`]}
      chips={member.is_dependent ? <Chip tone="info">Dependent</Chip> : null}
      onEdit={canEdit ? () => setEditing(true) : undefined}
      onDelete={canEdit ? onDelete : undefined}
    />
  );
}

function FamilyForm({
  initial,
  saving,
  saveLabel = "Save",
  onSave,
  onCancel,
}: {
  initial: FamilyMemberInput;
  saving: boolean;
  saveLabel?: string;
  onSave: (body: FamilyMemberInput) => void;
  onCancel: () => void;
}) {
  const [d, setD] = useState<FamilyMemberInput>({
    name: initial.name,
    relation: initial.relation,
    dob: initial.dob,
    is_dependent: initial.is_dependent,
  });
  return (
    <div className="grid gap-3 rounded-xl border border-brand-gold/40 bg-brand-gold/5 p-4 sm:grid-cols-3">
      <Field label="Name">
        <Input value={d.name} onChange={(e) => setD({ ...d, name: e.target.value })} />
      </Field>
      <Field label="Relation">
        <select
          value={d.relation}
          onChange={(e) => setD({ ...d, relation: e.target.value })}
          className={SELECT_CLASS}
        >
          {RELATIONS.map((r) => (
            <option key={r} value={r}>
              {titleCase(r)}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Date of birth">
        <Input
          type="date"
          value={d.dob ?? ""}
          onChange={(e) => setD({ ...d, dob: e.target.value || null })}
        />
      </Field>
      <label className="flex items-center gap-2 text-sm sm:col-span-3">
        <input
          type="checkbox"
          checked={d.is_dependent}
          onChange={(e) => setD({ ...d, is_dependent: e.target.checked })}
        />
        Dependent (covered under insurance / benefits)
      </label>
      <FormActions
        onCancel={onCancel}
        onSave={() => onSave(d)}
        saving={saving}
        saveLabel={saveLabel}
        disabled={!d.name.trim()}
      />
    </div>
  );
}

function PersonRow({
  name,
  meta,
  chips,
  onEdit,
  onDelete,
}: {
  name: string;
  meta: (string | null | false | undefined)[];
  chips?: React.ReactNode;
  onEdit?: () => void;
  onDelete?: () => void;
}) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-brand-brown-50 px-4 py-3">
      <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand-brown-50 text-sm font-semibold text-brand-brown-darker">
        {name.trim()[0]?.toUpperCase() ?? "?"}
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-brand-brown-darker">{name}</span>
          {chips}
        </div>
        <div className="text-xs text-brand-brown-light">
          {meta.filter(Boolean).join(" · ")}
        </div>
      </div>
      {onEdit && (
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onEdit} aria-label={`Edit ${name}`}>
          <Pencil className="h-3.5 w-3.5" />
        </Button>
      )}
      {onDelete && (
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-destructive"
          onClick={onDelete}
          aria-label={`Remove ${name}`}
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      )}
    </div>
  );
}

// ── Passport / visa ────────────────────────────────────────────────────
const EMPTY_PASSPORT: PassportInput = {
  passport_no: "",
  passport_country: "India",
  passport_issue_date: null,
  passport_expiry_date: null,
  passport_place_of_issue: null,
  visa_no: null,
  visa_type: null,
  visa_country: null,
  visa_issue_date: null,
  visa_expiry_date: null,
};

function expiryHint(iso: string | null): React.ReactNode {
  if (!iso) return undefined;
  const left = daysUntil(iso);
  if (left < 0) return <span className="text-error">Expired</span>;
  if (left <= 180) return <span className="text-warning">{left} days left</span>;
  return undefined;
}

export function PassportCard({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["employee-passport", employeeId],
    queryFn: () => employeeProfileApi.getPassport(employeeId),
  });
  const [editing, setEditing] = useState(false);
  const [d, setD] = useState<PassportInput>(EMPTY_PASSPORT);

  const open = () => {
    if (data) {
      const { id: _id, employee_id: _e, created_at: _c, ...rest } = data;
      setD(rest);
    } else {
      setD(EMPTY_PASSPORT);
    }
    setEditing(true);
  };

  const save = useMutation({
    mutationFn: () => employeeProfileApi.upsertPassport(employeeId, d),
    onSuccess: () => {
      toast.success("Passport details saved");
      qc.invalidateQueries({ queryKey: ["employee-passport", employeeId] });
      setEditing(false);
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });
  const remove = useMutation({
    mutationFn: () => employeeProfileApi.deletePassport(employeeId),
    onSuccess: () => {
      toast.success("Passport details removed");
      qc.invalidateQueries({ queryKey: ["employee-passport", employeeId] });
      setEditing(false);
    },
  });

  const text = (k: keyof PassportInput, label: string, placeholder?: string) => (
    <Field label={label}>
      <Input
        value={(d[k] as string | null) ?? ""}
        placeholder={placeholder}
        onChange={(e) =>
          setD({
            ...d,
            [k]: k === "passport_no" || k === "passport_country" ? e.target.value : e.target.value || null,
          })
        }
      />
    </Field>
  );
  const date = (k: keyof PassportInput, label: string) => (
    <Field label={label}>
      <Input
        type="date"
        value={(d[k] as string | null) ?? ""}
        onChange={(e) => setD({ ...d, [k]: e.target.value || null })}
      />
    </Field>
  );

  return (
    <SectionCard
      title="Passport & visa"
      description="Optional — for work travel or foreign nationals."
      onEdit={data ? open : undefined}
      editing={editing}
    >
      {isLoading ? (
        <p className="text-sm text-brand-brown-light">Loading…</p>
      ) : editing ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {text("passport_no", "Passport no.")}
          {text("passport_country", "Country")}
          {text("passport_place_of_issue", "Place of issue")}
          {date("passport_issue_date", "Issued on")}
          {date("passport_expiry_date", "Expires on")}
          <div className="hidden lg:block" />
          {text("visa_no", "Visa no.")}
          {text("visa_type", "Visa type", "H1B, B1, Schengen…")}
          {text("visa_country", "Visa country")}
          {date("visa_issue_date", "Visa issued on")}
          {date("visa_expiry_date", "Visa expires on")}
          <FormActions
            onCancel={() => setEditing(false)}
            onSave={() => save.mutate()}
            saving={save.isPending}
            disabled={!d.passport_no}
            extra={
              data && (
                <Button
                  variant="ghost"
                  className="text-destructive"
                  disabled={remove.isPending}
                  onClick={() => {
                    if (window.confirm("Remove passport and visa details?")) remove.mutate();
                  }}
                >
                  <Trash2 className="mr-1 h-4 w-4" /> Remove
                </Button>
              )
            }
          />
        </div>
      ) : !data ? (
        <EmptyState
          message="No passport on record."
          actionLabel="Add passport"
          onAction={open}
        />
      ) : (
        <InfoGrid cols={3}>
          <InfoItem label="Passport no." value={data.passport_no} mono />
          <InfoItem label="Country" value={data.passport_country} />
          <InfoItem label="Place of issue" value={data.passport_place_of_issue} />
          <InfoItem label="Issued on" value={fmtDate(data.passport_issue_date)} />
          <InfoItem
            label="Expires on"
            value={fmtDate(data.passport_expiry_date)}
            hint={expiryHint(data.passport_expiry_date)}
          />
          {data.visa_no ? (
            <>
              <InfoItem
                label="Visa"
                value={[data.visa_type, data.visa_country].filter(Boolean).join(" · ") || data.visa_no}
                hint={data.visa_no}
              />
              <InfoItem
                label="Visa expires on"
                value={fmtDate(data.visa_expiry_date)}
                hint={expiryHint(data.visa_expiry_date)}
              />
            </>
          ) : (
            <InfoItem label="Visa" value="" />
          )}
        </InfoGrid>
      )}
    </SectionCard>
  );
}

// ── Nominees ───────────────────────────────────────────────────────────
const NOMINEE_TYPES: { value: NomineeType; label: string }[] = [
  { value: "pf", label: "PF" },
  { value: "gratuity", label: "Gratuity" },
  { value: "insurance", label: "Insurance" },
  { value: "general", label: "General" },
];

export function NomineesCard({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const canEdit = useCanEdit();
  const refreshCompleteness = useInvalidateCompleteness(employeeId);
  const { data: nominees = [] } = useQuery({
    queryKey: ["employee-nominees", employeeId],
    queryFn: () => employeeProfileApi.listNominees(employeeId),
  });
  const [adding, setAdding] = useState<NomineeInput | null>(null);
  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["employee-nominees", employeeId] });
    refreshCompleteness();
  };

  const create = useMutation({
    mutationFn: (input: NomineeInput) => employeeProfileApi.createNominee(employeeId, input),
    onSuccess: () => {
      toast.success("Nominee added");
      refresh();
      setAdding(null);
    },
    onError: (e) => toast.error(errDetail(e, "Could not add")),
  });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Partial<NomineeInput> }) =>
      employeeProfileApi.updateNominee(id, body),
    onSuccess: () => {
      toast.success("Saved");
      refresh();
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });
  const del = useMutation({
    mutationFn: (id: number) => employeeProfileApi.deleteNominee(id),
    onSuccess: refresh,
    onError: (e) => toast.error(errDetail(e, "Could not delete")),
  });

  // Share must total 100 within each nominee type.
  const shareByType = new Map<string, number>();
  for (const n of nominees) {
    shareByType.set(n.nominee_type, (shareByType.get(n.nominee_type) ?? 0) + Number(n.share_pct || 0));
  }
  const offTypes = [...shareByType.entries()].filter(([, v]) => Math.abs(v - 100) > 0.01);

  return (
    <SectionCard
      title="Nominees"
      description="PF, gratuity and insurance nominees. Shares of each type should total 100%."
      action={
        canEdit &&
        !adding && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-1.5"
            onClick={() =>
              setAdding({
                name: "",
                relation: "spouse",
                date_of_birth: null,
                share_pct: "100",
                nominee_type: "pf",
                address: null,
                phone: null,
                id_proof_url: null,
                is_minor: false,
                guardian_name: null,
              })
            }
          >
            <Plus className="h-3.5 w-3.5" /> Add
          </Button>
        )
      }
    >
      <div className="space-y-2">
        {offTypes.length > 0 && (
          <p className="rounded-lg bg-warning/10 px-3 py-2 text-xs text-warning">
            {offTypes
              .map(([t, v]) => `${NOMINEE_TYPES.find((x) => x.value === t)?.label ?? t} shares total ${v.toFixed(0)}%`)
              .join(" · ")}{" "}
            — should be 100%.
          </p>
        )}
        {nominees.length === 0 && !adding && <EmptyState message="No nominees on record." />}
        {nominees.map((n) => (
          <NomineeRow
            key={n.id}
            nominee={n}
            saving={update.isPending}
            onSave={(body, done) => update.mutate({ id: n.id, body }, { onSuccess: done })}
            onDelete={() => {
              if (window.confirm(`Remove ${n.name}?`)) del.mutate(n.id);
            }}
          />
        ))}
        {adding && (
          <NomineeForm
            initial={adding}
            saving={create.isPending}
            saveLabel="Add"
            onSave={(body) => create.mutate(body)}
            onCancel={() => setAdding(null)}
          />
        )}
      </div>
    </SectionCard>
  );
}

function NomineeRow({
  nominee,
  saving,
  onSave,
  onDelete,
}: {
  nominee: Nominee;
  saving: boolean;
  onSave: (body: NomineeInput, done: () => void) => void;
  onDelete: () => void;
}) {
  const canEdit = useCanEdit();
  const [editing, setEditing] = useState(false);
  if (editing) {
    return (
      <NomineeForm
        initial={nominee}
        saving={saving}
        onSave={(body) => onSave(body, () => setEditing(false))}
        onCancel={() => setEditing(false)}
      />
    );
  }
  const type = NOMINEE_TYPES.find((t) => t.value === nominee.nominee_type)?.label ?? nominee.nominee_type;
  return (
    <PersonRow
      name={nominee.name}
      meta={[
        titleCase(nominee.relation),
        nominee.date_of_birth && `Born ${fmtDate(nominee.date_of_birth)}`,
        nominee.phone,
        nominee.is_minor && nominee.guardian_name && `Guardian: ${nominee.guardian_name}`,
      ]}
      chips={
        <>
          <Chip tone="gold">
            {type} · {Number(nominee.share_pct).toFixed(0)}%
          </Chip>
          {nominee.is_minor && <Chip tone="info">Minor</Chip>}
        </>
      }
      onEdit={canEdit ? () => setEditing(true) : undefined}
      onDelete={canEdit ? onDelete : undefined}
    />
  );
}

function NomineeForm({
  initial,
  saving,
  saveLabel = "Save",
  onSave,
  onCancel,
}: {
  initial: NomineeInput;
  saving: boolean;
  saveLabel?: string;
  onSave: (body: NomineeInput) => void;
  onCancel: () => void;
}) {
  const [d, setD] = useState<NomineeInput>({
    name: initial.name,
    relation: initial.relation,
    date_of_birth: initial.date_of_birth,
    share_pct: String(initial.share_pct),
    nominee_type: initial.nominee_type,
    address: initial.address,
    phone: initial.phone,
    id_proof_url: initial.id_proof_url,
    is_minor: initial.is_minor,
    guardian_name: initial.guardian_name,
  });
  return (
    <div className="grid gap-3 rounded-xl border border-brand-gold/40 bg-brand-gold/5 p-4 sm:grid-cols-2 lg:grid-cols-3">
      <Field label="Name">
        <Input value={d.name} onChange={(e) => setD({ ...d, name: e.target.value })} />
      </Field>
      <Field label="Relation">
        <select
          value={d.relation}
          onChange={(e) => setD({ ...d, relation: e.target.value })}
          className={SELECT_CLASS}
        >
          {RELATIONS.map((r) => (
            <option key={r} value={r}>
              {titleCase(r)}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Nominee for">
        <select
          value={d.nominee_type}
          onChange={(e) => setD({ ...d, nominee_type: e.target.value as NomineeType })}
          className={SELECT_CLASS}
        >
          {NOMINEE_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Share %">
        <Input
          type="number"
          min={0}
          max={100}
          step={0.01}
          value={d.share_pct}
          onChange={(e) => setD({ ...d, share_pct: e.target.value })}
        />
      </Field>
      <Field label="Date of birth">
        <Input
          type="date"
          value={d.date_of_birth ?? ""}
          onChange={(e) => setD({ ...d, date_of_birth: e.target.value || null })}
        />
      </Field>
      <Field label="Phone">
        <Input
          value={d.phone ?? ""}
          onChange={(e) => setD({ ...d, phone: e.target.value || null })}
        />
      </Field>
      <Field label="Address" className="sm:col-span-2 lg:col-span-3">
        <Input
          value={d.address ?? ""}
          onChange={(e) => setD({ ...d, address: e.target.value || null })}
        />
      </Field>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={d.is_minor}
          onChange={(e) => setD({ ...d, is_minor: e.target.checked })}
        />
        Minor (needs a guardian)
      </label>
      {d.is_minor && (
        <Field label="Guardian name" className="sm:col-span-1 lg:col-span-2">
          <Input
            value={d.guardian_name ?? ""}
            onChange={(e) => setD({ ...d, guardian_name: e.target.value || null })}
          />
        </Field>
      )}
      <FormActions
        onCancel={onCancel}
        onSave={() => onSave(d)}
        saving={saving}
        saveLabel={saveLabel}
        disabled={!d.name.trim() || (d.is_minor && !d.guardian_name)}
      />
    </div>
  );
}
