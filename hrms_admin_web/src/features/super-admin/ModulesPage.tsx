import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { superAdminApi, type ModuleSetting } from "@/lib/api/super-admin";

export default function ModulesPage() {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["modules"],
    queryFn: superAdminApi.listModules,
  });
  const update = useMutation({
    mutationFn: ({ id, is_enabled }: { id: number; is_enabled: boolean }) =>
      superAdminApi.updateModule(id, { is_enabled }),
    onSuccess: () => {
      toast.success("Saved");
      qc.invalidateQueries({ queryKey: ["modules"] });
    },
    onError: () => toast.error("Could not toggle module"),
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Modules</CardTitle>
        <CardDescription>
          Disable a module to hide it across web and mobile clients. Core
          modules cannot be disabled.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {data.map((m: ModuleSetting) => (
            <div
              key={m.id}
              className="flex items-start justify-between border border-brand-brown-50 rounded p-3"
            >
              <div>
                <div className="font-medium">
                  {m.name}{" "}
                  {m.is_core && (
                    <span className="text-xs text-brand-brown-light">
                      (core)
                    </span>
                  )}
                </div>
                <div className="text-xs text-brand-brown-light font-mono">
                  {m.module_code}
                </div>
                {m.description && (
                  <div className="text-sm text-brand-brown-light mt-1">
                    {m.description}
                  </div>
                )}
              </div>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={m.is_enabled}
                  disabled={m.is_core}
                  onChange={(e) =>
                    update.mutate({ id: m.id, is_enabled: e.target.checked })
                  }
                />
                {m.is_enabled ? "Enabled" : "Disabled"}
              </label>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
