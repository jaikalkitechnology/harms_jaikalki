import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { type ColumnDef } from "@tanstack/react-table";
import { Plus } from "lucide-react";

import { DataTable } from "@/components/shared/DataTable";
import { Button } from "@/components/ui/button";
import { PermissionGate } from "@/components/shared/PermissionGate";
import {
  employeesApi,
  lookupsApi,
  type EmployeeListItem,
} from "@/lib/api/employees";
import { useAuthStore } from "@/store/auth";
import { cn } from "@/lib/utils";
import { CategoryBadge } from "./CategoryBadge";
import { LifecycleDrawer } from "./LifecycleDrawer";
import { completenessTone } from "./profile/CompletenessCard";
import { SEPARATED_STATUSES } from "./profile/ExitBanner";
import { daysUntil, fmtDate, tenure } from "./profile/ui";

type StatusFilter = "all" | "active" | "probation" | "notice" | "exited";

const STATUS_FILTERS: { key: StatusFilter; label: string }[] = [
  { key: "all", label: "All" },
  { key: "active", label: "Active" },
  { key: "probation", label: "On probation" },
  { key: "notice", label: "Serving notice" },
  { key: "exited", label: "Resigned / terminated" },
];

/** Separated, with the last working day still ahead (or not yet set). */
function servingNotice(e: EmployeeListItem): boolean {
  return (
    SEPARATED_STATUSES.includes(e.status) &&
    (!e.exit_date || daysUntil(e.exit_date) >= 0)
  );
}

function matchesStatus(e: EmployeeListItem, f: StatusFilter): boolean {
  switch (f) {
    case "active":
      return !SEPARATED_STATUSES.includes(e.status);
    case "probation":
      return !SEPARATED_STATUSES.includes(e.status) && e.is_on_probation;
    case "notice":
      return servingNotice(e);
    case "exited":
      return SEPARATED_STATUSES.includes(e.status) && !servingNotice(e);
    default:
      return true;
  }
}

export default function EmployeesListPage() {
  const navigate = useNavigate();
  const [departmentId, setDepartmentId] = useState<number | undefined>();
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const canSeeCompleteness = useAuthStore((s) => s.hasPermission("employee.update"));
  const [lifecycleFor, setLifecycleFor] = useState<{
    id: number;
    name: string;
  } | null>(null);

  const { data: allEmployees = [], isLoading } = useQuery({
    queryKey: ["employees", { departmentId, categoryId }],
    queryFn: () =>
      employeesApi.list({
        department_id: departmentId,
        category_id: categoryId,
        limit: 500,
      }),
  });
  const employees = useMemo(
    () => allEmployees.filter((e) => matchesStatus(e, statusFilter)),
    [allEmployees, statusFilter],
  );
  const statusCounts = useMemo(() => {
    const out = {} as Record<StatusFilter, number>;
    for (const f of STATUS_FILTERS) {
      out[f.key] = allEmployees.filter((e) => matchesStatus(e, f.key)).length;
    }
    return out;
  }, [allEmployees]);
  const { data: completeness = {} } = useQuery({
    queryKey: ["employees", "completeness"],
    queryFn: employeesApi.completenessAll,
    enabled: canSeeCompleteness,
  });

  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: lookupsApi.departments,
  });
  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: lookupsApi.categories,
  });

  const columns = useMemo<ColumnDef<EmployeeListItem>[]>(
    () => [
      {
        id: "name",
        header: "Employee",
        accessorFn: (e) => `${e.first_name} ${e.last_name} ${e.employee_code}`,
        cell: ({ row }) => {
          const e = row.original;
          return (
            <div className="flex items-center gap-3">
              <div className="grid h-9 w-9 shrink-0 place-items-center overflow-hidden rounded-full bg-brand-gold/20 text-xs font-semibold text-brand-brown-darker">
                {e.photo_url ? (
                  <img src={e.photo_url} alt="" className="h-full w-full object-cover" />
                ) : (
                  `${e.first_name?.[0] ?? ""}${e.last_name?.[0] ?? ""}`.toUpperCase()
                )}
              </div>
              <div className="min-w-0">
                <div className="truncate font-medium">
                  {e.first_name} {e.last_name}
                </div>
                <div className="truncate text-xs text-brand-brown-light">
                  <span className="font-mono">{e.employee_code}</span>
                  {e.designation && ` · ${e.designation.name}`}
                </div>
              </div>
            </div>
          );
        },
      },
      {
        id: "department",
        header: "Department",
        accessorFn: (e) => e.department?.name ?? "—",
      },
      {
        id: "category",
        header: "Category",
        accessorFn: (e) => e.category?.code ?? "—",
        cell: ({ row }) => (
          <CategoryBadge code={row.original.category?.code} />
        ),
      },
      {
        id: "status",
        header: "Status",
        accessorFn: (e) => statusLabel(e),
        cell: ({ row }) => <StatusBadge employee={row.original} />,
      },
      {
        accessorKey: "date_of_joining",
        header: "Joined",
        cell: ({ row }) => {
          const e = row.original;
          if (!e.date_of_joining) return "—";
          const left = SEPARATED_STATUSES.includes(e.status) ? e.exit_date : null;
          return (
            <div>
              <div>{fmtDate(e.date_of_joining)}</div>
              <div className="text-xs text-brand-brown-light">
                {tenure(e.date_of_joining, left)}
                {left && ` · till ${fmtDate(left)}`}
              </div>
            </div>
          );
        },
      },
      ...(canSeeCompleteness
        ? [
            {
              id: "completeness",
              header: "Profile",
              accessorFn: (e: EmployeeListItem) => completeness[e.id]?.percent ?? -1,
              cell: ({ row }: { row: { original: EmployeeListItem } }) => {
                const c = completeness[row.original.id];
                if (!c) return <span className="text-brand-brown-light">—</span>;
                return (
                  <div
                    className="flex items-center gap-2"
                    title={
                      c.missing.length
                        ? `Missing: ${c.missing.map((m) => m.label).join(", ")}`
                        : "Complete"
                    }
                  >
                    <span className="h-1.5 w-14 overflow-hidden rounded-full bg-brand-brown-100">
                      <span
                        className={cn("block h-full rounded-full", completenessTone(c.percent))}
                        style={{ width: `${c.percent}%` }}
                      />
                    </span>
                    <span className="text-xs tabular-nums">{c.percent}%</span>
                  </div>
                );
              },
            } as ColumnDef<EmployeeListItem>,
          ]
        : []),
      {
        id: "lifecycle",
        header: "Lifecycle",
        cell: ({ row }) => (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setLifecycleFor({
                id: row.original.id,
                name: `${row.original.first_name} ${row.original.last_name}`,
              });
            }}
            className={
              "text-[10px] font-mono uppercase tracking-[0.15em] " +
              "px-2 py-1 rounded-md border border-brand-brown-50 " +
              "hover:border-brand-gold-dark hover:text-brand-brown-darker " +
              (row.original.is_on_probation
                ? "text-brand-gold-dark"
                : "text-success")
            }
            title="Manage intern / probation / confirmation"
          >
            {row.original.is_on_probation ? "Manage stage" : "Confirmed"}
          </button>
        ),
      },
    ],
    [canSeeCompleteness, completeness],
  );

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Phase 2 · Employee Master
          </div>
          <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
            Employee <span className="display-em">directory</span>
          </h2>
          <p className="mt-1 text-sm text-brand-brown-light">
            {employees.length} of {allEmployees.length} employees · scope respects your role.
          </p>
        </div>
        <PermissionGate permission="employee.create">
          <Button onClick={() => navigate("/employees/new")}>
            <Plus className="h-4 w-4" />
            Add employee
          </Button>
        </PermissionGate>
      </div>

      <div className="flex flex-wrap gap-1 rounded-xl bg-brand-brown-50/60 p-1 w-fit max-w-full">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.key}
            onClick={() => setStatusFilter(f.key)}
            className={cn(
              "rounded-lg px-3 py-1.5 text-sm transition-colors",
              statusFilter === f.key
                ? "bg-card font-medium text-brand-brown-darker shadow-sm"
                : "text-brand-brown-light hover:text-brand-brown-darker",
            )}
          >
            {f.label}
            <span className="ml-1.5 text-xs text-brand-brown-light tabular-nums">
              {statusCounts[f.key] ?? 0}
            </span>
          </button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <FilterPill
          label="All categories"
          active={categoryId === undefined}
          onClick={() => setCategoryId(undefined)}
        />
        {categories.map((c) => (
          <FilterPill
            key={c.id}
            label={c.name}
            active={categoryId === c.id}
            onClick={() => setCategoryId(c.id)}
          />
        ))}
        <span className="mx-2 w-px bg-brand-brown-100" />
        <FilterPill
          label="All departments"
          active={departmentId === undefined}
          onClick={() => setDepartmentId(undefined)}
        />
        {departments.map((d) => (
          <FilterPill
            key={d.id}
            label={d.name}
            active={departmentId === d.id}
            onClick={() => setDepartmentId(d.id)}
          />
        ))}
      </div>

      <DataTable
        columns={columns}
        data={employees}
        loading={isLoading}
        searchPlaceholder="Search by name, code, email…"
        onRowClick={(e) => navigate(`/employees/${e.id}`)}
        emptyMessage="No employees match these filters."
      />

      {lifecycleFor && (
        <LifecycleDrawer
          employeeId={lifecycleFor.id}
          employeeName={lifecycleFor.name}
          onClose={() => setLifecycleFor(null)}
        />
      )}
    </div>
  );
}

function FilterPill({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`text-[10px] font-mono uppercase tracking-[0.2em] px-3 py-1.5 rounded-full border transition-colors ${
        active
          ? "bg-brand-gold/15 border-brand-gold/40 text-brand-brown-darker"
          : "bg-card border-brand-brown-100 text-brand-brown-light hover:border-brand-gold/40"
      }`}
    >
      {label}
    </button>
  );
}

function statusLabel(e: EmployeeListItem): string {
  switch (e.status) {
    case "resigned":
      return "Resigned";
    case "exited":
    case "separated":
    case "inactive":
      return "Exited";
    case "terminated":
      return "Terminated";
    case "absconded":
      return "Absconded";
    case "on_leave":
      return "On Long Leave";
    default:
      return e.is_on_probation ? "On Probation" : "Confirmed";
  }
}

function StatusBadge({ employee }: { employee: EmployeeListItem }) {
  const label = statusLabel(employee);
  let cls = "bg-success/10 text-success";
  if (employee.status === "resigned" || employee.status === "exited" ||
      employee.status === "terminated" || employee.status === "absconded" ||
      employee.status === "separated" || employee.status === "inactive") {
    cls = "bg-error/15 text-error";
  } else if (employee.status === "on_leave") {
    cls = "bg-info/15 text-info";
  } else if (employee.is_on_probation) {
    cls = "bg-warning/10 text-warning";
  }
  return (
    <span
      className={`text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded ${cls}`}
    >
      {label}
    </span>
  );
}
