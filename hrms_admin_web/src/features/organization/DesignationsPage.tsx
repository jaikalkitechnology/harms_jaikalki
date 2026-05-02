import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Briefcase, Plus, Save, Trash2 } from "lucide-react";

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
  organizationApi,
  type Department,
  type Designation,
} from "@/lib/api/organization";

export default function DesignationsPage() {
  const qc = useQueryClient();
  const { data: list = [], isLoading } = useQuery({
    queryKey: ["designations"],
    queryFn: organizationApi.listDesignations,
  });
  const { data: depts = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: organizationApi.listDepartments,
  });

  const [draft, setDraft] = useState({
    code: "",
    name: "",
    level: 3,
    department_id: "",
  });

  const create = useMutation({
    mutationFn: () =>
      organizationApi.createDesignation({
        code: draft.code,
        name: draft.name,
        level: draft.level,
        department_id: draft.department_id ? Number(draft.department_id) : null,
      }),
    onSuccess: () => {
      toast.success("Designation added");
      setDraft({ code: "", name: "", level: 3, department_id: "" });
      qc.invalidateQueries({ queryKey: ["designations"] });
    },
    onError: () => toast.error("Could not add designation"),
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Briefcase className="h-5 w-5" /> Designations
          </CardTitle>
          <CardDescription>
            Job titles. Higher level = more seniority.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid sm:grid-cols-2 md:grid-cols-5 gap-3">
          <div>
            <Label>Code</Label>
            <Input
              value={draft.code}
              onChange={(e) =>
                setDraft({ ...draft, code: e.target.value.toUpperCase() })
              }
              placeholder="SE"
            />
          </div>
          <div className="md:col-span-2">
            <Label>Name</Label>
            <Input
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              placeholder="Software Engineer"
            />
          </div>
          <div>
            <Label>Level</Label>
            <Input
              type="number"
              min={1}
              max={10}
              value={draft.level}
              onChange={(e) =>
                setDraft({ ...draft, level: Number(e.target.value) })
              }
            />
          </div>
          <div>
            <Label>Department</Label>
            <select
              className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
              value={draft.department_id}
              onChange={(e) =>
                setDraft({ ...draft, department_id: e.target.value })
              }
            >
              <option value="">— None —</option>
              {(depts as Department[]).map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
          <div className="sm:col-span-2 md:col-span-5">
            <Button
              disabled={!draft.code || !draft.name}
              onClick={() => create.mutate()}
            >
              <Plus className="h-4 w-4 mr-1" /> Add
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm min-w-[700px]">
            <thead className="text-left text-brand-brown-light">
              <tr>
                <th className="py-2 px-4">Code</th>
                <th>Name</th>
                <th>Level</th>
                <th>Department</th>
                <th className="text-right pr-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(list as Designation[]).map((d) => (
                <DesignationRow key={d.id} desig={d} depts={depts} />
              ))}
              {list.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-6 text-brand-brown-light">
                    No designations yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

function DesignationRow({
  desig,
  depts,
}: {
  desig: Designation;
  depts: Department[];
}) {
  const qc = useQueryClient();
  const [name, setName] = useState(desig.name);
  const [level, setLevel] = useState(desig.level);
  const [departmentId, setDepartmentId] = useState<string>(
    desig.department_id ? String(desig.department_id) : "",
  );

  const save = useMutation({
    mutationFn: () =>
      organizationApi.updateDesignation(desig.id, {
        name,
        level,
        department_id: departmentId ? Number(departmentId) : null,
      }),
    onSuccess: () => {
      toast.success("Saved");
      qc.invalidateQueries({ queryKey: ["designations"] });
    },
  });
  const remove = useMutation({
    mutationFn: () => organizationApi.deleteDesignation(desig.id),
    onSuccess: () => {
      toast.success("Removed");
      qc.invalidateQueries({ queryKey: ["designations"] });
    },
    onError: () => toast.error("Could not delete (in use?)"),
  });

  const deptName = useMemo(
    () => depts.find((d) => d.id === desig.department_id)?.name ?? "—",
    [depts, desig.department_id],
  );

  return (
    <tr className="border-t border-brand-brown-50">
      <td className="py-2 px-4 font-mono">{desig.code}</td>
      <td>
        <Input value={name} onChange={(e) => setName(e.target.value)} />
      </td>
      <td>
        <Input
          type="number"
          min={1}
          max={10}
          value={level}
          onChange={(e) => setLevel(Number(e.target.value))}
        />
      </td>
      <td>
        <select
          className="w-full h-10 px-2 rounded border border-brand-brown-50 bg-card text-sm"
          value={departmentId}
          onChange={(e) => setDepartmentId(e.target.value)}
        >
          <option value="">— None —</option>
          {depts.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        {!departmentId && (
          <span className="block text-xs text-brand-brown-light mt-0.5">
            Currently: {deptName}
          </span>
        )}
      </td>
      <td className="text-right pr-4">
        <Button size="sm" variant="outline" onClick={() => save.mutate()}>
          <Save className="h-3 w-3" />
        </Button>{" "}
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            if (confirm(`Delete ${desig.name}?`)) remove.mutate();
          }}
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </td>
    </tr>
  );
}
