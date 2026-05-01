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
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { launchApi } from "@/lib/api/launch";

const METHOD_COLOR: Record<string, string> = {
  POST: "bg-info/15 text-info",
  PUT: "bg-warning/15 text-warning",
  PATCH: "bg-warning/15 text-warning",
  DELETE: "bg-error/15 text-error",
};

export default function AuditLogPage() {
  const [days, setDays] = useState(7);
  const [actionFilter, setActionFilter] = useState("");

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ["audit-log", days, actionFilter],
    queryFn: () =>
      launchApi.audit({
        since_days: days,
        action: actionFilter || undefined,
        limit: 500,
      }),
  });

  if (isLoading) return <LoadingScreen label="Loading audit trail…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Audit Trail
        </h1>
        <p className="text-sm text-brand-brown-light">
          Append-only record of who did what, when. Captured automatically
          for every authenticated mutation.
        </p>
      </div>

      <Card>
        <CardContent className="grid gap-4 md:grid-cols-3 pt-6">
          <div>
            <Label>Last (days)</Label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {[1, 7, 30, 90, 180, 365].map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
          <div className="md:col-span-2">
            <Label>Action filter</Label>
            <Input
              placeholder='e.g. http.post'
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            {logs.length} record{logs.length === 1 ? "" : "s"}
          </CardTitle>
          <CardDescription>Newest first</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">When</th>
                <th className="px-4 py-3">Actor</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Path</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No entries.
                  </td>
                </tr>
              ) : (
                logs.map((l) => (
                  <tr key={l.id} className="border-t border-brand-brown-50">
                    <td className="px-4 py-3 text-xs">
                      {new Date(l.occurred_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {l.actor_label ?? l.actor_user_id ?? "system"}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {l.action}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {l.method && (
                        <span
                          className={`mr-1 rounded px-1.5 py-0.5 text-[10px] ${METHOD_COLOR[l.method] ?? ""}`}
                        >
                          {l.method}
                        </span>
                      )}
                      {l.path ?? "—"}
                    </td>
                    <td
                      className={`px-4 py-3 text-xs ${
                        l.status_code && l.status_code >= 500
                          ? "text-error"
                          : l.status_code && l.status_code >= 400
                            ? "text-warning"
                            : ""
                      }`}
                    >
                      {l.status_code ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-xs text-brand-brown-light">
                      {l.ip ?? "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
