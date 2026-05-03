import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Download, FileDown } from "lucide-react";

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
  employeesApi,
  type EmployeeListItem,
} from "@/lib/api/employees";

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

function firstOfMonthISO(): string {
  const d = new Date();
  return new Date(d.getFullYear(), d.getMonth(), 1)
    .toISOString()
    .slice(0, 10);
}

export default function ExportReportPage() {
  const [from, setFrom] = useState(firstOfMonthISO());
  const [to, setTo] = useState(todayISO());
  const [search, setSearch] = useState("");
  const [picks, setPicks] = useState<Set<number>>(new Set());
  const [downloading, setDownloading] = useState(false);

  const { data: employees = [], isLoading } = useQuery({
    queryKey: ["employees-active"],
    queryFn: () => employeesApi.list(),
  });

  const activeEmployees = useMemo(
    () => employees.filter((e) => e.status === "active"),
    [employees],
  );

  const filtered = useMemo(() => {
    if (!search.trim()) return activeEmployees;
    const q = search.toLowerCase();
    return activeEmployees.filter(
      (e) =>
        e.employee_code.toLowerCase().includes(q) ||
        `${e.first_name} ${e.last_name}`.toLowerCase().includes(q) ||
        (e.department?.name ?? "").toLowerCase().includes(q),
    );
  }, [activeEmployees, search]);

  // Auto-select all on first load
  useEffect(() => {
    if (picks.size === 0 && activeEmployees.length > 0) {
      setPicks(new Set(activeEmployees.map((e) => e.id)));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeEmployees]);

  const allSelected =
    picks.size > 0 && picks.size === activeEmployees.length;

  const togglePick = (id: number) => {
    const next = new Set(picks);
    next.has(id) ? next.delete(id) : next.add(id);
    setPicks(next);
  };

  const toggleAll = () => {
    if (allSelected) setPicks(new Set());
    else setPicks(new Set(activeEmployees.map((e) => e.id)));
  };

  const download = async () => {
    if (!from || !to) {
      toast.error("Pick a date range");
      return;
    }
    if (picks.size === 0) {
      toast.error("Select at least one employee");
      return;
    }
    setDownloading(true);
    try {
      const params: Record<string, string> = {
        from_date: from,
        to_date: to,
      };
      if (!allSelected) {
        params.employee_ids = Array.from(picks).join(",");
      }
      const res = await apiClient.get(
        "/api/v1/reports/attendance-payroll-export.csv",
        { params, responseType: "blob" },
      );
      const blob = new Blob([res.data], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `jaikalki-attendance-payroll-${from}-${to}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`Exported ${picks.size} employees`);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Export failed";
      toast.error(detail);
    } finally {
      setDownloading(false);
    }
  };

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Reports · Export
        </div>
        <h2 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
          Attendance &amp; salary <span className="display-em">export</span>
        </h2>
        <p className="mt-1 text-sm text-brand-brown-light">
          Pick a date range and the employees you want, then download a
          CSV with day-by-day attendance plus calculated salary for the
          period.
        </p>
      </div>

      <div className="grid lg:grid-cols-[24rem_1fr] gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Date range</CardTitle>
            <CardDescription>
              Inclusive on both ends. Salary is pro-rated by working days
              in this range.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label>From</Label>
              <Input
                type="date"
                value={from}
                max={to}
                onChange={(e) => setFrom(e.target.value)}
              />
            </div>
            <div>
              <Label>To</Label>
              <Input
                type="date"
                value={to}
                min={from}
                max={todayISO()}
                onChange={(e) => setTo(e.target.value)}
              />
            </div>
            <div className="flex flex-wrap gap-2 pt-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setFrom(firstOfMonthISO());
                  setTo(todayISO());
                }}
              >
                This month
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  const d = new Date();
                  d.setMonth(d.getMonth() - 1);
                  const last = new Date(d.getFullYear(), d.getMonth() + 1, 0);
                  setFrom(
                    new Date(d.getFullYear(), d.getMonth(), 1)
                      .toISOString()
                      .slice(0, 10),
                  );
                  setTo(last.toISOString().slice(0, 10));
                }}
              >
                Last month
              </Button>
            </div>

            <div className="border-t border-brand-brown-50 pt-4">
              <Button
                disabled={downloading || picks.size === 0}
                onClick={download}
                className="w-full"
              >
                {downloading ? (
                  "Generating…"
                ) : (
                  <>
                    <Download className="h-4 w-4 mr-1" />
                    Download CSV ({picks.size})
                  </>
                )}
              </Button>
              <div className="text-xs text-brand-brown-light mt-2">
                Columns: code · name · category · from / to · totals per
                status (present / wfh / half-day / absent / leave) ·
                holidays · CTC monthly · gross · net · earned gross / net
                for the period.
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between gap-2 flex-wrap">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileDown className="h-5 w-5" /> Employees
              </CardTitle>
              <CardDescription>
                {activeEmployees.length} active · {picks.size} selected
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={toggleAll}>
                {allSelected ? "Clear all" : "Select all"}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <Input
              placeholder="Search by code, name, or department…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div className="border border-brand-brown-50 rounded-lg max-h-[28rem] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-brand-brown-light bg-brand-brown-50 sticky top-0">
                  <tr>
                    <th className="py-2 px-3 w-10"></th>
                    <th>Code</th>
                    <th>Name</th>
                    <th>Department</th>
                    <th>Designation</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((e: EmployeeListItem) => (
                    <tr
                      key={e.id}
                      className="border-t border-brand-brown-50 hover:bg-brand-brown-50/40 cursor-pointer"
                      onClick={() => togglePick(e.id)}
                    >
                      <td className="py-2 px-3">
                        <input
                          type="checkbox"
                          checked={picks.has(e.id)}
                          onChange={() => togglePick(e.id)}
                          onClick={(ev) => ev.stopPropagation()}
                        />
                      </td>
                      <td className="font-mono text-xs">{e.employee_code}</td>
                      <td>
                        {e.first_name} {e.last_name}
                      </td>
                      <td className="text-brand-brown-light">
                        {e.department?.name ?? "—"}
                      </td>
                      <td className="text-brand-brown-light">
                        {e.designation?.name ?? "—"}
                      </td>
                    </tr>
                  ))}
                  {filtered.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        className="text-center py-6 text-brand-brown-light"
                      >
                        No matches
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
