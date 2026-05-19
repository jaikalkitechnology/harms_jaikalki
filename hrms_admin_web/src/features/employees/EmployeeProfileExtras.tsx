import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil, Plus, Save, Trash2, Upload, X } from "lucide-react";

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
import {
  employeesApi,
  type EmployeeDetail,
} from "@/lib/api/employees";
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

// ── Statutory IDs + Insurance + Attendance cycle ───────────────────────
export function StatutoryIdsCard({ employee }: { employee: EmployeeDetail }) {
  const qc = useQueryClient();
  const [pf, setPf] = useState(employee.pf_number ?? "");
  const [uan, setUan] = useState(employee.uan_number ?? "");
  const [esic, setEsic] = useState(employee.esic_number ?? "");
  const [insCo, setInsCo] = useState(employee.insurance_company ?? "");
  const [insNo, setInsNo] = useState(employee.insurance_policy_no ?? "");
  const [cycleStart, setCycleStart] = useState<number>(
    employee.attendance_cycle_start_day || 1,
  );
  const [manageCyclesOpen, setManageCyclesOpen] = useState(false);

  const { data: cycles = [] } = useQuery({
    queryKey: ["attendance-cycles"],
    queryFn: () => attendanceCyclesApi.list(),
  });

  // If the employee's saved cycle isn't in the active list (e.g. it
  // was deactivated later), surface it anyway so it doesn't silently
  // disappear from the dropdown.
  const cyclesById = new Map(cycles.map((c) => [c.start_day, c]));
  const optionsToShow: { start_day: number; label: string }[] = cycles.map(
    (c) => ({ start_day: c.start_day, label: c.name }),
  );
  if (!cyclesById.has(cycleStart)) {
    optionsToShow.push({
      start_day: cycleStart,
      label: `Day ${cycleStart} (legacy / inactive)`,
    });
  }
  optionsToShow.sort((a, b) => a.start_day - b.start_day);

  const dirty =
    pf !== (employee.pf_number ?? "") ||
    uan !== (employee.uan_number ?? "") ||
    esic !== (employee.esic_number ?? "") ||
    insCo !== (employee.insurance_company ?? "") ||
    insNo !== (employee.insurance_policy_no ?? "") ||
    cycleStart !== (employee.attendance_cycle_start_day || 1);

  const save = useMutation({
    mutationFn: () =>
      employeesApi.update(employee.id, {
        pf_number: pf || null,
        uan_number: uan || null,
        esic_number: esic || null,
        insurance_company: insCo || null,
        insurance_policy_no: insNo || null,
        attendance_cycle_start_day: cycleStart,
      } as Partial<EmployeeDetail>),
    onSuccess: () => {
      toast.success("Statutory IDs saved");
      qc.invalidateQueries({ queryKey: ["employee", employee.id] });
    },
    onError: () => toast.error("Could not save"),
  });

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>
          Statutory <span className="display-em">IDs &amp; insurance</span>
        </CardTitle>
        <CardDescription>
          PF / UAN / ESIC numbers, group insurance details, and the
          attendance cycle this employee follows.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid md:grid-cols-2 gap-4">
        <Field label="PF Number">
          <Input value={pf} onChange={(e) => setPf(e.target.value)} placeholder="MH/BAN/00012345/678" />
        </Field>
        <Field label="UAN Number">
          <Input value={uan} onChange={(e) => setUan(e.target.value)} placeholder="100000000000" />
        </Field>
        <Field label="ESIC Number">
          <Input value={esic} onChange={(e) => setEsic(e.target.value)} placeholder="3100000000" />
        </Field>
        <Field label="Insurance Company">
          <Input
            value={insCo}
            onChange={(e) => setInsCo(e.target.value)}
            placeholder="HDFC ERGO General Insurance"
          />
        </Field>
        <Field label="Insurance Policy ID">
          <Input
            value={insNo}
            onChange={(e) => setInsNo(e.target.value)}
            placeholder="2950 1234 5678"
          />
        </Field>
        <Field label="Attendance cycle">
          <div className="flex gap-2">
            <select
              value={cycleStart}
              onChange={(e) => setCycleStart(Number(e.target.value))}
              className="flex h-10 flex-1 rounded-md border border-input bg-card px-3 py-2 text-sm"
            >
              {optionsToShow.map((o) => (
                <option key={o.start_day} value={o.start_day}>
                  {o.label}
                </option>
              ))}
            </select>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="gap-1"
              onClick={() => setManageCyclesOpen(true)}
            >
              <Pencil className="h-3.5 w-3.5" /> Manage
            </Button>
          </div>
          <p className="text-xs text-brand-brown-light mt-1">
            Drives the calendar slice and payroll cut-off for this
            employee. Manage to add/disable cycles for the whole company.
          </p>
        </Field>
        <div className="md:col-span-2 flex justify-end">
          <Button
            disabled={!dirty || save.isPending}
            onClick={() => save.mutate()}
            className="gap-2"
          >
            <Save className="h-4 w-4" />
            {save.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </CardContent>
      {manageCyclesOpen && (
        <ManageCyclesModal onClose={() => setManageCyclesOpen(false)} />
      )}
    </Card>
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

// ── Bank account card ──────────────────────────────────────────────────
export function BankCard({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["employee-bank", employeeId],
    queryFn: () => bankApi.get(employeeId),
  });
  const [draft, setDraft] = useState<BankDetailsInput>({
    account_no: "",
    ifsc: "",
    bank_name: "",
    branch: null,
    account_holder_name: null,
  });

  useEffect(() => {
    if (data) {
      setDraft({
        account_no: data.account_no,
        ifsc: data.ifsc,
        bank_name: data.bank_name,
        branch: data.branch,
        account_holder_name: data.account_holder_name,
      });
    }
  }, [data]);

  const save = useMutation({
    mutationFn: () => bankApi.upsert(employeeId, draft),
    onSuccess: () => {
      toast.success("Bank account saved");
      qc.invalidateQueries({ queryKey: ["employee-bank", employeeId] });
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not save";
      toast.error(detail);
    },
  });
  const remove = useMutation({
    mutationFn: () => bankApi.remove(employeeId),
    onSuccess: () => {
      toast.success("Bank account removed");
      qc.invalidateQueries({ queryKey: ["employee-bank", employeeId] });
      setDraft({
        account_no: "",
        ifsc: "",
        bank_name: "",
        branch: null,
        account_holder_name: null,
      });
    },
  });

  if (isLoading) return null;

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>
          Bank <span className="display-em">account</span>
        </CardTitle>
        <CardDescription>
          Salary credit account. Used by the payroll bank-file export.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid md:grid-cols-2 gap-4">
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
            onChange={(e) => setDraft({ ...draft, account_no: e.target.value })}
          />
        </Field>
        <Field label="IFSC">
          <Input
            value={draft.ifsc}
            onChange={(e) =>
              setDraft({ ...draft, ifsc: e.target.value.toUpperCase() })
            }
            placeholder="HDFC0001234"
          />
        </Field>
        <Field label="Bank name">
          <Input
            value={draft.bank_name}
            onChange={(e) => setDraft({ ...draft, bank_name: e.target.value })}
          />
        </Field>
        <Field label="Branch">
          <Input
            value={draft.branch ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, branch: e.target.value || null })
            }
          />
        </Field>
        <div className="md:col-span-2 flex justify-end gap-2">
          {data && (
            <Button
              variant="outline"
              className="text-destructive"
              onClick={() => remove.mutate()}
              disabled={remove.isPending}
            >
              Remove
            </Button>
          )}
          <Button
            disabled={
              !draft.account_no ||
              !draft.ifsc ||
              !draft.bank_name ||
              save.isPending
            }
            onClick={() => save.mutate()}
            className="gap-2"
          >
            <Save className="h-4 w-4" />
            {save.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Family card ────────────────────────────────────────────────────────
export function FamilyCard({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const { data: members = [] } = useQuery({
    queryKey: ["employee-family", employeeId],
    queryFn: () => employeeProfileApi.listFamily(employeeId),
  });
  const [adding, setAdding] = useState<FamilyMemberInput | null>(null);

  const create = useMutation({
    mutationFn: (input: FamilyMemberInput) =>
      employeeProfileApi.createFamily(employeeId, input),
    onSuccess: () => {
      toast.success("Family member added");
      qc.invalidateQueries({ queryKey: ["employee-family", employeeId] });
      setAdding(null);
    },
  });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Partial<FamilyMemberInput> }) =>
      employeeProfileApi.updateFamily(id, body),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["employee-family", employeeId] }),
  });
  const del = useMutation({
    mutationFn: (id: number) => employeeProfileApi.deleteFamily(id),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["employee-family", employeeId] }),
  });

  return (
    <Card className="lg:col-span-2">
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle>
            Family <span className="display-em">details</span>
          </CardTitle>
          <CardDescription>
            Spouse, children, parents — anyone the employee names as a
            dependent for insurance/benefits.
          </CardDescription>
        </div>
        <Button
          variant="outline"
          className="gap-2"
          onClick={() =>
            setAdding({ name: "", relation: "spouse", dob: null, is_dependent: false })
          }
        >
          <Plus className="h-4 w-4" /> Add
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {members.length === 0 && !adding && (
          <p className="text-sm text-brand-brown-light">
            No family members on record yet.
          </p>
        )}
        {members.map((m) => (
          <FamilyRow
            key={m.id}
            member={m}
            onSave={(body) => update.mutate({ id: m.id, body })}
            onDelete={() => del.mutate(m.id)}
          />
        ))}
        {adding && (
          <FamilyRow
            member={{ id: -1, employee_id: employeeId, ...adding }}
            isNew
            onSave={(body) => create.mutate(body as FamilyMemberInput)}
            onDelete={() => setAdding(null)}
          />
        )}
      </CardContent>
    </Card>
  );
}

function FamilyRow({
  member,
  isNew = false,
  onSave,
  onDelete,
}: {
  member: FamilyMember;
  isNew?: boolean;
  onSave: (body: Partial<FamilyMemberInput>) => void;
  onDelete: () => void;
}) {
  const [draft, setDraft] = useState<FamilyMemberInput>({
    name: member.name,
    relation: member.relation,
    dob: member.dob,
    is_dependent: member.is_dependent,
  });
  return (
    <div className="grid grid-cols-1 md:grid-cols-[1.5fr_1fr_1fr_auto_auto] gap-2 items-end p-3 rounded-md border border-brand-brown-100/60">
      <Field label="Name">
        <Input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
      </Field>
      <Field label="Relation">
        <select
          value={draft.relation}
          onChange={(e) => setDraft({ ...draft, relation: e.target.value })}
          className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
        >
          {["spouse", "child", "father", "mother", "sibling", "other"].map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </Field>
      <Field label="DOB">
        <Input
          type="date"
          value={draft.dob ?? ""}
          onChange={(e) => setDraft({ ...draft, dob: e.target.value || null })}
        />
      </Field>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={draft.is_dependent}
          onChange={(e) => setDraft({ ...draft, is_dependent: e.target.checked })}
        />
        Dependent
      </label>
      <div className="flex gap-1">
        <Button size="sm" onClick={() => onSave(draft)} disabled={!draft.name}>
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

// ── Passport / visa card ───────────────────────────────────────────────
export function PassportCard({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["employee-passport", employeeId],
    queryFn: () => employeeProfileApi.getPassport(employeeId),
  });
  const [draft, setDraft] = useState<PassportInput>({
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
  });

  useEffect(() => {
    if (data) {
      setDraft({
        passport_no: data.passport_no,
        passport_country: data.passport_country,
        passport_issue_date: data.passport_issue_date,
        passport_expiry_date: data.passport_expiry_date,
        passport_place_of_issue: data.passport_place_of_issue,
        visa_no: data.visa_no,
        visa_type: data.visa_type,
        visa_country: data.visa_country,
        visa_issue_date: data.visa_issue_date,
        visa_expiry_date: data.visa_expiry_date,
      });
    }
  }, [data]);

  const save = useMutation({
    mutationFn: () => employeeProfileApi.upsertPassport(employeeId, draft),
    onSuccess: () => {
      toast.success("Passport details saved");
      qc.invalidateQueries({ queryKey: ["employee-passport", employeeId] });
    },
    onError: () => toast.error("Could not save"),
  });
  const remove = useMutation({
    mutationFn: () => employeeProfileApi.deletePassport(employeeId),
    onSuccess: () => {
      toast.success("Passport details removed");
      qc.invalidateQueries({ queryKey: ["employee-passport", employeeId] });
    },
  });

  if (isLoading) return null;

  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>
          Passport &amp; <span className="display-em">visa</span>
        </CardTitle>
        <CardDescription>
          Recorded only when the employee travels for work or is a foreign
          national. Optional.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid md:grid-cols-3 gap-4">
        <Field label="Passport No.">
          <Input
            value={draft.passport_no}
            onChange={(e) => setDraft({ ...draft, passport_no: e.target.value })}
          />
        </Field>
        <Field label="Country">
          <Input
            value={draft.passport_country}
            onChange={(e) =>
              setDraft({ ...draft, passport_country: e.target.value })
            }
          />
        </Field>
        <Field label="Place of issue">
          <Input
            value={draft.passport_place_of_issue ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, passport_place_of_issue: e.target.value || null })
            }
          />
        </Field>
        <Field label="Issued on">
          <Input
            type="date"
            value={draft.passport_issue_date ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, passport_issue_date: e.target.value || null })
            }
          />
        </Field>
        <Field label="Expires on">
          <Input
            type="date"
            value={draft.passport_expiry_date ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, passport_expiry_date: e.target.value || null })
            }
          />
        </Field>
        <div />
        <Field label="Visa No.">
          <Input
            value={draft.visa_no ?? ""}
            onChange={(e) => setDraft({ ...draft, visa_no: e.target.value || null })}
          />
        </Field>
        <Field label="Visa Type">
          <Input
            value={draft.visa_type ?? ""}
            onChange={(e) => setDraft({ ...draft, visa_type: e.target.value || null })}
            placeholder="H1B, B1, Schengen…"
          />
        </Field>
        <Field label="Visa Country">
          <Input
            value={draft.visa_country ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, visa_country: e.target.value || null })
            }
          />
        </Field>
        <Field label="Visa issued on">
          <Input
            type="date"
            value={draft.visa_issue_date ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, visa_issue_date: e.target.value || null })
            }
          />
        </Field>
        <Field label="Visa expires on">
          <Input
            type="date"
            value={draft.visa_expiry_date ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, visa_expiry_date: e.target.value || null })
            }
          />
        </Field>
        <div className="md:col-span-3 flex justify-end gap-2">
          {data && (
            <Button
              variant="outline"
              className="text-destructive"
              onClick={() => remove.mutate()}
              disabled={remove.isPending}
            >
              Remove
            </Button>
          )}
          <Button
            disabled={!draft.passport_no || save.isPending}
            onClick={() => save.mutate()}
            className="gap-2"
          >
            <Save className="h-4 w-4" /> Save
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Nominees card ──────────────────────────────────────────────────────
export function NomineesCard({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const { data: nominees = [] } = useQuery({
    queryKey: ["employee-nominees", employeeId],
    queryFn: () => employeeProfileApi.listNominees(employeeId),
  });
  const [adding, setAdding] = useState<NomineeInput | null>(null);

  const create = useMutation({
    mutationFn: (input: NomineeInput) =>
      employeeProfileApi.createNominee(employeeId, input),
    onSuccess: () => {
      toast.success("Nominee added");
      qc.invalidateQueries({ queryKey: ["employee-nominees", employeeId] });
      setAdding(null);
    },
  });
  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Partial<NomineeInput> }) =>
      employeeProfileApi.updateNominee(id, body),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["employee-nominees", employeeId] }),
  });
  const del = useMutation({
    mutationFn: (id: number) => employeeProfileApi.deleteNominee(id),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["employee-nominees", employeeId] }),
  });

  const totalShare = nominees.reduce((s, n) => s + Number(n.share_pct || 0), 0);

  return (
    <Card className="lg:col-span-2">
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <CardTitle>
            Nominees · <span className="display-em">PF / Gratuity / Insurance</span>
          </CardTitle>
          <CardDescription>
            Share % across nominees of the same type should total 100. Up to
            4 nominees per employee is the standard practice.
          </CardDescription>
        </div>
        <Button
          variant="outline"
          className="gap-2"
          onClick={() =>
            setAdding({
              name: "",
              relation: "spouse",
              date_of_birth: null,
              share_pct: "100",
              nominee_type: "general",
              address: null,
              phone: null,
              id_proof_url: null,
              is_minor: false,
              guardian_name: null,
            })
          }
        >
          <Plus className="h-4 w-4" /> Add nominee
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {nominees.length > 0 && (
          <div className="text-xs text-brand-brown-light">
            Total share across all nominees: <strong>{totalShare.toFixed(2)}%</strong>
          </div>
        )}
        {nominees.length === 0 && !adding && (
          <p className="text-sm text-brand-brown-light">
            No nominees on record yet.
          </p>
        )}
        {nominees.map((n) => (
          <NomineeRow
            key={n.id}
            nominee={n}
            onSave={(body) => update.mutate({ id: n.id, body })}
            onDelete={() => del.mutate(n.id)}
          />
        ))}
        {adding && (
          <NomineeRow
            nominee={{ id: -1, employee_id: employeeId, ...adding } as Nominee}
            isNew
            onSave={(body) => create.mutate(body as NomineeInput)}
            onDelete={() => setAdding(null)}
          />
        )}
      </CardContent>
    </Card>
  );
}

function NomineeRow({
  nominee,
  isNew = false,
  onSave,
  onDelete,
}: {
  nominee: Nominee;
  isNew?: boolean;
  onSave: (body: Partial<NomineeInput>) => void;
  onDelete: () => void;
}) {
  const [draft, setDraft] = useState<NomineeInput>({
    name: nominee.name,
    relation: nominee.relation,
    date_of_birth: nominee.date_of_birth,
    share_pct: String(nominee.share_pct),
    nominee_type: nominee.nominee_type,
    address: nominee.address,
    phone: nominee.phone,
    id_proof_url: nominee.id_proof_url,
    is_minor: nominee.is_minor,
    guardian_name: nominee.guardian_name,
  });
  return (
    <div className="rounded-md border border-brand-brown-100/60 p-3 space-y-2">
      <div className="grid grid-cols-1 md:grid-cols-[1fr_1fr_1fr_1fr_1fr_auto] gap-2 items-end">
        <Field label="Name">
          <Input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} />
        </Field>
        <Field label="Relation">
          <select
            value={draft.relation}
            onChange={(e) => setDraft({ ...draft, relation: e.target.value })}
            className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
          >
            {["spouse", "child", "father", "mother", "sibling", "other"].map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Type">
          <select
            value={draft.nominee_type}
            onChange={(e) =>
              setDraft({ ...draft, nominee_type: e.target.value as NomineeType })
            }
            className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
          >
            <option value="general">General</option>
            <option value="pf">PF</option>
            <option value="gratuity">Gratuity</option>
            <option value="insurance">Insurance</option>
          </select>
        </Field>
        <Field label="Share %">
          <Input
            type="number"
            min={0}
            max={100}
            step={0.01}
            value={draft.share_pct}
            onChange={(e) => setDraft({ ...draft, share_pct: e.target.value })}
          />
        </Field>
        <Field label="DOB">
          <Input
            type="date"
            value={draft.date_of_birth ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, date_of_birth: e.target.value || null })
            }
          />
        </Field>
        <div className="flex gap-1 pb-1">
          <Button size="sm" onClick={() => onSave(draft)} disabled={!draft.name}>
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        <Field label="Phone">
          <Input
            value={draft.phone ?? ""}
            onChange={(e) => setDraft({ ...draft, phone: e.target.value || null })}
          />
        </Field>
        <Field label="Address">
          <Input
            value={draft.address ?? ""}
            onChange={(e) => setDraft({ ...draft, address: e.target.value || null })}
          />
        </Field>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={draft.is_minor}
            onChange={(e) => setDraft({ ...draft, is_minor: e.target.checked })}
          />
          Minor (needs guardian)
        </label>
        {draft.is_minor && (
          <Field label="Guardian name">
            <Input
              value={draft.guardian_name ?? ""}
              onChange={(e) =>
                setDraft({ ...draft, guardian_name: e.target.value || null })
              }
            />
          </Field>
        )}
      </div>
    </div>
  );
}

// ── Profile photo upload (drop-in for the avatar) ──────────────────────
export function PhotoUploadButton({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const upload = useMutation({
    mutationFn: (file: File) =>
      employeeProfileApi.uploadPhoto(employeeId, file),
    onSuccess: () => {
      toast.success("Photo updated");
      qc.invalidateQueries({ queryKey: ["employee", employeeId] });
    },
    onError: () => toast.error("Upload failed"),
  });

  return (
    <>
      <Button
        size="sm"
        variant="outline"
        className="gap-2"
        onClick={() => inputRef.current?.click()}
      >
        <Upload className="h-3.5 w-3.5" />
        Photo
      </Button>
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) upload.mutate(f);
          if (inputRef.current) inputRef.current.value = "";
        }}
      />
    </>
  );
}

// ── Local Field shim ───────────────────────────────────────────────────
function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
    </div>
  );
}
