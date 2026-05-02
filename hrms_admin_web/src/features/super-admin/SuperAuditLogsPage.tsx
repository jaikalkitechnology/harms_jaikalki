import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { superAdminApi, type AuditLogRow } from "@/lib/api/super-admin";

export default function SuperAuditLogsPage() {
  const [filters, setFilters] = useState({
    action: "",
    entity_type: "",
    actor_user_id: "",
    since_days: "30",
    limit: "200",
  });
  const params = {
    action: filters.action || undefined,
    entity_type: filters.entity_type || undefined,
    actor_user_id: filters.actor_user_id
      ? Number(filters.actor_user_id)
      : undefined,
    since_days: filters.since_days ? Number(filters.since_days) : undefined,
    limit: filters.limit ? Number(filters.limit) : undefined,
  };
  const { data = [], isLoading, refetch } = useQuery({
    queryKey: ["audit-logs", params],
    queryFn: () => superAdminApi.listAuditLogs(params),
  });

  const exportCsv = () => {
    const header = "occurred_at,actor,action,entity_type,entity_id,ip,path";
    const rows = (data as AuditLogRow[]).map((r) =>
      [
        r.occurred_at,
        JSON.stringify(r.actor_label ?? ""),
        r.action,
        r.entity_type ?? "",
        r.entity_id ?? "",
        r.ip ?? "",
        r.path ?? "",
      ].join(","),
    );
    const blob = new Blob([header + "\n" + rows.join("\n")], {
      type: "text/csv",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-${new Date().toISOString()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Audit logs</CardTitle>
          <CardDescription>
            Append-only log of admin and high-value actions.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid md:grid-cols-5 gap-3">
          <div>
            <Label>Action</Label>
            <Input
              value={filters.action}
              onChange={(e) =>
                setFilters({ ...filters, action: e.target.value })
              }
              placeholder="role.create"
            />
          </div>
          <div>
            <Label>Entity</Label>
            <Input
              value={filters.entity_type}
              onChange={(e) =>
                setFilters({ ...filters, entity_type: e.target.value })
              }
              placeholder="user"
            />
          </div>
          <div>
            <Label>Actor user id</Label>
            <Input
              value={filters.actor_user_id}
              onChange={(e) =>
                setFilters({ ...filters, actor_user_id: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Since (days)</Label>
            <Input
              value={filters.since_days}
              onChange={(e) =>
                setFilters({ ...filters, since_days: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Limit</Label>
            <Input
              value={filters.limit}
              onChange={(e) =>
                setFilters({ ...filters, limit: e.target.value })
              }
            />
          </div>
          <div className="md:col-span-5 flex gap-2">
            <Button onClick={() => refetch()}>Apply</Button>
            <Button variant="outline" onClick={exportCsv}>
              Export CSV
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <LoadingScreen />
          ) : (
            <table className="w-full text-sm">
              <thead className="text-left text-brand-brown-light">
                <tr>
                  <th className="py-2 px-4">When</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>IP</th>
                  <th>Path</th>
                </tr>
              </thead>
              <tbody>
                {(data as AuditLogRow[]).map((r) => (
                  <tr key={r.id} className="border-t border-brand-brown-50">
                    <td className="py-2 px-4 text-xs">
                      {new Date(r.occurred_at).toLocaleString()}
                    </td>
                    <td>{r.actor_label ?? "—"}</td>
                    <td className="font-mono">{r.action}</td>
                    <td className="text-brand-brown-light">
                      {r.entity_type ?? ""} {r.entity_id ?? ""}
                    </td>
                    <td className="text-xs">{r.ip ?? "—"}</td>
                    <td className="text-xs font-mono">{r.path ?? "—"}</td>
                  </tr>
                ))}
                {data.length === 0 && (
                  <tr>
                    <td
                      colSpan={6}
                      className="text-center py-6 text-brand-brown-light"
                    >
                      No matching entries
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
