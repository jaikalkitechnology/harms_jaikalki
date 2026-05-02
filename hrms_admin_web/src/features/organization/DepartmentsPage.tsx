import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Building, Plus, Save, Trash2 } from "lucide-react";

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
import { organizationApi, type Department } from "@/lib/api/organization";

export default function DepartmentsPage() {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["departments"],
    queryFn: organizationApi.listDepartments,
  });
  const [draft, setDraft] = useState({
    code: "",
    name: "",
    description: "",
  });

  const create = useMutation({
    mutationFn: organizationApi.createDepartment,
    onSuccess: () => {
      toast.success("Department added");
      setDraft({ code: "", name: "", description: "" });
      qc.invalidateQueries({ queryKey: ["departments"] });
    },
    onError: () => toast.error("Could not add department"),
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" /> Departments
          </CardTitle>
          <CardDescription>
            Group employees by org unit. Codes are short and uppercase.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid sm:grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <Label>Code</Label>
            <Input
              value={draft.code}
              onChange={(e) =>
                setDraft({ ...draft, code: e.target.value.toUpperCase() })
              }
              placeholder="ENG"
            />
          </div>
          <div>
            <Label>Name</Label>
            <Input
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              placeholder="Engineering"
            />
          </div>
          <div className="sm:col-span-2">
            <Label>Description</Label>
            <Input
              value={draft.description}
              onChange={(e) =>
                setDraft({ ...draft, description: e.target.value })
              }
            />
          </div>
          <div className="sm:col-span-2 md:col-span-4">
            <Button
              disabled={!draft.code || !draft.name}
              onClick={() =>
                create.mutate({
                  code: draft.code,
                  name: draft.name,
                  description: draft.description || undefined,
                })
              }
            >
              <Plus className="h-4 w-4 mr-1" /> Add
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead className="text-left text-brand-brown-light">
              <tr>
                <th className="py-2 px-4">Code</th>
                <th>Name</th>
                <th>Description</th>
                <th className="text-right pr-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(data as Department[]).map((d) => (
                <DepartmentRow key={d.id} dept={d} />
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan={4} className="text-center py-6 text-brand-brown-light">
                    No departments yet
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

function DepartmentRow({ dept }: { dept: Department }) {
  const qc = useQueryClient();
  const [name, setName] = useState(dept.name);
  const [description, setDescription] = useState(dept.description ?? "");

  const save = useMutation({
    mutationFn: () =>
      organizationApi.updateDepartment(dept.id, { name, description }),
    onSuccess: () => {
      toast.success("Saved");
      qc.invalidateQueries({ queryKey: ["departments"] });
    },
  });
  const remove = useMutation({
    mutationFn: () => organizationApi.deleteDepartment(dept.id),
    onSuccess: () => {
      toast.success("Removed");
      qc.invalidateQueries({ queryKey: ["departments"] });
    },
    onError: () => toast.error("Could not delete (in use?)"),
  });

  return (
    <tr className="border-t border-brand-brown-50">
      <td className="py-2 px-4 font-mono">{dept.code}</td>
      <td>
        <Input value={name} onChange={(e) => setName(e.target.value)} />
      </td>
      <td>
        <Input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </td>
      <td className="text-right pr-4">
        <Button size="sm" variant="outline" onClick={() => save.mutate()}>
          <Save className="h-3 w-3" />
        </Button>{" "}
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            if (confirm(`Delete ${dept.name}?`)) remove.mutate();
          }}
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </td>
    </tr>
  );
}
