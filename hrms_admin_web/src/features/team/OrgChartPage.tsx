// Org chart: the reporting tree you can see (the whole company for
// Director / HR / Admin), with today's status and team size on each
// person. Click someone for their details, or open their team.
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight, Search, Users } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { DAY_STATUS, teamApi, type OrgNode } from "@/lib/api/team";
import { cn } from "@/lib/utils";
import { todayIso } from "@/features/employees/profile/ui";
import { MemberPanel } from "./MemberPanel";
import { Avatar } from "./shared";

const DOT: Record<string, string> = {
  success: "bg-success",
  warning: "bg-warning",
  error: "bg-error",
  info: "bg-info",
  gold: "bg-brand-gold",
  neutral: "bg-brand-brown-100",
};

function matches(n: OrgNode, q: string): boolean {
  return (
    n.name.toLowerCase().includes(q) ||
    (n.designation ?? "").toLowerCase().includes(q) ||
    (n.department ?? "").toLowerCase().includes(q) ||
    n.employee_code.toLowerCase().includes(q)
  );
}

export default function OrgChartPage() {
  const navigate = useNavigate();
  const { data: roots = [], isLoading } = useQuery({
    queryKey: ["org-chart"],
    queryFn: () => teamApi.orgChart(),
  });
  const [q, setQ] = useState("");
  const [collapsed, setCollapsed] = useState<Set<number>>(new Set());
  const [open, setOpen] = useState<number | null>(null);
  const query = q.trim().toLowerCase();

  // With a search, keep only matches and the managers above them.
  const shown = useMemo(() => {
    if (!query) return roots;
    const prune = (n: OrgNode): OrgNode | null => {
      const kids = n.children.map(prune).filter(Boolean) as OrgNode[];
      return matches(n, query) || kids.length ? { ...n, children: kids } : null;
    };
    return roots.map(prune).filter(Boolean) as OrgNode[];
  }, [roots, query]);

  const total = useMemo(() => roots.reduce((s, r) => s + 1 + r.team_size, 0), [roots]);

  if (isLoading) return <LoadingScreen label="Loading org chart…" />;

  const toggle = (id: number) =>
    setCollapsed((c) => {
      const n = new Set(c);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  const renderNode = (n: OrgNode): React.ReactNode => {
    const isOpen = !!query || !collapsed.has(n.employee_id);
    const st = DAY_STATUS[n.status_today];
    return (
      <li key={n.employee_id}>
        <div className="group flex items-center gap-2 rounded-lg py-1.5 pr-2 hover:bg-brand-brown-50/50">
          <button
            type="button"
            className={cn("grid size-6 place-items-center rounded text-brand-brown-light", !n.children.length && "invisible")}
            onClick={() => toggle(n.employee_id)}
            aria-label={isOpen ? "Collapse" : "Expand"}
          >
            {isOpen ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
          </button>
          <button type="button" className="flex min-w-0 flex-1 items-center gap-3 text-left" onClick={() => setOpen(n.employee_id)}>
            <Avatar name={n.name} photo={n.photo_url} size={32} />
            <span className="min-w-0">
              <span className="block truncate font-medium text-brand-brown-darker">{n.name}</span>
              <span className="block truncate text-xs text-brand-brown-light">
                {[n.designation, n.department].filter(Boolean).join(" · ") || n.employee_code}
              </span>
            </span>
          </button>
          <span className="flex shrink-0 items-center gap-1.5 text-xs text-brand-brown-light" title={`Today: ${st.label}`}>
            <span className={cn("size-2 rounded-full", DOT[st.tone])} /> {st.label}
          </span>
          {n.team_size > 0 && (
            <Link
              to={`/team?root=${n.employee_id}`}
              className="ml-2 flex shrink-0 items-center gap-1 rounded-full bg-brand-gold/15 px-2 py-0.5 text-xs text-brand-gold-dark hover:bg-brand-gold/25"
              title="Open their team"
            >
              <Users className="size-3" /> {n.team_size}
            </Link>
          )}
        </div>
        {isOpen && n.children.length > 0 && (
          <ul className="ml-3 border-l border-brand-brown-100 pl-3">
            {n.children.map((c) => renderNode(c))}
          </ul>
        )}
      </li>
    );
  };

  const allIds = (ns: OrgNode[]): number[] => ns.flatMap((n) => [n.employee_id, ...allIds(n.children)]);

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader className="flex flex-row flex-wrap items-start justify-between gap-3 space-y-0">
          <div>
            <CardTitle>Org chart</CardTitle>
            <CardDescription className="mt-1">
              {total} people · who reports to whom, with today's attendance. Click a person for details;
              the number opens their team.
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 size-4 text-brand-brown-light" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Find a person, role or department"
                className="w-72 pl-8"
              />
            </div>
            <Button variant="outline" size="sm" onClick={() => setCollapsed(new Set())}>
              Expand all
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCollapsed(new Set(allIds(roots).filter((id) => id !== roots[0]?.employee_id)))}
            >
              Collapse
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {shown.length === 0 ? (
            <p className="py-8 text-center text-sm text-brand-brown-light">
              {query ? "Nobody matches that search." : "No one to show yet."}
            </p>
          ) : (
            <ul className="space-y-0.5">{shown.map((r) => renderNode(r))}</ul>
          )}
        </CardContent>
      </Card>
      {open && (
        <MemberPanel
          employeeId={open}
          day={todayIso()}
          onClose={() => setOpen(null)}
          onOpenTeam={(id) => navigate(`/team?root=${id}`)}
        />
      )}
    </div>
  );
}
