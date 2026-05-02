import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Copy, Plus, Trash2 } from "lucide-react";

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
import { superAdminApi, type ApiKey } from "@/lib/api/super-admin";

export default function ApiKeysPage() {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["api-keys"],
    queryFn: superAdminApi.listApiKeys,
  });

  const [draft, setDraft] = useState({
    name: "",
    scopes: "",
    rate: "",
  });
  const [revealed, setRevealed] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () =>
      superAdminApi.createApiKey({
        name: draft.name,
        scopes: draft.scopes
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        rate_limit_per_minute: draft.rate ? Number(draft.rate) : null,
      }),
    onSuccess: (resp) => {
      setRevealed(resp.plain_key);
      setDraft({ name: "", scopes: "", rate: "" });
      qc.invalidateQueries({ queryKey: ["api-keys"] });
    },
    onError: () => toast.error("Could not create key"),
  });

  const revoke = useMutation({
    mutationFn: (id: number) => superAdminApi.revokeApiKey(id),
    onSuccess: () => {
      toast.success("Revoked");
      qc.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>New API key</CardTitle>
          <CardDescription>
            Plain text shown ONCE — copy and store securely.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-3 gap-3">
          <div>
            <Label>Name</Label>
            <Input
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
          </div>
          <div>
            <Label>Scopes (comma-separated)</Label>
            <Input
              value={draft.scopes}
              onChange={(e) => setDraft({ ...draft, scopes: e.target.value })}
              placeholder="employee.read, attendance.read"
            />
          </div>
          <div>
            <Label>Rate limit / min</Label>
            <Input
              value={draft.rate}
              onChange={(e) => setDraft({ ...draft, rate: e.target.value })}
              placeholder="60"
            />
          </div>
          <div className="md:col-span-3">
            <Button disabled={!draft.name} onClick={() => create.mutate()}>
              <Plus className="h-4 w-4 mr-1" /> Generate
            </Button>
          </div>
          {revealed && (
            <div className="md:col-span-3 border border-brand-gold-dark rounded p-3 bg-brand-gold/10">
              <div className="text-sm font-medium mb-2">
                Plain key (shown once):
              </div>
              <div className="flex items-center gap-2">
                <code className="font-mono text-sm break-all flex-1">
                  {revealed}
                </code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    navigator.clipboard.writeText(revealed);
                    toast.success("Copied");
                  }}
                >
                  <Copy className="h-3 w-3" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setRevealed(null)}
                >
                  Dismiss
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="text-left text-brand-brown-light">
              <tr>
                <th className="py-2 px-4">Name</th>
                <th>Prefix</th>
                <th>Scopes</th>
                <th>Rate</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {(data as ApiKey[]).map((k) => (
                <tr key={k.id} className="border-t border-brand-brown-50">
                  <td className="py-2 px-4">{k.name}</td>
                  <td className="font-mono text-xs">{k.key_prefix}…</td>
                  <td className="text-xs">{k.scopes?.join(", ") ?? "—"}</td>
                  <td>{k.rate_limit_per_minute ?? "—"}</td>
                  <td>
                    {k.is_active ? (
                      <span className="text-success">active</span>
                    ) : (
                      <span className="text-brand-brown-light">revoked</span>
                    )}
                  </td>
                  <td className="text-right pr-4">
                    {k.is_active && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          if (confirm(`Revoke "${k.name}"?`))
                            revoke.mutate(k.id);
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="text-center py-6 text-brand-brown-light"
                  >
                    No keys yet
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
