import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { fetchHealth } from "@/lib/api/health";
import { Users, CalendarCheck, Wallet, ClipboardList } from "lucide-react";

const STATS = [
  { label: "Employees", value: "—", hint: "Phase 2", icon: Users },
  { label: "Present Today", value: "—", hint: "Phase 3", icon: CalendarCheck },
  { label: "Pending Approvals", value: "—", hint: "Phase 4", icon: ClipboardList },
  { label: "Payroll (MTD)", value: "—", hint: "Phase 7", icon: Wallet },
];

export default function DashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 15_000,
  });

  return (
    <div className="space-y-8">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Overview
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          Today, at a <span className="display-em">glance</span>
        </h2>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ label, value, hint, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                  {label}
                </span>
                <Icon className="h-4 w-4 text-brand-gold-dark" />
              </div>
              <div className="font-display text-3xl font-bold text-brand-brown-darker">
                {value}
              </div>
              <div className="mt-1 text-xs text-brand-brown-light">{hint}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            Backend <span className="display-em">health</span>
          </CardTitle>
          <CardDescription>
            Live status from <code className="font-mono">/health</code>.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="text-sm text-brand-brown-light">Pinging…</div>
          )}
          {isError && (
            <div className="text-sm text-error">
              Could not reach the backend. Is{" "}
              <code className="font-mono">uvicorn</code> running on :8000?
            </div>
          )}
          {data && (
            <dl className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
              <Row k="App" v={data.app} />
              <Row k="Version" v={data.version} />
              <Row k="Env" v={data.environment} />
              <Row k="Company" v={data.company} />
              <Row k="DB" v={data.db} />
              <Row k="Redis" v={data.redis} />
            </dl>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div>
      <dt className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
        {k}
      </dt>
      <dd className="font-medium text-brand-brown-darker">{v}</dd>
    </div>
  );
}
