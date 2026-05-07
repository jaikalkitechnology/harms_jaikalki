import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Check,
  Download,
  Pencil,
  Save,
  Search,
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
import { apiClient } from "@/lib/api/client";
import {
  attendanceApi,
  type AttendanceRecord,
  type RegularizationRequest,
} from "@/lib/api/attendance";
import { employeesApi, type EmployeeListItem } from "@/lib/api/employees";
import { fmtIst, fmtIstTime } from "@/lib/datetime";

type ViewMode = "day" | "month";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}
function thisMonthISO() {
  return new Date().toISOString().slice(0, 7);
}
function monthRange(month: string): { from: string; to: string } {
  const [y, m] = month.split("-").map(Number);
  const first = new Date(y, m - 1, 1);
  const last = new Date(y, m, 0);
  return {
    from: first.toISOString().slice(0, 10),
    to: last.toISOString().slice(0, 10),
  };
}

const STATUS_COLOR: Record<string, string> = {
  present: "bg-success/15 text-success",
  wfh: "bg-info/15 text-info",
  half_day: "bg-warning/15 text-warning",
  absent: "bg-error/15 text-error",
  leave: "bg-brand-gold/15 text-brand-gold-dark",
  holiday: "bg-brand-brown-50 text-brand-brown-darker",
};

export default function AttendancePage() {
  const [view, setView] = useState<ViewMode>("day");
  const [day, setDay] = useState(todayISO());
  const [month, setMonth] = useState(thisMonthISO());
  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [empSearch, setEmpSearch] = useState("");
  const [editing, setEditing] = useState<AttendanceRecord | null>(null);

  const { data: employees = [] } = useQuery({
    queryKey: ["employees-active-att"],
    queryFn: () => employeesApi.list(),
  });

  const empById = useMemo(() => {
    const m = new Map<number, EmployeeListItem>();
    employees.forEach((e) => m.set(e.id, e));
    return m;
  }, [employees]);

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

  // ── Day view: backend /team
  const dayQuery = useQuery({
    queryKey: ["attendance-team", day, employeeId],
    queryFn: () => attendanceApi.team(day),
    enabled: view === "day",
  });

  // ── Month view: backend /report
  const monthRangeISO = useMemo(() => monthRange(month), [month]);
  const monthQuery = useQuery({
    queryKey: ["attendance-report", monthRangeISO, employeeId],
    queryFn: () =>
      attendanceApi.report({
        from_date: monthRangeISO.from,
        to_date: monthRangeISO.to,
        employee_id: employeeId === "" ? undefined : employeeId,
      }),
    enabled: view === "month",
  });

  const records = useMemo(() => {
    let list = view === "day" ? dayQuery.data ?? [] : monthQuery.data ?? [];
    if (employeeId !== "") list = list.filter((r) => r.employee_id === employeeId);
    return list;
  }, [view, dayQuery.data, monthQuery.data, employeeId]);

  const present = records.filter((r) => r.status === "present").length;
  const wfh = records.filter((r) => r.status === "wfh").length;
  const halfDay = records.filter((r) => r.status === "half_day").length;
  const onLeave = records.filter((r) => r.status === "leave").length;
  const absent = records.filter((r) => r.status === "absent").length;

  const isLoading =
    (view === "day" && dayQuery.isLoading) ||
    (view === "month" && monthQuery.isLoading);

  const downloadCsv = async () => {
    const params =
      view === "day"
        ? { from_date: day, to_date: day }
        : { from_date: monthRangeISO.from, to_date: monthRangeISO.to };
    const finalParams = {
      ...params,
      ...(employeeId === "" ? {} : { employee_id: employeeId as number }),
    };
    try {
      const res = await apiClient.get(
        attendanceApi.exportCsvUrl(finalParams),
        { responseType: "blob" },
      );
      const blob = new Blob([res.data], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `attendance-${finalParams.from_date}-${finalParams.to_date}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`Exported ${records.length} rows`);
    } catch {
      toast.error("Export failed");
    }
  };

  if (isLoading) return <LoadingScreen label="Loading attendance…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Attendance
          </div>
          <h2 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            {view === "day"
              ? "Day-by-day attendance"
              : "Month attendance"}
          </h2>
        </div>
        <div className="flex flex-wrap gap-2 items-end">
          <div className="inline-flex border border-brand-brown-50 rounded-lg p-0.5 bg-card">
            <button
              onClick={() => setView("day")}
              className={`px-3 py-1.5 text-xs rounded ${
                view === "day"
                  ? "bg-brand-gold/15 text-brand-brown-darker"
                  : "text-brand-brown-light"
              }`}
            >
              Day
            </button>
            <button
              onClick={() => setView("month")}
              className={`px-3 py-1.5 text-xs rounded ${
                view === "month"
                  ? "bg-brand-gold/15 text-brand-brown-darker"
                  : "text-brand-brown-light"
              }`}
            >
              Month
            </button>
          </div>
          {view === "day" ? (
            <Input
              type="date"
              value={day}
              onChange={(e) => setDay(e.target.value)}
              className="w-44"
            />
          ) : (
            <Input
              type="month"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="w-44"
            />
          )}
          <Button onClick={downloadCsv} variant="outline">
            <Download className="h-4 w-4 mr-1" /> Export CSV
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filter by employee</CardTitle>
          <CardDescription>
            {employees.length} employees · {records.length} rows in view
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
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
              <option value="">All employees</option>
              {filteredEmployees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.employee_code} — {e.first_name} {e.last_name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-wrap gap-2">
            <Stat label="Present" value={present} accent="success" />
            <Stat label="WFH" value={wfh} accent="info" />
            <Stat label="Half day" value={halfDay} accent="warning" />
            <Stat label="On leave" value={onLeave} accent="gold" />
            <Stat label="Absent" value={absent} accent="error" />
          </div>
        </CardContent>
      </Card>

      <RegularizationQueue empById={empById} />

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm min-w-[760px]">
            <thead className="text-left text-brand-brown-light bg-brand-brown-50">
              <tr>
                <th className="py-2 px-4">Date</th>
                <th>Employee</th>
                <th>Status</th>
                <th>Work mode</th>
                <th>Check in</th>
                <th>Check out</th>
                <th>Hours</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => {
                const e = empById.get(r.employee_id);
                return (
                  <tr
                    key={r.id}
                    className="border-t border-brand-brown-50 hover:bg-brand-brown-50/30"
                  >
                    <td className="py-2 px-4 font-mono text-xs">{r.date}</td>
                    <td>
                      {e
                        ? `${e.employee_code} · ${e.first_name} ${e.last_name}`
                        : `Employee #${r.employee_id}`}
                    </td>
                    <td>
                      <span
                        className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded ${
                          STATUS_COLOR[r.status] ?? ""
                        }`}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="text-xs text-brand-brown-light">
                      {r.work_mode}
                    </td>
                    <td className="text-xs">
                      {r.check_in ? fmtIstTime(r.check_in) : "—"}
                    </td>
                    <td className="text-xs">
                      {r.check_out ? fmtIstTime(r.check_out) : "—"}
                    </td>
                    <td className="text-xs">
                      {Math.round(r.total_minutes / 60)}h{" "}
                      {r.total_minutes % 60}m
                    </td>
                    <td className="text-right pr-4">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setEditing(r)}
                      >
                        <Pencil className="h-3 w-3" />
                      </Button>
                    </td>
                  </tr>
                );
              })}
              {records.length === 0 && (
                <tr>
                  <td
                    colSpan={8}
                    className="text-center py-8 text-brand-brown-light"
                  >
                    No attendance recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {editing && (
        <EditorModal
          record={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            dayQuery.refetch();
            monthQuery.refetch();
          }}
        />
      )}
    </div>
  );
}

type StatAccent = "success" | "info" | "warning" | "error" | "gold";
const STAT_TINT: Record<StatAccent, string> = {
  success: "bg-success/15 text-success",
  info: "bg-info/15 text-info",
  warning: "bg-warning/15 text-warning",
  error: "bg-error/15 text-error",
  gold: "bg-brand-gold/15 text-brand-gold-dark",
};

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: StatAccent;
}) {
  return (
    <div className={`px-4 py-2 rounded-xl ${STAT_TINT[accent]}`}>
      <div className="text-[10px] font-mono uppercase tracking-[0.2em]">
        {label}
      </div>
      <div className="font-display text-2xl font-bold">{value}</div>
    </div>
  );
}

function EditorModal({
  record,
  onClose,
  onSaved,
}: {
  record: AttendanceRecord;
  onClose: () => void;
  onSaved: () => void;
}) {
  const qc = useQueryClient();
  const [draft, setDraft] = useState({
    status: record.status,
    work_mode: record.work_mode,
    check_in: record.check_in ? record.check_in.slice(0, 16) : "",
    check_out: record.check_out ? record.check_out.slice(0, 16) : "",
    notes: record.notes ?? "",
  });

  const save = useMutation({
    mutationFn: () =>
      attendanceApi.update(record.id, {
        status: draft.status,
        work_mode: draft.work_mode,
        check_in: draft.check_in ? new Date(draft.check_in).toISOString() : null,
        check_out: draft.check_out ? new Date(draft.check_out).toISOString() : null,
        notes: draft.notes || null,
      }),
    onSuccess: () => {
      toast.success("Saved");
      qc.invalidateQueries({ queryKey: ["attendance-team"] });
      qc.invalidateQueries({ queryKey: ["attendance-report"] });
      onSaved();
      onClose();
    },
    onError: () => toast.error("Save failed"),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-start md:items-center justify-center p-4 bg-black/40">
      <div className="bg-card rounded-xl border border-brand-brown-100 shadow-xl w-full max-w-md flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-brand-brown-100">
          <div className="font-display text-lg">Edit attendance · {record.date}</div>
          <button
            onClick={onClose}
            className="h-8 w-8 grid place-items-center rounded-lg hover:bg-brand-brown-50"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
        <div className="p-4 space-y-3">
          <div>
            <Label>Status</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.status}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  status: e.target.value as AttendanceRecord["status"],
                })
              }
            >
              {(["present", "absent", "half_day", "wfh", "leave", "holiday"] as const).map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Work mode</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.work_mode}
              onChange={(e) =>
                setDraft({ ...draft, work_mode: e.target.value })
              }
            >
              {["office", "wfh", "hybrid", "field"].map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label>Check in</Label>
              <Input
                type="datetime-local"
                value={draft.check_in}
                onChange={(e) =>
                  setDraft({ ...draft, check_in: e.target.value })
                }
              />
            </div>
            <div>
              <Label>Check out</Label>
              <Input
                type="datetime-local"
                value={draft.check_out}
                onChange={(e) =>
                  setDraft({ ...draft, check_out: e.target.value })
                }
              />
            </div>
          </div>
          <div>
            <Label>Notes</Label>
            <textarea
              rows={2}
              className="w-full border border-brand-brown-50 rounded p-2 text-sm bg-card"
              value={draft.notes}
              onChange={(e) => setDraft({ ...draft, notes: e.target.value })}
            />
          </div>
        </div>
        <div className="p-4 border-t border-brand-brown-100 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={() => save.mutate()} disabled={save.isPending}>
            <Save className="h-4 w-4 mr-1" /> Save
          </Button>
        </div>
      </div>
    </div>
  );
}

function RegularizationQueue({
  empById,
}: {
  empById: Map<number, EmployeeListItem>;
}) {
  const queryClient = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["regularizations-pending"],
    queryFn: attendanceApi.pendingRegularizations,
  });

  const approve = useMutation({
    mutationFn: (id: number) => attendanceApi.approveRegularization(id),
    onSuccess: () => {
      toast.success("Regularization approved");
      queryClient.invalidateQueries({ queryKey: ["regularizations-pending"] });
      queryClient.invalidateQueries({ queryKey: ["attendance-team"] });
    },
  });
  const reject = useMutation({
    mutationFn: (id: number) =>
      attendanceApi.rejectRegularization(id, "Rejected"),
    onSuccess: () => {
      toast.success("Rejected");
      queryClient.invalidateQueries({ queryKey: ["regularizations-pending"] });
    },
  });

  if (isLoading || data.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Regularization queue</CardTitle>
        <CardDescription>
          {data.length} pending correction request{data.length === 1 ? "" : "s"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {data.map((r) => (
          <RegRow
            key={r.id}
            req={r}
            empById={empById}
            onApprove={() => approve.mutate(r.id)}
            onReject={() => reject.mutate(r.id)}
          />
        ))}
      </CardContent>
    </Card>
  );
}

function RegRow({
  req,
  empById,
  onApprove,
  onReject,
}: {
  req: RegularizationRequest;
  empById: Map<number, EmployeeListItem>;
  onApprove: () => void;
  onReject: () => void;
}) {
  const e = empById.get(req.employee_id);
  return (
    <div className="flex items-start justify-between py-2 border-b border-brand-brown-100/50 last:border-0">
      <div className="min-w-0">
        <div className="font-medium text-sm">
          {e ? `${e.employee_code} · ${e.first_name} ${e.last_name}` : `Employee #${req.employee_id}`}{" "}
          · {req.date}
        </div>
        <div className="text-xs text-brand-brown-light">
          {req.requested_check_in && fmtIst(req.requested_check_in)}{" "}
          {req.requested_check_out && `→ ${fmtIst(req.requested_check_out)}`}
        </div>
        <p className="text-xs mt-1">{req.reason}</p>
      </div>
      <div className="flex gap-2">
        <Button size="sm" variant="gold" onClick={onApprove}>
          <Check className="h-3.5 w-3.5" /> Approve
        </Button>
        <Button size="sm" variant="outline" onClick={onReject}>
          <X className="h-3.5 w-3.5" /> Reject
        </Button>
      </div>
    </div>
  );
}
