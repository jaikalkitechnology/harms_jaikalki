// Side panel: everything about one asset — configuration, accessories,
// warranty, and who has had it.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Link } from "react-router-dom";
import {
  Archive,
  ArchiveRestore,
  ArrowDownLeft,
  ArrowUpRight,
  Pencil,
  Trash2,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { polishApi, type Asset } from "@/lib/api/polish";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { useAllAssets } from "./AssetDialogs";
import {
  ConditionChip,
  StatusChip,
  categoryIcon,
  conditionLabel,
  errDetail,
  invalidateAssets,
  fmtDay,
  makeModel,
  useAssetCategories,
  useEmployeesById,
} from "./shared";

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 py-1.5 text-sm">
      <dt className="text-brand-brown-light">{label}</dt>
      <dd className="text-right font-medium text-brand-brown-darker">{value || "—"}</dd>
    </div>
  );
}

export function AssetDetailPanel({
  asset,
  onClose,
  onEdit,
  onAssign,
  onReturn,
  onRetire,
  onOpen,
}: {
  asset: Asset;
  onClose: () => void;
  onEdit: () => void;
  onAssign: () => void;
  onReturn: () => void;
  onRetire: () => void;
  onOpen: (a: Asset) => void;
}) {
  const qc = useQueryClient();
  const restore = useMutation({
    mutationFn: () => polishApi.restoreAsset(asset.id),
    onSuccess: () => {
      toast.success(`${asset.asset_tag} is back in stock`);
      invalidateAssets(qc);
    },
    onError: (e) => toast.error(errDetail(e, "Could not restore")),
  });
  const remove = useMutation({
    mutationFn: () => polishApi.deleteAsset(asset.id),
    onSuccess: () => {
      toast.success(`${asset.asset_tag} deleted`);
      invalidateAssets(qc);
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not delete")),
  });
  const { byCode, name: categoryName } = useAssetCategories(true);
  const { name: employeeName } = useEmployeesById();
  const { data: all = [] } = useAllAssets();
  const { data: history = [] } = useQuery({
    queryKey: ["asset-history", asset.id],
    queryFn: () => polishApi.assetHistory(asset.id),
  });
  const Icon = categoryIcon(asset.category);
  const accessories = all.filter((a) => a.parent_asset_id === asset.id);
  const parent = asset.parent_asset_id ? all.find((a) => a.id === asset.parent_asset_id) : null;
  const specFields = byCode.get(asset.category)?.spec_fields ?? [];
  const specs = asset.specs ?? {};
  // Configuration values, in the category's field order, then any extras.
  const specRows = [
    ...specFields.filter((f) => specs[f.key]).map((f) => [f.label, specs[f.key]] as const),
    ...Object.entries(specs).filter(([k]) => !specFields.some((f) => f.key === k)),
  ];
  const warrantyOver =
    asset.warranty_until && asset.warranty_until < new Date().toISOString().slice(0, 10);

  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-black/30" onClick={onClose}>
      <aside
        className="h-full w-full max-w-md overflow-y-auto bg-card shadow-xl"
        onClick={(e) => e.stopPropagation()}
        aria-label={`${asset.asset_tag} details`}
      >
        <div className="sticky top-0 z-10 flex items-start gap-3 border-b border-brand-brown-50 bg-card px-5 py-4">
          <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-gold/15 text-brand-gold-dark">
            <Icon className="size-5" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-mono text-xs text-brand-brown-light">{asset.asset_tag}</div>
            <div className="truncate text-lg font-semibold">{asset.name}</div>
            <div className="text-xs text-brand-brown-light">
              {[categoryName(asset.category), makeModel(asset)].filter(Boolean).join(" · ")}
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            <X className="size-4" />
          </Button>
        </div>

        <div className="space-y-5 px-5 py-4">
          <div className="flex flex-wrap items-center gap-2">
            <StatusChip status={asset.status} />
            <ConditionChip condition={asset.condition} />
            {!asset.is_usable && (
              <span className="text-xs text-warning">Not usable — can't be assigned</span>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" className="gap-1" onClick={onEdit}>
              <Pencil className="size-3.5" /> Edit
            </Button>
            {asset.status === "in_stock" && asset.is_usable && (
              <Button size="sm" onClick={onAssign}>
                Assign
              </Button>
            )}
            {asset.status === "assigned" && (
              <Button size="sm" onClick={onReturn}>
                Take back
              </Button>
            )}
            <PermissionGate permission="admin.users.manage">
              {(asset.status === "in_stock" || asset.status === "in_repair") && (
                <Button variant="outline" size="sm" className="gap-1" onClick={onRetire}>
                  <Archive className="size-3.5" /> Retire
                </Button>
              )}
              {(asset.status === "retired" || asset.status === "lost") && (
                <Button
                  variant="outline"
                  size="sm"
                  className="gap-1"
                  disabled={restore.isPending}
                  onClick={() => restore.mutate()}
                >
                  <ArchiveRestore className="size-3.5" /> Restore to stock
                </Button>
              )}
              {/* Delete only what was never handed out — e.g. a wrong entry. */}
              {asset.status !== "assigned" && history.length === 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="gap-1 text-error"
                  disabled={remove.isPending}
                  onClick={() => {
                    if (
                      window.confirm(
                        `Delete ${asset.asset_tag} permanently? Use this only for an asset added by mistake.`,
                      )
                    )
                      remove.mutate();
                  }}
                >
                  <Trash2 className="size-3.5" /> Delete
                </Button>
              )}
            </PermissionGate>
          </div>
          {asset.status === "retired" && (
            <p className="text-xs text-brand-brown-light">
              No longer available — kept on the register for its history.
            </p>
          )}

          {asset.status === "assigned" && asset.assigned_to && (
            <div className="rounded-xl bg-brand-gold/10 px-4 py-3 text-sm">
              With{" "}
              <Link
                to={`/employees/${asset.assigned_to}?tab=assets`}
                className="font-semibold text-brand-gold-dark hover:underline"
              >
                {employeeName(asset.assigned_to)}
              </Link>{" "}
              since {fmtDay(asset.assigned_at)}
            </div>
          )}

          {specRows.length > 0 && (
            <section>
              <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-brand-gold-dark">
                Configuration
              </h3>
              <dl className="divide-y divide-brand-brown-50">
                {specRows.map(([k, v]) => (
                  <Row key={k} label={k} value={v} />
                ))}
              </dl>
            </section>
          )}

          <section>
            <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-brand-gold-dark">
              Details
            </h3>
            <dl className="divide-y divide-brand-brown-50">
              <Row label="Serial number" value={asset.serial_number} />
              <Row label="Purchased" value={asset.purchase_date && fmtDay(asset.purchase_date)} />
              <Row
                label="Cost"
                value={
                  asset.purchase_cost &&
                  `₹${Number(asset.purchase_cost).toLocaleString("en-IN")}`
                }
              />
              <Row
                label="Warranty until"
                value={
                  asset.warranty_until && (
                    <span className={warrantyOver ? "text-error" : undefined}>
                      {fmtDay(asset.warranty_until)}
                      {warrantyOver ? " · expired" : ""}
                    </span>
                  )
                }
              />
              {parent && (
                <Row
                  label="Accessory of"
                  value={
                    <button
                      className="text-brand-gold-dark hover:underline"
                      onClick={() => onOpen(parent)}
                    >
                      {parent.asset_tag} · {parent.name}
                    </button>
                  }
                />
              )}
            </dl>
            {asset.notes && (
              <p className="mt-2 rounded-lg bg-brand-brown-50/50 px-3 py-2 text-sm">{asset.notes}</p>
            )}
          </section>

          {accessories.length > 0 && (
            <section>
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-gold-dark">
                Accessories ({accessories.length})
              </h3>
              <ul className="space-y-1.5">
                {accessories.map((a) => (
                  <li key={a.id}>
                    <button
                      className="flex w-full items-center justify-between gap-2 rounded-lg border border-brand-brown-50 px-3 py-2 text-left text-sm hover:bg-brand-brown-50/50"
                      onClick={() => onOpen(a)}
                    >
                      <span className="min-w-0 truncate">
                        <span className="font-mono text-xs">{a.asset_tag}</span> · {a.name}
                      </span>
                      <ConditionChip condition={a.condition} />
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-gold-dark">
              History
            </h3>
            {history.length === 0 ? (
              <p className="text-sm text-brand-brown-light">Never assigned.</p>
            ) : (
              <ol className="space-y-3">
                {history.map((h) => (
                  <li key={h.id} className="rounded-lg border border-brand-brown-50 px-3 py-2 text-sm">
                    <div className="flex items-center gap-2">
                      <ArrowUpRight className="size-3.5 text-brand-gold-dark" />
                      <span>
                        To{" "}
                        <Link
                          to={`/employees/${h.employee_id}?tab=assets`}
                          className="font-medium hover:underline"
                        >
                          {employeeName(h.employee_id)}
                        </Link>{" "}
                        · {fmtDay(h.assigned_at)}
                      </span>
                    </div>
                    {h.returned_at ? (
                      <div className="mt-1 flex items-center gap-2 text-brand-brown-light">
                        <ArrowDownLeft className="size-3.5" />
                        Returned {fmtDay(h.returned_at)} · {conditionLabel(h.return_condition)}
                      </div>
                    ) : (
                      <div className="mt-1 text-xs text-brand-gold-dark">Currently with them</div>
                    )}
                    {h.notes && (
                      <div className="mt-1 whitespace-pre-line text-xs text-brand-brown-light">
                        {h.notes}
                      </div>
                    )}
                  </li>
                ))}
              </ol>
            )}
          </section>
        </div>
      </aside>
    </div>
  );
}
