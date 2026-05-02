import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Trash2, KeyRound } from "lucide-react";

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
  superAdminApi,
  type AdminUser,
  type AuditLogRow,
} from "@/lib/api/super-admin";

export default function AdminUsersPage() {
  const qc = useQueryClient();
  const { data: admins = [], isLoading } = useQuery({
    queryKey: ["admins"],
    queryFn: superAdminApi.listAdmins,
  });
  const { data: roles = [] } = useQuery({
    queryKey: ["roles"],
    queryFn: superAdminApi.listRoles,
  });

  const [activeId, setActiveId] = useState<number | null>(null);
  const active = admins.find((a) => a.id === activeId) ?? null;

  const [draft, setDraft] = useState({
    email: "",
    full_name: "",
    password: "",
    role_codes: [] as string[],
  });
  const create = useMutation({
    mutationFn: superAdminApi.createAdmin,
    onSuccess: () => {
      toast.success("Admin created");
      setDraft({ email: "", full_name: "", password: "", role_codes: [] });
      qc.invalidateQueries({ queryKey: ["admins"] });
    },
    onError: () => toast.error("Could not create admin"),
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="grid md:grid-cols-3 gap-6">
      <div className="md:col-span-1 space-y-3">
        <Card>
          <CardHeader>
            <CardTitle>New admin</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                value={draft.email}
                onChange={(e) => setDraft({ ...draft, email: e.target.value })}
              />
            </div>
            <div>
              <Label>Full name</Label>
              <Input
                value={draft.full_name}
                onChange={(e) =>
                  setDraft({ ...draft, full_name: e.target.value })
                }
              />
            </div>
            <div>
              <Label>Initial password</Label>
              <Input
                type="password"
                value={draft.password}
                onChange={(e) =>
                  setDraft({ ...draft, password: e.target.value })
                }
              />
            </div>
            <div>
              <Label>Roles</Label>
              <div className="space-y-1 max-h-40 overflow-y-auto border border-brand-brown-50 rounded p-2">
                {roles.map((r) => (
                  <label
                    key={r.id}
                    className="flex items-center gap-2 text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={draft.role_codes.includes(r.code)}
                      onChange={(e) =>
                        setDraft({
                          ...draft,
                          role_codes: e.target.checked
                            ? [...draft.role_codes, r.code]
                            : draft.role_codes.filter((c) => c !== r.code),
                        })
                      }
                    />
                    {r.name}
                  </label>
                ))}
              </div>
            </div>
            <Button
              disabled={
                !draft.email ||
                !draft.full_name ||
                draft.password.length < 8 ||
                draft.role_codes.length === 0
              }
              onClick={() => create.mutate(draft)}
            >
              <Plus className="h-4 w-4 mr-1" /> Create
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Admins</CardTitle>
            <CardDescription>{admins.length} accounts</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {admins.map((a) => (
              <button
                key={a.id}
                onClick={() => setActiveId(a.id)}
                className={`w-full text-left px-4 py-2 border-b border-brand-brown-50 hover:bg-brand-brown-50 ${
                  activeId === a.id ? "bg-brand-brown-50" : ""
                }`}
              >
                <div className="font-medium text-sm">{a.full_name}</div>
                <div className="text-xs text-brand-brown-light">
                  {a.email} · {a.role_codes.join(", ") || "no roles"}
                  {!a.is_active && " · inactive"}
                </div>
              </button>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="md:col-span-2">
        {active ? (
          <AdminEditor key={active.id} admin={active} allRoles={roles} />
        ) : (
          <Card>
            <CardContent className="py-12 text-center text-brand-brown-light">
              Select an admin to edit
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function AdminEditor({
  admin,
  allRoles,
}: {
  admin: AdminUser;
  allRoles: { id: number; code: string; name: string }[];
}) {
  const qc = useQueryClient();
  const [picks, setPicks] = useState<Set<string>>(new Set(admin.role_codes));
  const [resetPwd, setResetPwd] = useState("");

  const setRoles = useMutation({
    mutationFn: () => superAdminApi.setAdminRoles(admin.id, Array.from(picks)),
    onSuccess: () => {
      toast.success("Roles updated");
      qc.invalidateQueries({ queryKey: ["admins"] });
    },
  });

  const update = useMutation({
    mutationFn: (body: Parameters<typeof superAdminApi.updateAdmin>[1]) =>
      superAdminApi.updateAdmin(admin.id, body),
    onSuccess: () => {
      toast.success("Updated");
      setResetPwd("");
      qc.invalidateQueries({ queryKey: ["admins"] });
    },
  });

  const remove = useMutation({
    mutationFn: () => superAdminApi.deleteAdmin(admin.id),
    onSuccess: () => {
      toast.success("Deactivated");
      qc.invalidateQueries({ queryKey: ["admins"] });
    },
  });

  const { data: audit = [] } = useQuery({
    queryKey: ["admin-audit", admin.id],
    queryFn: () => superAdminApi.adminAudit(admin.id),
  });

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>{admin.full_name}</CardTitle>
            <CardDescription>{admin.email}</CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (confirm("Deactivate this admin?")) remove.mutate();
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Roles</Label>
            <div className="grid grid-cols-2 gap-1 mt-1">
              {allRoles.map((r) => (
                <label key={r.id} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={picks.has(r.code)}
                    onChange={(e) => {
                      const next = new Set(picks);
                      e.target.checked ? next.add(r.code) : next.delete(r.code);
                      setPicks(next);
                    }}
                  />
                  {r.name}
                </label>
              ))}
            </div>
            <Button
              size="sm"
              className="mt-2"
              onClick={() => setRoles.mutate()}
            >
              Save roles
            </Button>
          </div>
          <div className="border-t border-brand-brown-50 pt-4">
            <Label>Reset password</Label>
            <div className="flex gap-2 mt-1">
              <Input
                type="password"
                value={resetPwd}
                onChange={(e) => setResetPwd(e.target.value)}
                placeholder="New password (≥ 8 chars)"
              />
              <Button
                disabled={resetPwd.length < 8}
                onClick={() => update.mutate({ password: resetPwd })}
              >
                <KeyRound className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent activity</CardTitle>
        </CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <tbody>
              {audit.map((row: AuditLogRow) => (
                <tr key={row.id} className="border-t border-brand-brown-50">
                  <td className="py-2 text-xs text-brand-brown-light">
                    {new Date(row.occurred_at).toLocaleString()}
                  </td>
                  <td className="py-2 font-mono">{row.action}</td>
                  <td className="py-2 text-brand-brown-light">
                    {row.entity_type} {row.entity_id}
                  </td>
                </tr>
              ))}
              {audit.length === 0 && (
                <tr>
                  <td className="py-4 text-center text-brand-brown-light">
                    No recorded activity
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
