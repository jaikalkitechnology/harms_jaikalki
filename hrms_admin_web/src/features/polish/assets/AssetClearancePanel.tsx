// Exit clearance: company assets the leaving employee still has to hand
// back (the asset NOC). Shown on resignation / separation cards.
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, PackageX } from "lucide-react";

import { Button } from "@/components/ui/button";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { launchApi, type AssetClearanceItem } from "@/lib/api/launch";
import { ReturnAssetModal } from "./AssetDialogs";
import { conditionLabel, fmtDay } from "./shared";

export function AssetClearancePanel({ resignationId }: { resignationId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: ["resignation-assets", resignationId],
    queryFn: () => launchApi.resignationAssets(resignationId),
  });
  const [returning, setReturning] = useState<AssetClearanceItem | null>(null);
  const [showReturned, setShowReturned] = useState(false);

  if (isLoading || !data) {
    return <div className="text-xs text-brand-brown-light">Checking company assets…</div>;
  }

  return (
    <div className="rounded-md border border-brand-brown-50 p-3">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-semibold uppercase text-brand-gold-dark">
          Asset NOC
        </div>
        {data.cleared ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-success">
            <CheckCircle2 className="size-3.5" /> All company assets returned
          </span>
        ) : (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-warning">
            <PackageX className="size-3.5" /> {data.pending_count} to return
            {data.last_working_day && ` by ${fmtDay(data.last_working_day)}`}
          </span>
        )}
      </div>

      {data.pending.length > 0 && (
        <ul className="space-y-1.5">
          {data.pending.map((a) => (
            <li
              key={a.id}
              className="flex items-center justify-between gap-2 rounded-lg bg-warning/5 px-3 py-2 text-sm"
            >
              <span className="min-w-0 truncate">
                {a.name} <span className="font-mono text-xs text-brand-brown-light">{a.asset_tag}</span>
                <span className="text-xs text-brand-brown-light"> · {a.category_name}</span>
              </span>
              <PermissionGate permission="admin.users.manage">
                <Button size="sm" variant="outline" onClick={() => setReturning(a)}>
                  Mark returned
                </Button>
              </PermissionGate>
            </li>
          ))}
        </ul>
      )}

      {data.returned.length > 0 && (
        <div className="mt-2">
          <button
            type="button"
            className="text-xs text-brand-brown-light hover:text-brand-brown-darker"
            onClick={() => setShowReturned((s) => !s)}
          >
            {showReturned ? "Hide" : "Show"} {data.returned_count} returned during exit
          </button>
          {showReturned && (
            <ul className="mt-1 space-y-1 text-xs text-brand-brown-light">
              {data.returned.map((a) => (
                <li key={`${a.id}-${a.returned_at}`}>
                  {a.name} ({a.asset_tag}) · {fmtDay(a.returned_at)} ·{" "}
                  {conditionLabel(a.return_condition)}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {returning && <ReturnAssetModal asset={returning} onClose={() => setReturning(null)} />}
    </div>
  );
}
