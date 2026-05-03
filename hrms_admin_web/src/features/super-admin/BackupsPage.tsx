import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { DatabaseBackup, Play } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import {
  superAdminApi,
  type DatabaseBackup as Backup,
} from "@/lib/api/super-admin";
import { fmtIst } from "@/lib/datetime";

const STATUS_COLOR: Record<string, string> = {
  completed: "bg-success/15 text-success",
  failed: "bg-error/15 text-error",
  running: "bg-info/15 text-info",
  pending: "bg-warning/15 text-warning",
};

function fmtBytes(n: number): string {
  if (!n) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} MB`;
  return `${(n / 1024 ** 3).toFixed(1)} GB`;
}

export default function BackupsPage() {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["backups"],
    queryFn: superAdminApi.listBackups,
  });
  const trigger = useMutation({
    mutationFn: superAdminApi.triggerBackup,
    onSuccess: () => {
      toast.success("Backup triggered");
      qc.invalidateQueries({ queryKey: ["backups"] });
    },
    onError: () => toast.error("Backup failed to start"),
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <DatabaseBackup className="h-5 w-5" /> Database backups
          </CardTitle>
          <CardDescription>
            Trigger a mysqldump on demand. The actual dump is delegated to
            scripts/ops/backup.sh on the host.
          </CardDescription>
        </div>
        <Button onClick={() => trigger.mutate()}>
          <Play className="h-4 w-4 mr-1" /> Trigger backup
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <table className="w-full text-sm">
          <thead className="text-left text-brand-brown-light">
            <tr>
              <th className="py-2 px-4">When</th>
              <th>File</th>
              <th>Size</th>
              <th>Status</th>
              <th>Error</th>
            </tr>
          </thead>
          <tbody>
            {(data as Backup[]).map((b) => (
              <tr key={b.id} className="border-t border-brand-brown-50">
                <td className="py-2 px-4 text-xs">
                  {fmtIst(b.started_at)}
                </td>
                <td className="font-mono text-xs">{b.file_name}</td>
                <td>{fmtBytes(b.size_bytes)}</td>
                <td>
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      STATUS_COLOR[b.status] ?? ""
                    }`}
                  >
                    {b.status}
                  </span>
                </td>
                <td className="text-xs text-error">{b.error ?? ""}</td>
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td
                  colSpan={5}
                  className="text-center py-6 text-brand-brown-light"
                >
                  No backups yet
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
