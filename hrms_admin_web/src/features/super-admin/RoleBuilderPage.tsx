import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Save, Trash2 } from "lucide-react";

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
import { superAdminApi, type Permission, type Role } from "@/lib/api/super-admin";

export default function RoleBuilderPage() {
  const { data: roles = [], isLoading: rolesLoading } = useQuery({
    queryKey: ["roles"],
    queryFn: superAdminApi.listRoles,
  });
  const { data: perms = [], isLoading: permsLoading } = useQuery({
    queryKey: ["permissions"],
    queryFn: superAdminApi.listPermissions,
  });

  const [activeId, setActiveId] = useState<number | null>(null);
  const active = roles.find((r) => r.id === activeId) ?? null;

  if (rolesLoading || permsLoading) return <LoadingScreen />;

  return (
    <div className="grid md:grid-cols-3 gap-6">
      <div className="md:col-span-1 space-y-3">
        <CreateRoleCard />
        <Card>
          <CardHeader>
            <CardTitle>Roles</CardTitle>
            <CardDescription>Click to edit permissions</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {roles.map((r) => (
              <button
                key={r.id}
                onClick={() => setActiveId(r.id)}
                className={`w-full text-left px-4 py-2 border-b border-brand-brown-50 hover:bg-brand-brown-50 ${
                  activeId === r.id ? "bg-brand-brown-50" : ""
                }`}
              >
                <div className="font-medium">{r.name}</div>
                <div className="text-xs text-brand-brown-light font-mono">
                  {r.code} · level {r.level} · {r.permission_codes.length}{" "}
                  perms
                </div>
              </button>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="md:col-span-2">
        {active ? (
          <RoleEditor key={active.id} role={active} perms={perms} />
        ) : (
          <Card>
            <CardContent className="py-12 text-center text-brand-brown-light">
              Select a role to edit its permissions
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function CreateRoleCard() {
  const qc = useQueryClient();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [level, setLevel] = useState(2);
  const [picks, setPicks] = useState<Set<string>>(new Set());

  const create = useMutation({
    mutationFn: superAdminApi.createRole,
    onSuccess: () => {
      toast.success("Role created");
      setCode("");
      setName("");
      setPicks(new Set());
      qc.invalidateQueries({ queryKey: ["roles"] });
    },
    onError: () => toast.error("Could not create role"),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>New role</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <Label>Code</Label>
          <Input value={code} onChange={(e) => setCode(e.target.value)} />
        </div>
        <div>
          <Label>Name</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <Label>Level</Label>
          <Input
            type="number"
            value={level}
            onChange={(e) => setLevel(Number(e.target.value))}
          />
        </div>
        <Button
          disabled={!code || !name}
          onClick={() =>
            create.mutate({
              code,
              name,
              level,
              permission_codes: Array.from(picks),
            })
          }
        >
          <Plus className="h-4 w-4 mr-1" /> Create
        </Button>
      </CardContent>
    </Card>
  );
}

function RoleEditor({ role, perms }: { role: Role; perms: Permission[] }) {
  const qc = useQueryClient();
  const [picks, setPicks] = useState<Set<string>>(new Set(role.permission_codes));
  const [search, setSearch] = useState("");

  useEffect(() => {
    setPicks(new Set(role.permission_codes));
  }, [role.id, role.permission_codes]);

  const grouped = useMemo(() => {
    const out: Record<string, Permission[]> = {};
    perms
      .filter(
        (p) =>
          !search ||
          p.code.includes(search) ||
          (p.description ?? "").toLowerCase().includes(search.toLowerCase()),
      )
      .forEach((p) => {
        out[p.category] = out[p.category] ?? [];
        out[p.category].push(p);
      });
    return out;
  }, [perms, search]);

  const save = useMutation({
    mutationFn: () => superAdminApi.setRolePermissions(role.id, Array.from(picks)),
    onSuccess: () => {
      toast.success("Permissions saved");
      qc.invalidateQueries({ queryKey: ["roles"] });
    },
    onError: () => toast.error("Save failed"),
  });

  const remove = useMutation({
    mutationFn: () => superAdminApi.deleteRole(role.id),
    onSuccess: () => {
      toast.success("Role deleted");
      qc.invalidateQueries({ queryKey: ["roles"] });
    },
    onError: () => toast.error("Delete failed"),
  });

  const toggle = (code: string) => {
    const next = new Set(picks);
    next.has(code) ? next.delete(code) : next.add(code);
    setPicks(next);
  };
  const toggleAll = (codes: string[]) => {
    const next = new Set(picks);
    const allOn = codes.every((c) => next.has(c));
    codes.forEach((c) => (allOn ? next.delete(c) : next.add(c)));
    setPicks(next);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>
            {role.name}{" "}
            <span className="text-sm text-brand-brown-light font-mono">
              ({role.code})
            </span>
          </CardTitle>
          <CardDescription>{picks.size} permissions selected</CardDescription>
        </div>
        <div className="flex gap-2">
          {role.code !== "super_admin" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (confirm(`Delete role "${role.name}"?`)) remove.mutate();
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
          <Button size="sm" onClick={() => save.mutate()}>
            <Save className="h-4 w-4 mr-1" /> Save
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Input
          placeholder="Filter permissions…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {Object.entries(grouped).map(([cat, rows]) => {
          const codes = rows.map((r) => r.code);
          const allOn = codes.every((c) => picks.has(c));
          return (
            <div key={cat} className="border border-brand-brown-50 rounded p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium capitalize">{cat}</div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => toggleAll(codes)}
                >
                  {allOn ? "Clear all" : "Select all"}
                </Button>
              </div>
              <div className="grid md:grid-cols-2 gap-2">
                {rows.map((p) => (
                  <label
                    key={p.id}
                    className="flex items-start gap-2 text-sm cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={picks.has(p.code)}
                      onChange={() => toggle(p.code)}
                    />
                    <span>
                      <span className="font-mono">{p.code}</span>
                      <span className="block text-xs text-brand-brown-light">
                        {p.description ?? ""}
                      </span>
                    </span>
                  </label>
                ))}
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
