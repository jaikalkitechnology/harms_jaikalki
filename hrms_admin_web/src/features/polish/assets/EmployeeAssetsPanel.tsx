// Employee profile → Assets tab: what they hold now, and their history.
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Plus } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { polishApi, type Asset } from "@/lib/api/polish";
import { AssignAssetModal, ReturnAssetModal } from "./AssetDialogs";
import {
  ConditionChip,
  categoryIcon,
  conditionLabel,
  fmtDay,
  makeModel,
  useAssetCategories,
} from "./shared";

function specSummary(a: Asset, labels: Map<string, string>): string {
  return Object.entries(a.specs ?? {})
    .slice(0, 4)
    .map(([k, v]) => `${labels.get(k) ?? k}: ${v}`)
    .join(" · ");
}

export function EmployeeAssetsPanel({
  employeeId,
  leavingOn,
}: {
  employeeId: number;
  /** Last working day when the employee is on the way out. */
  leavingOn?: string | null;
}) {
  const { byCode, name: categoryName } = useAssetCategories(true);
  const { data, isLoading } = useQuery({
    queryKey: ["employee-assets", employeeId],
    queryFn: () => polishApi.employeeAssets(employeeId),
  });
  const [assigning, setAssigning] = useState(false);
  const [returning, setReturning] = useState<Asset | null>(null);

  const current = data?.current ?? [];
  const history = data?.history ?? [];
  const labelsFor = (a: Asset) =>
    new Map((byCode.get(a.category)?.spec_fields ?? []).map((f) => [f.key, f.label]));

  return (
    <div className="space-y-4">
      {leavingOn && current.length > 0 && (
        <div className="flex items-start gap-3 rounded-2xl border border-warning/40 bg-warning/10 px-4 py-3 text-sm">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-warning" />
          <div>
            <div className="font-semibold">
              {current.length} asset{current.length === 1 ? "" : "s"} to collect before{" "}
              {fmtDay(leavingOn)}
            </div>
            <div className="text-brand-brown-light">
              Exit clearance (asset NOC) and the final settlement wait until everything is
              taken back.
            </div>
          </div>
        </div>
      )}

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <div>
            <CardTitle className="text-lg">Assets held now</CardTitle>
            <CardDescription>
              {isLoading
                ? "Loading…"
                : current.length
                  ? `${current.length} item${current.length === 1 ? "" : "s"}`
                  : "Nothing assigned"}
            </CardDescription>
          </div>
          {!leavingOn && (
            <PermissionGate permission="admin.users.manage">
              <Button size="sm" className="gap-1" onClick={() => setAssigning(true)}>
                <Plus className="size-4" /> Assign asset
              </Button>
            </PermissionGate>
          )}
        </CardHeader>
        <CardContent className="space-y-2">
          {current.map((a) => {
            const Icon = categoryIcon(a.category);
            const specs = specSummary(a, labelsFor(a));
            return (
              <div
                key={a.id}
                className="flex flex-wrap items-center gap-3 rounded-xl border border-brand-brown-50 px-4 py-3"
              >
                <div className="grid size-10 shrink-0 place-items-center rounded-lg bg-brand-gold/15 text-brand-gold-dark">
                  <Icon className="size-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-medium">
                    {a.name}{" "}
                    <span className="font-mono text-xs text-brand-brown-light">{a.asset_tag}</span>
                  </div>
                  <div className="text-xs text-brand-brown-light">
                    {[categoryName(a.category), makeModel(a), a.serial_number && `SN ${a.serial_number}`]
                      .filter(Boolean)
                      .join(" · ")}
                  </div>
                  {specs && <div className="text-xs text-brand-brown-light">{specs}</div>}
                  <div className="text-xs text-brand-brown-light">Since {fmtDay(a.assigned_at)}</div>
                </div>
                <ConditionChip condition={a.condition} />
                <PermissionGate permission="admin.users.manage">
                  <Button size="sm" variant="outline" onClick={() => setReturning(a)}>
                    Take back
                  </Button>
                </PermissionGate>
              </div>
            );
          })}
          {!isLoading && current.length === 0 && (
            <p className="rounded-lg border border-dashed border-brand-brown-100 px-4 py-6 text-center text-sm text-brand-brown-light">
              No company assets with this employee.
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">History</CardTitle>
          <CardDescription>Every asset this employee has been given.</CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full min-w-[620px] text-sm">
            <thead className="bg-brand-brown-50/40 text-left text-xs text-brand-brown-light">
              <tr>
                <th className="px-4 py-2">Asset</th>
                <th className="px-4 py-2">Given</th>
                <th className="px-4 py-2">Returned</th>
                <th className="px-4 py-2">Condition on return</th>
              </tr>
            </thead>
            <tbody>
              {history.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-brand-brown-light">
                    No history yet.
                  </td>
                </tr>
              ) : (
                history.map((h) => (
                  <tr key={h.id} className="border-t border-brand-brown-50">
                    <td className="px-4 py-2">
                      {h.asset.name}{" "}
                      <span className="font-mono text-xs text-brand-brown-light">{h.asset.asset_tag}</span>
                    </td>
                    <td className="px-4 py-2">{fmtDay(h.assigned_at)}</td>
                    <td className="px-4 py-2">
                      {h.returned_at ? fmtDay(h.returned_at) : <span className="text-brand-gold-dark">With them</span>}
                    </td>
                    <td className="px-4 py-2">
                      {h.return_condition ? conditionLabel(h.return_condition) : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {assigning && <AssignAssetModal employeeId={employeeId} onClose={() => setAssigning(false)} />}
      {returning && <ReturnAssetModal asset={returning} onClose={() => setReturning(null)} />}
    </div>
  );
}
