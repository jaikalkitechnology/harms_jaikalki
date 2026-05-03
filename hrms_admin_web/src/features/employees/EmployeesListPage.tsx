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
import { CategoryBadge } from "./CategoryBadge";
import { fmtIstDate } from "@/lib/datetime";

export default function EmployeesListPage() {
  const navigate = useNavigate();
  const [departmentId, setDepartmentId] = useState<number | undefined>();
  const [categoryId, setCategoryId] = useState<number | undefined>();
  const [onProbation, setOnProbation] = useState<boolean | undefined>();

  const { data: employees = [], isLoading } = useQuery({
    queryKey: ["employees", { departmentId, categoryId, onProbation }],
    queryFn: () =>
      employeesApi.list({
        department_id: departmentId,
        category_id: categoryId,
        on_probation: onProbation,
      }),
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
        accessorKey: "employee_code",
        header: "Code",
        cell: ({ row }) => (
          <span className="font-mono text-xs">
            {row.original.employee_code}
          </span>
        ),
      },
      {
        id: "name",
        header: "Name",
        accessorFn: (e) => `${e.first_name} ${e.last_name}`,
        cell: ({ row }) => (
          <div>
            <div className="font-medium">
              {row.original.first_name} {row.original.last_name}
            </div>
            {row.original.designation && (
              <div className="text-xs text-brand-brown-light">
                {row.original.designation.name}
              </div>
            )}
          </div>
        ),
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
        id: "probation",
        header: "Status",
        accessorFn: (e) => (e.is_on_probation ? "Probation" : "Confirmed"),
        cell: ({ row }) =>
          row.original.is_on_probation ? (
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded bg-warning/10 text-warning">
              On Probation
            </span>
          ) : (
            <span className="text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded bg-success/10 text-success">
              Confirmed
            </span>
          ),
      },
      {
        accessorKey: "date_of_joining",
        header: "Joined",
        cell: ({ row }) =>
          row.original.date_of_joining
            ? fmtIstDate(row.original.date_of_joining)
            : "—",
      },
    ],
    [],
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
            {employees.length} employees · scope respects your role.
          </p>
        </div>
        <PermissionGate permission="employee.create">
          <Button onClick={() => navigate("/employees/new")}>
            <Plus className="h-4 w-4" />
            Add employee
          </Button>
        </PermissionGate>
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
        <span className="mx-2 w-px bg-brand-brown-100" />
        <FilterPill
          label="On probation"
          active={onProbation === true}
          onClick={() =>
            setOnProbation(onProbation === true ? undefined : true)
          }
        />
      </div>

      <DataTable
        columns={columns}
        data={employees}
        loading={isLoading}
        searchPlaceholder="Search by name, code, email…"
        onRowClick={(e) => navigate(`/employees/${e.id}`)}
        emptyMessage="No employees match these filters."
      />
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
