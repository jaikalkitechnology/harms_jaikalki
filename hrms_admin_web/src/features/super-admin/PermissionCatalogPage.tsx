import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";

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
import { superAdminApi, type Permission } from "@/lib/api/super-admin";

export default function PermissionCatalogPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["permissions"],
    queryFn: superAdminApi.listPermissions,
  });
  const [search, setSearch] = useState("");

  const grouped = useMemo(() => {
    const out: Record<string, Permission[]> = {};
    (data ?? [])
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
  }, [data, search]);

  const [draft, setDraft] = useState({
    code: "",
    description: "",
    category: "",
  });

  const create = useMutation({
    mutationFn: superAdminApi.createPermission,
    onSuccess: () => {
      toast.success("Permission added");
      setDraft({ code: "", description: "", category: "" });
      qc.invalidateQueries({ queryKey: ["permissions"] });
    },
    onError: () => toast.error("Could not add permission"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => superAdminApi.deletePermission(id),
    onSuccess: () => {
      toast.success("Removed");
      qc.invalidateQueries({ queryKey: ["permissions"] });
    },
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Permission catalog</CardTitle>
          <CardDescription>
            Codes follow `entity.action.scope`. Roles reference these codes.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-4 gap-3">
          <div>
            <Label>Code</Label>
            <Input
              value={draft.code}
              onChange={(e) => setDraft({ ...draft, code: e.target.value })}
              placeholder="e.g. report.view.team"
            />
          </div>
          <div>
            <Label>Category</Label>
            <Input
              value={draft.category}
              onChange={(e) => setDraft({ ...draft, category: e.target.value })}
            />
          </div>
          <div className="md:col-span-2">
            <Label>Description</Label>
            <Input
              value={draft.description}
              onChange={(e) =>
                setDraft({ ...draft, description: e.target.value })
              }
            />
          </div>
          <div className="md:col-span-4">
            <Button
              disabled={!draft.code || !draft.category}
              onClick={() =>
                create.mutate({
                  code: draft.code,
                  category: draft.category,
                  description: draft.description || undefined,
                })
              }
            >
              <Plus className="h-4 w-4 mr-1" /> Add
            </Button>
          </div>
        </CardContent>
      </Card>

      <Input
        placeholder="Search permissions…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {Object.entries(grouped).map(([cat, rows]) => (
        <Card key={cat}>
          <CardHeader>
            <CardTitle className="capitalize">
              {cat}{" "}
              <span className="text-brand-brown-light text-sm">
                ({rows.length})
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <tbody>
                {rows.map((p) => (
                  <tr key={p.id} className="border-t border-brand-brown-50">
                    <td className="py-2 font-mono">{p.code}</td>
                    <td className="py-2 text-brand-brown-light">
                      {p.description ?? "—"}
                    </td>
                    <td className="py-2 text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          if (confirm(`Delete ${p.code}?`)) remove.mutate(p.id);
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
