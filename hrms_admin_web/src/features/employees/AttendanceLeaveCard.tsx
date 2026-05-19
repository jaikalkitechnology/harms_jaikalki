import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ChevronLeft, ChevronRight, X } from "lucide-react";

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
  attendanceApi,
  type CalendarDay,
} from "@/lib/api/attendance";
import { leavesApi } from "@/lib/api/leaves";
import { employeesApi } from "@/lib/api/employees";
import { attendanceCyclesApi } from "@/lib/api/employeeProfile";

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const MONTHS_FULL = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export function AttendanceLeaveCard({ employeeId }: { employeeId: number }) {
  const qc = useQueryClient();
  const thisYear = new Date().getFullYear();
  const [year, setYear] = useState(thisYear);
  const [openMonth, setOpenMonth] = useState<number | null>(null);
  const [adjustOpen, setAdjustOpen] = useState(false);

  const { data: employee } = useQuery({
    queryKey: ["employee", employeeId],
    queryFn: () => employeesApi.get(employeeId),
  });
  const { data: cycles = [] } = useQuery({
    queryKey: ["attendance-cycles"],
    queryFn: () => attendanceCyclesApi.list(),
  });

  const cycleStart = employee?.attendance_cycle_start_day ?? 1;

  const setCycle = useMutation({
    mutationFn: (startDay: number) =>
      employeesApi.update(employeeId, {
        attendance_cycle_start_day: startDay,
      } as Partial<import("@/lib/api/employees").EmployeeDetail>),
    onSuccess: () => {
      toast.success("Attendance cycle updated");
      qc.invalidateQueries({ queryKey: ["employee", employeeId] });
      qc.invalidateQueries({ queryKey: ["attendance-year", employeeId] });
      qc.invalidateQueries({ queryKey: ["attendance-calendar", employeeId] });
    },
    onError: () => toast.error("Could not update cycle"),
  });

  const [bdFrom, setBdFrom] = useState("");
  const [bdTo, setBdTo] = useState("");
  useEffect(() => {
    setBdFrom(employee?.backdate_from ?? "");
    setBdTo(employee?.backdate_to ?? "");
  }, [employee?.backdate_from, employee?.backdate_to]);

  const setBackdate = useMutation({
    mutationFn: (clear: boolean) =>
      employeesApi.update(employeeId, {
        backdate_from: clear ? null : bdFrom || null,
        backdate_to: clear ? null : bdTo || null,
      } as Partial<import("@/lib/api/employees").EmployeeDetail>),
    onSuccess: (_d, clear) => {
      toast.success(
        clear
          ? "Back-date window locked"
          : "Back-date window granted",
      );
      qc.invalidateQueries({ queryKey: ["employee", employeeId] });
    },
    onError: () => toast.error("Could not update back-date window"),
  });

  // Active cycle list + the employee's current value even if it was
  // since deactivated, so the dropdown never loses the saved choice.
  const cycleOptions: { start_day: number; label: string }[] = cycles.map(
    (c) => ({ start_day: c.start_day, label: c.name }),
  );
  if (!cycleOptions.some((o) => o.start_day === cycleStart)) {
    cycleOptions.push({
      start_day: cycleStart,
      label:
        cycleStart === 1
          ? "1st → last day (calendar month)"
          : `Day ${cycleStart} cycle`,
    });
  }
  cycleOptions.sort((a, b) => a.start_day - b.start_day);

  const { data: summary } = useQuery({
    queryKey: ["attendance-year", employeeId, year, cycleStart],
    queryFn: () => attendanceApi.employeeYearSummary(employeeId, year),
  });

  const { data: balances = [] } = useQuery({
    queryKey: ["leave-balance", employeeId, year],
    queryFn: () => leavesApi.employeeBalance(employeeId, year),
  });

  return (
    <Card className="lg:col-span-2">
      <CardHeader className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <CardTitle>
            Attendance &amp; <span className="display-em">Leave</span>
          </CardTitle>
          <CardDescription>
            Leave balance, plus a roll-up sliced by the chosen cycle.
            Click any period to open and edit attendance.
          </CardDescription>
        </div>
        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <div className="space-y-1">
            <Label className="text-[10px] uppercase tracking-[0.2em] text-brand-brown-light">
              Cycle calendar
            </Label>
            <select
              value={cycleStart}
              onChange={(e) => setCycle.mutate(Number(e.target.value))}
              disabled={setCycle.isPending}
              className="flex h-9 rounded-md border border-input bg-card px-2 py-1.5 text-sm"
            >
              {cycleOptions.map((o) => (
                <option key={o.start_day} value={o.start_day}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-1">
            <Button
              size="sm"
              variant="outline"
              onClick={() => setYear((y) => y - 1)}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="px-3 py-1.5 rounded border border-brand-brown-50 bg-card text-sm font-medium min-w-[4.5rem] text-center">
              {year}
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setYear((y) => Math.min(thisYear + 1, y + 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* ── Leave balances ── */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-gold-dark">
              Leave balance · {year}
            </div>
            <Button
              size="sm"
              variant="outline"
              className="h-7 gap-1"
              onClick={() => setAdjustOpen(true)}
            >
              Adjust balance
            </Button>
          </div>
          {balances.length === 0 ? (
            <p className="text-sm text-brand-brown-light">
              No leave balances allocated for this year.
            </p>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
              {balances.map((b) => {
                const remaining = Number(b.balance);
                const used = Number(b.used);
                const alloc =
                  Number(b.allocated) + Number(b.carried_forward);
                return (
                  <div
                    key={b.id}
                    className="rounded-md border border-brand-brown-100 p-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-brand-brown-darker">
                        {b.leave_type?.code ?? "—"}
                      </span>
                      <span className="text-[10px] font-mono uppercase tracking-[0.15em] text-brand-brown-light">
                        {b.leave_type?.name ?? ""}
                      </span>
                    </div>
                    <div className="mt-2 flex items-end justify-between">
                      <div>
                        <div className="text-[10px] text-brand-brown-light uppercase tracking-wide">
                          Remaining
                        </div>
                        <div
                          className={`text-xl font-bold ${
                            remaining > 0 ? "text-success" : "text-error"
                          }`}
                        >
                          {remaining}
                        </div>
                      </div>
                      <div className="text-right text-[11px] text-brand-brown-light leading-tight">
                        <div>
                          used <span className="text-warning font-semibold">{used}</span>
                        </div>
                        <div>of {alloc}</div>
                        {Number(b.adjustment) !== 0 && (
                          <div
                            className={
                              Number(b.adjustment) > 0
                                ? "text-success"
                                : "text-error"
                            }
                          >
                            adj {Number(b.adjustment) > 0 ? "+" : ""}
                            {b.adjustment}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ── Year totals ── */}
        {summary && (
          <div className="flex flex-wrap gap-2">
            <Pill label="Present" value={summary.total_present} tone="success" />
            <Pill label="WFH" value={summary.total_wfh} tone="info" />
            <Pill label="Half-day" value={summary.total_half_day} tone="warning" />
            <Pill label="Leave" value={summary.total_leave} tone="error" />
            <Pill label="Absent" value={summary.total_absent} tone="error" />
            <Pill label="Holiday" value={summary.total_holiday} tone="muted" />
            <Pill label="Working days" value={summary.total_working_days} tone="muted" />
          </div>
        )}

        {/* ── Back-date permission ── */}
        <div className="rounded-md border border-brand-brown-100 p-3">
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-gold-dark mb-2">
            Back-date attendance permission
          </div>
          <p className="text-xs text-brand-brown-light mb-2">
            Open a date range so this employee can self-mark missed
            attendance from the mobile app. Same-day marking is always
            allowed. Lock to revoke.
          </p>
          <div className="flex flex-wrap items-end gap-2">
            <div>
              <Label className="text-[10px] uppercase tracking-[0.2em] text-brand-brown-light">
                From
              </Label>
              <Input
                type="date"
                value={bdFrom}
                onChange={(e) => setBdFrom(e.target.value)}
                className="h-9 w-40"
              />
            </div>
            <div>
              <Label className="text-[10px] uppercase tracking-[0.2em] text-brand-brown-light">
                To
              </Label>
              <Input
                type="date"
                value={bdTo}
                onChange={(e) => setBdTo(e.target.value)}
                className="h-9 w-40"
              />
            </div>
            <Button
              size="sm"
              disabled={!bdFrom || !bdTo || setBackdate.isPending}
              onClick={() => setBackdate.mutate(false)}
            >
              Grant
            </Button>
            {(employee?.backdate_from || employee?.backdate_to) && (
              <Button
                size="sm"
                variant="outline"
                className="text-destructive"
                disabled={setBackdate.isPending}
                onClick={() => setBackdate.mutate(true)}
              >
                Lock
              </Button>
            )}
          </div>
          {employee?.backdate_from && employee?.backdate_to && (
            <p className="text-xs text-success mt-2">
              Currently open: {employee.backdate_from} →{" "}
              {employee.backdate_to}
            </p>
          )}
        </div>

        {/* ── 12-month grid ── */}
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-gold-dark mb-2">
            Monthly breakdown · {year}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {(summary?.months ?? []).map((m) => {
              const flagged = m.days_absent > 0 || m.days_leave > 0;
              const isOpen = openMonth === m.month;
              return (
                <button
                  key={m.month}
                  type="button"
                  onClick={() =>
                    setOpenMonth(isOpen ? null : m.month)
                  }
                  className={`text-left rounded-lg border p-3 transition-colors ${
                    isOpen
                      ? "border-brand-gold-dark bg-brand-gold/10"
                      : flagged
                        ? "border-error/30 bg-error/5 hover:border-error/50"
                        : "border-brand-brown-100 bg-card hover:border-brand-gold-dark/50"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-brand-brown-darker">
                      {MONTHS[m.month - 1]}
                    </span>
                    <span className="text-[10px] font-mono text-brand-brown-light">
                      {m.working_days} wd
                    </span>
                  </div>
                  {cycleStart !== 1 && (
                    <div className="text-[10px] text-brand-brown-light mt-0.5">
                      {cycleRangeLabel(year, m.month, cycleStart)}
                    </div>
                  )}
                  <div className="mt-2 flex flex-wrap gap-1.5 text-[11px]">
                    <span className="px-1.5 py-0.5 rounded bg-success/15 text-success font-semibold">
                      P {m.days_present}
                    </span>
                    {m.days_absent > 0 && (
                      <span className="px-1.5 py-0.5 rounded bg-error/15 text-error font-semibold">
                        A {m.days_absent}
                      </span>
                    )}
                    {m.days_leave > 0 && (
                      <span className="px-1.5 py-0.5 rounded bg-error/15 text-error font-semibold">
                        L {m.days_leave}
                      </span>
                    )}
                    {m.days_half_day > 0 && (
                      <span className="px-1.5 py-0.5 rounded bg-warning/15 text-warning font-semibold">
                        ½ {m.days_half_day}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {openMonth !== null && (
          <MonthEditor
            employeeId={employeeId}
            year={year}
            month={openMonth}
            onClose={() => setOpenMonth(null)}
          />
        )}
        {adjustOpen && (
          <AdjustBalanceModal
            employeeId={employeeId}
            year={year}
            balances={balances}
            onClose={() => setAdjustOpen(false)}
            onDone={() => {
              setAdjustOpen(false);
              qc.invalidateQueries({
                queryKey: ["leave-balance", employeeId, year],
              });
            }}
          />
        )}
      </CardContent>
    </Card>
  );
}

function AdjustBalanceModal({
  employeeId,
  year,
  balances,
  onClose,
  onDone,
}: {
  employeeId: number;
  year: number;
  balances: import("@/lib/api/leaves").LeaveBalance[];
  onClose: () => void;
  onDone: () => void;
}) {
  const [leaveTypeId, setLeaveTypeId] = useState<number>(
    balances[0]?.leave_type_id ?? 0,
  );
  const [sign, setSign] = useState<"+" | "-">("+");
  const [amount, setAmount] = useState("1");
  const [reason, setReason] = useState("");

  const { data: history = [] } = useQuery({
    queryKey: ["leave-adjustments", employeeId, year],
    queryFn: () => leavesApi.listAdjustments(employeeId, year),
  });

  const save = useMutation({
    mutationFn: () =>
      leavesApi.adjustBalance(employeeId, {
        leave_type_id: leaveTypeId,
        delta: (sign === "-" ? -1 : 1) * Number(amount),
        reason: reason.trim(),
        year,
      }),
    onSuccess: () => {
      toast.success("Balance adjusted");
      onDone();
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not adjust";
      toast.error(detail);
    },
  });

  const codeFor = (id: number) =>
    balances.find((b) => b.leave_type_id === id)?.leave_type?.code ??
    `#${id}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Adjust leave balance</CardTitle>
            <CardDescription>
              Add or remove days for FY {year}. Every change is logged
              with a reason.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Leave type</Label>
              <select
                value={leaveTypeId}
                onChange={(e) => setLeaveTypeId(Number(e.target.value))}
                className="flex h-10 w-full rounded-md border border-input bg-card px-3 text-sm"
              >
                {balances.map((b) => (
                  <option key={b.id} value={b.leave_type_id}>
                    {b.leave_type?.code} — {b.leave_type?.name} (bal{" "}
                    {b.balance})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Change</Label>
              <div className="flex gap-2">
                <select
                  value={sign}
                  onChange={(e) => setSign(e.target.value as "+" | "-")}
                  className="flex h-10 rounded-md border border-input bg-card px-2 text-sm"
                >
                  <option value="+">Add (+)</option>
                  <option value="-">Remove (−)</option>
                </select>
                <Input
                  type="number"
                  min={0}
                  step={0.5}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  className="w-24"
                />
              </div>
            </div>
          </div>
          <div>
            <Label>Reason *</Label>
            <Input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. comp-off for Sunday work on 12 Apr"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              disabled={
                !leaveTypeId ||
                !Number(amount) ||
                reason.trim().length < 3 ||
                save.isPending
              }
              onClick={() => save.mutate()}
            >
              {save.isPending ? "Saving…" : "Apply adjustment"}
            </Button>
          </div>

          {history.length > 0 && (
            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-2">
                Adjustment history
              </div>
              <div className="rounded-md border border-brand-brown-100 divide-y divide-brand-brown-100/60 max-h-52 overflow-y-auto">
                {history.map((h) => (
                  <div
                    key={h.id}
                    className="flex items-start justify-between gap-3 px-3 py-2 text-xs"
                  >
                    <div>
                      <span
                        className={`font-semibold ${
                          Number(h.delta) >= 0
                            ? "text-success"
                            : "text-error"
                        }`}
                      >
                        {Number(h.delta) >= 0 ? "+" : ""}
                        {h.delta} {codeFor(h.leave_type_id)}
                      </span>
                      <span className="text-brand-brown-light">
                        {" "}
                        · {h.reason}
                      </span>
                    </div>
                    <span className="text-brand-brown-light whitespace-nowrap">
                      {new Date(h.created_at).toLocaleDateString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Pill({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "success" | "info" | "warning" | "error" | "muted";
}) {
  const cls =
    tone === "success"
      ? "text-success"
      : tone === "info"
        ? "text-info"
        : tone === "warning"
          ? "text-warning"
          : tone === "error"
            ? "text-error"
            : "text-brand-brown-darker";
  return (
    <div className="rounded-md border border-brand-brown-50 px-3 py-1.5 text-sm">
      <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
        {label}
      </span>
      <span className={`ml-2 font-semibold ${cls}`}>{value}</span>
    </div>
  );
}

// ── Inline editable month calendar ─────────────────────────────────────
const STATUS_LABEL: Record<string, string> = {
  present: "P",
  absent: "A",
  half_day: "½",
  wfh: "WFH",
  leave: "L",
  holiday: "HOL",
  week_off: "SUN",
  upcoming: "",
  blank: "",
};

function MonthEditor({
  employeeId,
  year,
  month,
  onClose,
}: {
  employeeId: number;
  year: number;
  month: number;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [editing, setEditing] = useState<CalendarDay | null>(null);

  const { data: cal, isLoading } = useQuery({
    queryKey: ["attendance-calendar", employeeId, year, month],
    queryFn: () => attendanceApi.employeeCalendar(employeeId, year, month),
  });

  const grid = useMemo(() => {
    if (!cal) return [];
    const first = new Date(cal.year, cal.month - 1, 1);
    const firstWd = (first.getDay() + 6) % 7; // Mon=0
    const out: Array<CalendarDay | null> = [];
    for (let i = 0; i < firstWd; i++) out.push(null);
    out.push(...cal.days);
    while (out.length % 7 !== 0) out.push(null);
    return out;
  }, [cal]);

  return (
    <div className="rounded-xl border border-brand-gold-dark/40 bg-brand-gold/5 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="font-display text-lg font-bold text-brand-brown-darker">
          {MONTHS_FULL[month - 1]} {year}
        </div>
        <Button size="sm" variant="ghost" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {isLoading || !cal ? (
        <div className="py-8 text-center text-sm text-brand-brown-light">
          Loading…
        </div>
      ) : (
        <>
          <div className="grid grid-cols-7 gap-1 text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-1">
            {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => (
              <div key={d} className="text-center">
                {d}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {grid.map((d, i) =>
              d === null ? (
                <div key={`pad-${i}`} className="aspect-square" />
              ) : (
                <DayCell
                  key={d.date}
                  day={d}
                  onClick={() => d.is_editable && setEditing(d)}
                />
              ),
            )}
          </div>
          <p className="mt-3 text-xs text-brand-brown-light">
            Sundays &amp; holidays are red and locked. Click any working
            day to add or correct attendance.
          </p>
        </>
      )}

      {editing && (
        <DayEditModal
          day={editing}
          employeeId={employeeId}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            qc.invalidateQueries({
              queryKey: ["attendance-calendar", employeeId, year, month],
            });
            qc.invalidateQueries({
              queryKey: ["attendance-year", employeeId, year],
            });
          }}
        />
      )}
    </div>
  );
}

function DayCell({
  day,
  onClick,
}: {
  day: CalendarDay;
  onClick: () => void;
}) {
  const dayNum = Number(day.date.slice(8, 10));
  const off = day.is_sunday || day.is_holiday;
  const upcoming = day.status === "upcoming";
  const tone = off
    ? "bg-error/10 border-error/30 text-error cursor-not-allowed"
    : upcoming
      ? "bg-brand-brown-50/40 border-brand-brown-50 text-brand-brown-light cursor-not-allowed"
      : day.status === "present" || day.status === "wfh"
        ? "bg-success/10 border-success/30 text-success cursor-pointer hover:border-success"
        : day.status === "absent"
          ? "bg-error/10 border-error/30 text-error cursor-pointer hover:border-error"
          : day.status === "leave"
            ? "bg-error/10 border-error/30 text-error cursor-pointer hover:border-error"
            : day.status === "half_day"
              ? "bg-warning/10 border-warning/30 text-warning cursor-pointer hover:border-warning"
              : "bg-card border-brand-brown-50 cursor-pointer hover:border-brand-gold-dark";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={!day.is_editable}
      className={`aspect-square rounded-md border p-1 text-left transition-colors ${tone}`}
      title={
        day.is_holiday
          ? `Holiday: ${day.holiday_name ?? ""}`
          : day.is_sunday
            ? "Sunday — week off"
            : day.status
      }
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold">{dayNum}</span>
        {day.is_late && (
          <span
            title={day.late_remark ?? "Late arrival"}
            className="h-1.5 w-1.5 rounded-full bg-warning"
          />
        )}
      </div>
      {!upcoming && (
        <div className="text-[10px] font-bold mt-0.5">
          {day.is_holiday
            ? "HOL"
            : day.is_sunday
              ? "SUN"
              : STATUS_LABEL[day.status] ?? day.status}
        </div>
      )}
    </button>
  );
}

function DayEditModal({
  day,
  employeeId,
  onClose,
  onSaved,
}: {
  day: CalendarDay;
  employeeId: number;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [status_, setStatus] = useState<string>(
    day.status === "blank" ||
      day.status === "week_off" ||
      day.status === "holiday" ||
      day.status === "upcoming"
      ? "present"
      : day.status,
  );
  const [workMode, setWorkMode] = useState<string>(day.work_mode ?? "office");
  const [checkIn, setCheckIn] = useState<string>(
    day.check_in ? toTimeInput(day.check_in) : "",
  );
  const [checkOut, setCheckOut] = useState<string>(
    day.check_out ? toTimeInput(day.check_out) : "",
  );
  const [notes, setNotes] = useState<string>(day.notes ?? "");
  const [isLate, setIsLate] = useState<boolean>(day.is_late ?? false);
  const [lateRemark, setLateRemark] = useState<string>(
    day.late_remark ?? "",
  );

  const save = useMutation({
    mutationFn: () =>
      attendanceApi.upsertByDate(employeeId, {
        date: day.date,
        status: status_ as never,
        work_mode: workMode,
        check_in: checkIn ? `${day.date}T${checkIn}:00` : null,
        check_out: checkOut ? `${day.date}T${checkOut}:00` : null,
        notes: notes || null,
        is_late: isLate,
        late_remark: lateRemark || null,
      }),
    onSuccess: () => {
      toast.success("Attendance updated");
      onSaved();
    },
    onError: (e: unknown) => {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Could not save";
      toast.error(detail);
    },
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>{day.date}</CardTitle>
            <CardDescription>Update attendance for this day.</CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Status</Label>
            <select
              value={status_}
              onChange={(e) => setStatus(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
            >
              <option value="present">Present</option>
              <option value="wfh">Work from home</option>
              <option value="half_day">Half day</option>
              <option value="leave">Leave</option>
              <option value="absent">Absent</option>
            </select>
          </div>
          <div>
            <Label>Work mode</Label>
            <select
              value={workMode}
              onChange={(e) => setWorkMode(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
            >
              <option value="office">Office</option>
              <option value="wfh">WFH</option>
              <option value="hybrid">Hybrid</option>
              <option value="field">Field</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Check-in</Label>
              <Input
                type="time"
                value={checkIn}
                onChange={(e) => setCheckIn(e.target.value)}
              />
            </div>
            <div>
              <Label>Check-out</Label>
              <Input
                type="time"
                value={checkOut}
                onChange={(e) => setCheckOut(e.target.value)}
              />
            </div>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              className="accent-brand-gold-dark"
              checked={isLate}
              onChange={(e) => setIsLate(e.target.checked)}
            />
            Mark as late arrival
          </label>
          {isLate && (
            <div>
              <Label>Late remark</Label>
              <Input
                value={lateRemark}
                onChange={(e) => setLateRemark(e.target.value)}
                placeholder="e.g. Reported at 10:45 — traffic"
              />
            </div>
          )}
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
            <Button disabled={save.isPending} onClick={() => save.mutate()}>
              {save.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function toTimeInput(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, "0")}:${String(
    d.getMinutes(),
  ).padStart(2, "0")}`;
}

// For a cycle whose start day is N (>1), the period that "belongs to"
// month m in year y runs from N of the previous month to N-1 of month m.
function cycleRangeLabel(y: number, m: number, startDay: number): string {
  const fmt = (d: Date) =>
    `${d.getDate()} ${MONTHS[d.getMonth()]}`;
  const prevMonthDate = new Date(y, m - 2, 1); // m is 1-based; m-2 = prev month
  const lastOfPrev = new Date(
    prevMonthDate.getFullYear(),
    prevMonthDate.getMonth() + 1,
    0,
  ).getDate();
  const startDom = Math.min(startDay, lastOfPrev);
  const start = new Date(
    prevMonthDate.getFullYear(),
    prevMonthDate.getMonth(),
    startDom,
  );
  const lastOfThis = new Date(y, m, 0).getDate();
  const endDom = Math.min(startDay - 1, lastOfThis);
  const end = new Date(y, m - 1, endDom);
  return `${fmt(start)} – ${fmt(end)}`;
}
