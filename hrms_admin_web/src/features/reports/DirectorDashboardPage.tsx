import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { reportsApi } from "@/lib/api/reports";

const BRAND = ["#3D2817", "#F4B71F", "#5E8B3A", "#2C7A7B", "#C53030", "#5C3D24"];

export default function DirectorDashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["director-dashboard"],
    queryFn: reportsApi.directorDashboard,
  });

  if (isLoading || !data) return <LoadingScreen label="Loading dashboard…" />;

  const compliance = data.compliance;
  const compliancePieData = [
    { name: "Fully", value: compliance.fully_compliant, color: BRAND[2] },
    {
      name: "Partial",
      value: compliance.partially_compliant,
      color: BRAND[1],
    },
    { name: "None", value: compliance.non_compliant, color: BRAND[4] },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Director Dashboard
        </h1>
        <p className="text-sm text-brand-brown-light">
          Real-time view of headcount, attrition, compliance, sales, and ops.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KPI
          label="Active headcount"
          value={data.headcount.current_headcount}
        />
        <KPI
          label="12m attrition"
          value={`${data.attrition.attrition_pct}%`}
          color={data.attrition.attrition_pct > 15 ? "text-error" : "text-success"}
        />
        <KPI
          label="Compliance coverage"
          value={`${compliance.coverage_pct}%`}
          color={
            compliance.coverage_pct >= 90 ? "text-success" : "text-warning"
          }
        />
        <KPI
          label="Verification breach"
          value={`${data.verification.breach_pct}%`}
          color={
            data.verification.breach_pct > 10 ? "text-error" : "text-success"
          }
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Headcount trend</CardTitle>
            <CardDescription>
              Monthly active headcount with new joins and exits.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={data.headcount.points}>
                <CartesianGrid stroke="#E8DACA" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="headcount"
                  stroke={BRAND[0]}
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="joined"
                  stroke={BRAND[2]}
                />
                <Line
                  type="monotone"
                  dataKey="exited"
                  stroke={BRAND[4]}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Department breakdown</CardTitle>
            <CardDescription>
              Active employees per department.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={data.department_breakdown}>
                <CartesianGrid stroke="#E8DACA" />
                <XAxis dataKey="department" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="headcount" fill={BRAND[1]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compliance</CardTitle>
            <CardDescription>
              {compliance.mandatory_courses} mandatory course(s) ·{" "}
              {compliance.employees_total} employees
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={compliancePieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={48}
                  outerRadius={92}
                  dataKey="value"
                  label
                >
                  {compliancePieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Operations summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <Row label="Sales leads (90d)" value={data.sales?.leads_count ?? 0} />
            <Row
              label="Win rate"
              value={`${data.sales?.win_rate_pct ?? 0}%`}
            />
            <Row
              label="Orders booked (90d)"
              value={`₹${Number(data.sales?.orders_total ?? 0).toLocaleString("en-IN")}`}
            />
            <hr className="border-brand-brown-50" />
            <Row label="Verifications total" value={data.verification.total} />
            <Row
              label="Verifications completed"
              value={data.verification.completed}
            />
            <Row
              label="Avg TAT (h)"
              value={data.verification.avg_hours}
            />
            <hr className="border-brand-brown-50" />
            <Row
              label="Training sessions"
              value={`${data.training.sessions_completed}/${data.training.sessions_total} done · ${data.training.upcoming_sessions} upcoming`}
            />
            <Row
              label="Trained attendees"
              value={data.training.total_attendees}
            />
            {data.payroll_this_month && (
              <>
                <hr className="border-brand-brown-50" />
                <Row
                  label={`Payroll cost ${data.payroll_this_month.year}/${String(
                    data.payroll_this_month.month,
                  ).padStart(2, "0")}`}
                  value={`₹${Number(data.payroll_this_month.total_employer_cost).toLocaleString("en-IN")}`}
                />
                <Row
                  label="Avg cost per employee"
                  value={`₹${Number(data.payroll_this_month.avg_cost_per_employee).toLocaleString("en-IN")}`}
                />
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function KPI({
  label,
  value,
  color,
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="text-xs uppercase tracking-wide text-brand-brown-light">
          {label}
        </div>
        <div
          className={`text-3xl font-semibold ${color ?? "text-brand-brown-darker"}`}
        >
          {value}
        </div>
      </CardContent>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-brand-brown-light">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
