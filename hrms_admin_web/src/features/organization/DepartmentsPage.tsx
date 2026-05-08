import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Building, Plus, Save, Smartphone, Trash2, X } from "lucide-react";

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
  const [modulesFor, setModulesFor] = useState<Department | null>(null);

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
          <table className="w-full text-sm min-w-[720px]">
            <thead className="text-left text-brand-brown-light">
              <tr>
                <th className="py-2 px-4">Code</th>
                <th>Name</th>
                <th>Description</th>
                <th>Mobile modules</th>
                <th className="text-right pr-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(data as Department[]).map((d) => (
                <DepartmentRow
                  key={d.id}
                  dept={d}
                  onEditModules={() => setModulesFor(d)}
                />
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan={5} className="text-center py-6 text-brand-brown-light">
                    No departments yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {modulesFor && (
        <ModulesModal
          dept={modulesFor}
          onClose={() => setModulesFor(null)}
        />
      )}
    </div>
  );
}

function DepartmentRow({
  dept,
  onEditModules,
}: {
  dept: Department;
  onEditModules: () => void;
}) {
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

  const moduleSummary =
    dept.enabled_modules == null
      ? "All modules visible"
      : dept.enabled_modules.length === 0
        ? "Locked down"
        : `${dept.enabled_modules.length} selected`;

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
      <td>
        <button
          type="button"
          onClick={onEditModules}
          className="inline-flex items-center gap-1 text-xs text-brand-gold-dark hover:underline"
        >
          <Smartphone className="h-3 w-3" />
          {moduleSummary}
        </button>
      </td>
      <td className="text-right pr-4 whitespace-nowrap">
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

function ModulesModal({
  dept,
  onClose,
}: {
  dept: Department;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["department-modules", dept.id],
    queryFn: () => organizationApi.getDepartmentModules(dept.id),
  });

  // null = "no whitelist (show all)" — represented by the master toggle
  // being on. When the user flips it off we initialize an empty selection.
  const [unrestricted, setUnrestricted] = useState<boolean>(true);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!data) return;
    if (data.enabled_modules == null) {
      setUnrestricted(true);
      setSelected(new Set(data.available_modules));
    } else {
      setUnrestricted(false);
      setSelected(new Set(data.enabled_modules));
    }
  }, [data]);

  const save = useMutation({
    mutationFn: () =>
      organizationApi.setDepartmentModules(
        dept.id,
        unrestricted ? null : Array.from(selected),
      ),
    onSuccess: () => {
      toast.success("Mobile modules saved");
      qc.invalidateQueries({ queryKey: ["departments"] });
      qc.invalidateQueries({ queryKey: ["department-modules", dept.id] });
      onClose();
    },
    onError: () => toast.error("Could not save"),
  });

  if (isLoading || !data) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
        <Card className="w-full max-w-2xl">
          <CardContent className="py-10 text-center text-sm text-brand-brown-light">
            Loading…
          </CardContent>
        </Card>
      </div>
    );
  }

  const toggle = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Smartphone className="h-4 w-4 text-brand-gold-dark" />
              Mobile modules · {dept.name}
            </CardTitle>
            <CardDescription>
              Pick the More-menu tiles members of this department can see in
              the mobile app. Notifications, 2FA and Settings are always
              visible.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <label className="flex items-center gap-2 rounded border border-brand-brown-50 p-3 cursor-pointer">
            <input
              type="checkbox"
              checked={unrestricted}
              onChange={(e) => setUnrestricted(e.target.checked)}
            />
            <div>
              <div className="text-sm font-medium">No restriction</div>
              <div className="text-xs text-brand-brown-light">
                Show every module to anyone in this department
                (recommended for HR / leadership departments).
              </div>
            </div>
          </label>

          <div
            className={
              unrestricted ? "opacity-50 pointer-events-none" : ""
            }
          >
            <div className="flex items-center justify-between mb-2">
              <div className="text-xs uppercase tracking-wider text-brand-gold-dark font-semibold">
                Modules ({selected.size}/{data.available_modules.length})
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setSelected(new Set(data.available_modules))
                  }
                  className="text-xs text-brand-gold-dark hover:underline"
                >
                  Select all
                </button>
                <button
                  type="button"
                  onClick={() => setSelected(new Set())}
                  className="text-xs text-brand-gold-dark hover:underline"
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
              {data.available_modules.map((m) => (
                <label
                  key={m}
                  className="flex items-center gap-2 rounded border border-brand-brown-50 px-2 py-1.5 text-xs cursor-pointer hover:bg-brand-brown-50/40"
                >
                  <input
                    type="checkbox"
                    checked={selected.has(m)}
                    onChange={() => toggle(m)}
                  />
                  <span className="capitalize">{m.replaceAll("_", " ")}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={() => save.mutate()} disabled={save.isPending}>
              {save.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
