import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus } from "lucide-react";

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
import { fieldApi } from "@/lib/api/field";
import { employeesApi } from "@/lib/api/employees";

const JOB_TYPES = [
  "sales_call",
  "demo",
  "service",
  "delivery",
  "training",
  "collection",
  "survey",
  "other",
];

const PRIORITIES = ["low", "medium", "high", "urgent"];

export default function FieldJobsPage() {
  const qc = useQueryClient();
  const today = new Date().toISOString().slice(0, 10);

  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [customerId, setCustomerId] = useState<number | "">("");
  const [jobType, setJobType] = useState("sales_call");
  const [priority, setPriority] = useState("medium");
  const [scheduledDate, setScheduledDate] = useState(today);
  const [scheduledTime, setScheduledTime] = useState("");
  const [notes, setNotes] = useState("");

  const { data: customers = [], isLoading: loadingCust } = useQuery({
    queryKey: ["field-customers"],
    queryFn: () => fieldApi.listCustomers(),
  });
  const { data: employees = [], isLoading: loadingEmps } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });
  const { data: performance = [] } = useQuery({
    queryKey: ["field-performance", today],
    queryFn: () => fieldApi.teamPerformance(today),
  });

  const assign = useMutation({
    mutationFn: () =>
      fieldApi.assignJob({
        employee_id: Number(employeeId),
        customer_id: Number(customerId),
        job_type: jobType,
        scheduled_date: scheduledDate,
        scheduled_time: scheduledTime || undefined,
        priority: priority as "low" | "medium" | "high" | "urgent",
        notes: notes || undefined,
      }),
    onSuccess: () => {
      toast.success("Job assigned");
      setEmployeeId("");
      setCustomerId("");
      setNotes("");
      setScheduledTime("");
      qc.invalidateQueries({ queryKey: ["field-performance"] });
    },
    onError: () => toast.error("Could not assign job"),
  });

  if (loadingCust || loadingEmps) return <LoadingScreen label="Loading…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Field Jobs
        </h1>
        <p className="text-sm text-brand-brown-light">
          Assign daily plans to field employees. Jobs trigger geo-fenced check-ins.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Assign new job</CardTitle>
          <CardDescription>
            The employee will see this in today’s plan and must check in within
            200 m of the customer.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>Employee *</Label>
            <select
              value={employeeId}
              onChange={(e) =>
                setEmployeeId(e.target.value ? Number(e.target.value) : "")
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">— Select —</option>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>
                  {emp.employee_code} — {emp.first_name} {emp.last_name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Customer *</Label>
            <select
              value={customerId}
              onChange={(e) =>
                setCustomerId(e.target.value ? Number(e.target.value) : "")
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="">— Select —</option>
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} {c.territory ? `· ${c.territory}` : ""}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Job type</Label>
            <select
              value={jobType}
              onChange={(e) => setJobType(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {JOB_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Priority</Label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Date</Label>
            <Input
              type="date"
              value={scheduledDate}
              onChange={(e) => setScheduledDate(e.target.value)}
            />
          </div>
          <div>
            <Label>Time</Label>
            <Input
              type="time"
              value={scheduledTime}
              onChange={(e) => setScheduledTime(e.target.value)}
            />
          </div>
          <div className="md:col-span-2">
            <Label>Notes</Label>
            <Input value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          <div className="md:col-span-2 flex justify-end">
            <Button
              disabled={!employeeId || !customerId || assign.isPending}
              onClick={() => assign.mutate()}
              className="gap-2"
            >
              <Plus className="size-4" />
              Assign job
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Today's team performance</CardTitle>
          <CardDescription>
            Jobs assigned, completed, in progress — for {today}.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Employee</th>
                <th className="px-4 py-3">Assigned</th>
                <th className="px-4 py-3">Completed</th>
                <th className="px-4 py-3">In progress</th>
                <th className="px-4 py-3">Avg visit (min)</th>
              </tr>
            </thead>
            <tbody>
              {performance.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No jobs scheduled today.
                  </td>
                </tr>
              ) : (
                performance.map((p) => (
                  <tr
                    key={p.employee_id}
                    className="border-t border-brand-brown-50"
                  >
                    <td className="px-4 py-3 font-medium">
                      {p.employee_code} · {p.name}
                    </td>
                    <td className="px-4 py-3">{p.jobs_assigned}</td>
                    <td className="px-4 py-3 text-success">
                      {p.jobs_completed}
                    </td>
                    <td className="px-4 py-3 text-info">
                      {p.visits_in_progress}
                    </td>
                    <td className="px-4 py-3">{p.avg_visit_minutes}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
