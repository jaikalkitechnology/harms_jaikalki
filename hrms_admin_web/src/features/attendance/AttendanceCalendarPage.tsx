import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ArrowLeft, ArrowRight, X, Search } from "lucide-react";

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
import {
  attendanceApi,
  type CalendarDay,
} from "@/lib/api/attendance";
import { employeesApi } from "@/lib/api/employees";

const STATUS_LABEL: Record<string, string> = {
  present: "Present",
  absent: "Absent",
  half_day: "Half day",
  wfh: "WFH",
  leave: "Leave",
  holiday: "Holiday",
  week_off: "Sunday",
  upcoming: "—",
  blank: "—",
};

const STATUS_BG: Record<string, string> = {
  present: "bg-success/15 text-success",
  wfh: "bg-info/15 text-info",
  half_day: "bg-warning/15 text-warning",
  absent: "bg-error/15 text-error",
  leave: "bg-brand-gold/15 text-brand-gold-dark",
  holiday: "bg-error/15 text-error",
  week_off: "bg-error/15 text-error",
  upcoming: "bg-brand-brown-50 text-brand-brown-light",
};

function ymOf(d: Date) {
  return { y: d.getFullYear(), m: d.getMonth() + 1 };
}

export default function AttendanceCalendarPage() {
  const today = new Date();
  const [{ y, m }, setYm] = useState(ymOf(today));
  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [empSearch, setEmpSearch] = useState("");
  const [editing, setEditing] = useState<CalendarDay | null>(null);

  const { data: employees = [] } = useQuery({
    queryKey: ["employees-active-att"],
    queryFn: () => employeesApi.list(),
  });

  const filteredEmployees = useMemo(
    () =>
      employees.filter(
        (e) =>
          !empSearch ||
          e.employee_code.toLowerCase().includes(empSearch.toLowerCase()) ||
          `${e.first_name} ${e.last_name}`
            .toLowerCase()
            .includes(empSearch.toLowerCase()),
      ),
    [employees, empSearch],
  );

  const calendarQuery = useQuery({
    queryKey: ["attendance-calendar", employeeId, y, m],
    queryFn: () =>
      attendanceApi.employeeCalendar(Number(employeeId), y, m),
    enabled: employeeId !== "",
  });

  const cal = calendarQuery.data;

  // 7-column grid that pads the leading blanks (week starts Mon).
  const grid = useMemo(() => {
    if (!cal) return [];
    const first = new Date(cal.year, cal.month - 1, 1);
    // Convert JS getDay() (Sun=0..Sat=6) to Mon=0..Sun=6 to match backend weekday.
    const firstWd = (first.getDay() + 6) % 7;
    const out: Array<CalendarDay | null> = [];
    for (let i = 0; i < firstWd; i++) out.push(null);
    out.push(...cal.days);
    while (out.length % 7 !== 0) out.push(null);
    return out;
  }, [cal]);

  function shift(delta: number) {
    let ny = y;
    let nm = m + delta;
    if (nm < 1) {
      nm = 12;
      ny -= 1;
    } else if (nm > 12) {
      nm = 1;
      ny += 1;
    }
    setYm({ y: ny, m: nm });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Attendance · Calendar
          </div>
          <h2 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            Edit any past <span className="display-em">day</span>
          </h2>
          <p className="text-sm text-brand-brown-light mt-1">
            Sundays and holidays are red and locked. Click any other day
            to add or correct attendance.
          </p>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="outline" size="sm" onClick={() => shift(-1)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="px-3 py-1.5 rounded border border-brand-brown-50 bg-card text-sm font-medium min-w-[10rem] text-center">
            {new Date(y, m - 1, 1).toLocaleString("default", {
              month: "long",
              year: "numeric",
            })}
          </div>
          <Button variant="outline" size="sm" onClick={() => shift(1)}>
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pick an employee</CardTitle>
          <CardDescription>
            Calendar shows attendance, leaves, holidays and week-offs at
            once. Editing is admin-only.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-[16rem_1fr] gap-3">
            <div className="relative">
              <Search className="h-4 w-4 absolute left-2 top-1/2 -translate-y-1/2 text-brand-brown-light" />
              <Input
                placeholder="Search employees…"
                value={empSearch}
                onChange={(e) => setEmpSearch(e.target.value)}
                className="pl-8"
              />
            </div>
            <select
              className="h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={employeeId}
              onChange={(e) =>
                setEmployeeId(e.target.value ? Number(e.target.value) : "")
              }
            >
              <option value="">Select an employee…</option>
              {filteredEmployees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.employee_code} — {e.first_name} {e.last_name}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {employeeId === "" ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-brand-brown-light">
            Pick an employee above to see their calendar.
          </CardContent>
        </Card>
      ) : calendarQuery.isLoading ? (
        <LoadingScreen label="Loading calendar…" />
      ) : !cal ? null : (
        <>
          <div className="flex flex-wrap gap-2">
            <Stat label="Working" value={cal.working_days} />
            <Stat label="Present" value={cal.days_present} accent="success" />
            <Stat label="WFH" value={cal.days_wfh} accent="info" />
            <Stat label="Half-day" value={cal.days_half_day} accent="warning" />
            <Stat label="Leave" value={cal.days_leave} accent="gold" />
            <Stat label="Absent" value={cal.days_absent} accent="error" />
            <Stat label="Holiday" value={cal.days_holiday} accent="error" />
            <Stat label="Sundays" value={cal.days_weekoff} accent="error" />
          </div>

          <Card>
            <CardContent className="p-4">
              <div className="grid grid-cols-7 gap-1 text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-2">
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
            </CardContent>
          </Card>
        </>
      )}

      {editing && employeeId !== "" && (
        <DayEditModal
          day={editing}
          employeeId={Number(employeeId)}
          onClose={() => setEditing(null)}
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
  const blocked = !day.is_editable;
  const isUpcoming = day.status === "upcoming";
  // Dates before the employee joined or after their exit_date come back
  // from the API as ``not_in_service`` — grey them out and disable the
  // editor entirely so HR can't back-date onto an inactive record.
  const isNotInService = day.status === "not_in_service";
  const isOffDay = day.is_sunday || day.is_holiday;
  const tone = STATUS_BG[day.status] ?? "bg-brand-brown-50";
  const cellTone = isNotInService
    ? "bg-brand-brown-50/30 border-dashed border-brand-brown-50 cursor-not-allowed opacity-50"
    : isOffDay
      ? "bg-error/10 border-error/30 cursor-not-allowed"
      : isUpcoming
        ? "bg-brand-brown-50/40 border-brand-brown-50 cursor-not-allowed"
        : "bg-card hover:border-brand-gold-dark border-brand-brown-50 cursor-pointer";
  const numTone = isNotInService
    ? "text-brand-brown-light"
    : isOffDay
      ? "text-error"
      : isUpcoming
        ? "text-brand-brown-light"
        : "text-brand-brown-darker";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={blocked}
      className={`aspect-square rounded-md border text-left p-1.5 transition-colors ${cellTone}`}
      title={
        isNotInService
          ? "Outside the employee's service window (before joining or after exit)"
          : day.is_holiday
          ? `Holiday: ${day.holiday_name ?? ""}`
          : day.is_sunday
            ? "Sunday — week off"
            : isUpcoming
              ? "Upcoming — not editable yet"
              : STATUS_LABEL[day.status] ?? day.status
      }
    >
      <div className="flex items-center justify-between">
        <span className={`text-sm font-semibold ${numTone}`}>{dayNum}</span>
        {day.is_late && (
          <span
            title={day.late_remark ?? "Late arrival"}
            className="h-2 w-2 rounded-full bg-warning"
          />
        )}
      </div>
      {isNotInService ? (
        <div className="text-[9px] text-brand-brown-light mt-0.5">—</div>
      ) : day.is_holiday ? (
        <div className="text-[9px] text-error font-medium truncate mt-0.5">
          {day.holiday_name}
        </div>
      ) : day.is_sunday ? (
        <div className="text-[9px] text-error mt-0.5">Sun</div>
      ) : isUpcoming ? null : (
        <div
          className={`text-[9px] mt-0.5 inline-block px-1 rounded ${tone}`}
        >
          {STATUS_LABEL[day.status] ?? day.status}
        </div>
      )}
    </button>
  );
}

function DayEditModal({
  day,
  employeeId,
  onClose,
}: {
  day: CalendarDay;
  employeeId: number;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [status_, setStatus] = useState<string>(
    day.status === "blank" || day.status === "week_off" || day.status === "holiday"
      ? "present"
      : day.status,
  );
  const [workMode, setWorkMode] = useState<string>(day.work_mode ?? "office");
  const [checkIn, setCheckIn] = useState<string>(
    day.check_in ? toLocalTimeInput(day.check_in) : "",
  );
  const [checkOut, setCheckOut] = useState<string>(
    day.check_out ? toLocalTimeInput(day.check_out) : "",
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
        check_in: checkIn ? combineDateTime(day.date, checkIn) : null,
        check_out: checkOut ? combineDateTime(day.date, checkOut) : null,
        notes: notes || null,
        is_late: isLate,
        late_remark: lateRemark || null,
      }),
    onSuccess: () => {
      toast.success("Attendance updated");
      qc.invalidateQueries({ queryKey: ["attendance-calendar"] });
      qc.invalidateQueries({ queryKey: ["attendance-team"] });
      qc.invalidateQueries({ queryKey: ["attendance-report"] });
      onClose();
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
      <Card className="w-full max-w-lg">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>{day.date}</CardTitle>
            <CardDescription>
              Update attendance for this day.
            </CardDescription>
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

function Stat({
  label,
  value,
  accent = "muted",
}: {
  label: string;
  value: number;
  accent?: "muted" | "success" | "info" | "warning" | "gold" | "error";
}) {
  const cls =
    accent === "success"
      ? "text-success"
      : accent === "info"
        ? "text-info"
        : accent === "warning"
          ? "text-warning"
          : accent === "gold"
            ? "text-brand-gold-dark"
            : accent === "error"
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

function toLocalTimeInput(iso: string): string {
  const d = new Date(iso);
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

function combineDateTime(dateStr: string, hhmm: string): string {
  // dateStr is YYYY-MM-DD, hhmm is HH:MM. Build an ISO timestamp in
  // local time so server interprets check-in/out as wall-clock.
  return `${dateStr}T${hhmm}:00`;
}
