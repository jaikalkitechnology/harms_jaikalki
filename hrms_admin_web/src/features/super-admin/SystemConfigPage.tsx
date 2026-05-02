import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Save } from "lucide-react";

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
import { superAdminApi, type SystemConfig } from "@/lib/api/super-admin";

export default function SystemConfigPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["system-config"],
    queryFn: superAdminApi.listConfig,
  });
  const { data: health } = useQuery({
    queryKey: ["system-health"],
    queryFn: superAdminApi.systemHealth,
  });

  const grouped = useMemo(() => {
    const out: Record<string, SystemConfig[]> = {};
    (data ?? []).forEach((row) => {
      out[row.category] = out[row.category] ?? [];
      out[row.category].push(row);
    });
    return out;
  }, [data]);

  const upsert = useMutation({
    mutationFn: superAdminApi.upsertConfig,
    onSuccess: () => {
      toast.success("Saved");
      qc.invalidateQueries({ queryKey: ["system-config"] });
    },
    onError: () => toast.error("Save failed"),
  });

  const [draft, setDraft] = useState({
    key: "",
    value: "",
    category: "general",
    description: "",
    is_secret: false,
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>System</CardTitle>
          <CardDescription>
            Runtime config + health snapshot. Secret values are write-only.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="text-xs bg-brand-brown-50 p-3 rounded font-mono overflow-x-auto">
            {JSON.stringify(health ?? {}, null, 2)}
          </pre>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add / update key</CardTitle>
        </CardHeader>
        <CardContent className="grid md:grid-cols-2 gap-3">
          <div>
            <Label>Key</Label>
            <Input
              value={draft.key}
              onChange={(e) => setDraft({ ...draft, key: e.target.value })}
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
            <Label>Value (JSON or text)</Label>
            <Input
              value={draft.value}
              onChange={(e) => setDraft({ ...draft, value: e.target.value })}
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
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={draft.is_secret}
              onChange={(e) =>
                setDraft({ ...draft, is_secret: e.target.checked })
              }
            />{" "}
            Secret (UI-mask the value)
          </label>
          <div className="md:col-span-2">
            <Button
              disabled={!draft.key}
              onClick={() => {
                let value: unknown = draft.value;
                try {
                  value = JSON.parse(draft.value);
                } catch {
                  // keep as string
                }
                upsert.mutate({
                  key: draft.key,
                  value,
                  category: draft.category || "general",
                  description: draft.description || undefined,
                  is_secret: draft.is_secret,
                });
              }}
            >
              <Plus className="h-4 w-4 mr-1" /> Upsert
            </Button>
          </div>
        </CardContent>
      </Card>

      {Object.entries(grouped).map(([cat, rows]) => (
        <Card key={cat}>
          <CardHeader>
            <CardTitle className="capitalize">{cat}</CardTitle>
          </CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead className="text-left text-brand-brown-light">
                <tr>
                  <th className="py-2">Key</th>
                  <th>Value</th>
                  <th>Description</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <ConfigRow key={r.id} row={r} />
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function ConfigRow({ row }: { row: SystemConfig }) {
  const qc = useQueryClient();
  const [val, setVal] = useState(JSON.stringify(row.value ?? ""));
  const save = useMutation({
    mutationFn: () =>
      superAdminApi.upsertConfig({
        key: row.key,
        value: (() => {
          try {
            return JSON.parse(val);
          } catch {
            return val;
          }
        })(),
        category: row.category,
        description: row.description ?? undefined,
        is_secret: row.is_secret,
      }),
    onSuccess: () => {
      toast.success("Saved");
      qc.invalidateQueries({ queryKey: ["system-config"] });
    },
  });
  return (
    <tr className="border-t border-brand-brown-50">
      <td className="py-2 font-mono">{row.key}</td>
      <td className="py-2">
        {row.is_secret ? (
          <span className="text-brand-brown-light">••••••</span>
        ) : (
          <Input value={val} onChange={(e) => setVal(e.target.value)} />
        )}
      </td>
      <td className="py-2 text-brand-brown-light">{row.description ?? "—"}</td>
      <td className="py-2 text-right">
        {!row.is_secret && (
          <Button size="sm" variant="outline" onClick={() => save.mutate()}>
            <Save className="h-3 w-3 mr-1" /> Save
          </Button>
        )}
      </td>
    </tr>
  );
}
