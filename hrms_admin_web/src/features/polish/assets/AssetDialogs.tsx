// Assign / return dialogs, shared by the register, the employee Assets
// tab and the exit-clearance panel.
import { useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { X } from "lucide-react";

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
import { polishApi, type Asset } from "@/lib/api/polish";
import { cn } from "@/lib/utils";
import {
  CONDITIONS,
  SELECT_CLASS,
  errDetail,
  invalidateAssets,
  makeModel,
  useAssetCategories,
  useEmployeesById,
} from "./shared";

const LEFT_STATUSES = ["terminated", "exited", "separated", "inactive", "absconded"];

export function Modal({
  title,
  description,
  onClose,
  children,
  wide = false,
}: {
  title: ReactNode;
  description?: ReactNode;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
    >
      <Card className={cn("max-h-[92vh] w-full overflow-y-auto", wide ? "max-w-3xl" : "max-w-lg")}>
        <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
          <div className="min-w-0">
            <CardTitle className="text-lg">{title}</CardTitle>
            {description && <CardDescription className="mt-1">{description}</CardDescription>}
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close">
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent>{children}</CardContent>
      </Card>
    </div>
  );
}

/** The whole register — used to find an asset's accessories. */
export function useAllAssets() {
  return useQuery({
    queryKey: ["polish-assets", "all"],
    queryFn: () => polishApi.listAssets(),
    staleTime: 30_000,
  });
}

function AccessoryList({ items, label }: { items: Asset[]; label: string }) {
  if (!items.length) return null;
  return (
    <div className="rounded-lg bg-brand-brown-50/50 px-3 py-2 text-xs text-brand-brown-darker">
      <div className="mb-1 font-medium">{label}</div>
      <ul className="space-y-0.5">
        {items.map((a) => (
          <li key={a.id}>
            <span className="font-mono">{a.asset_tag}</span> · {a.name}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Hand an asset to an employee. Pass `asset` (pick the employee) or
 * `employeeId` (pick from usable stock).
 */
export function AssignAssetModal({
  asset: fixedAsset,
  employeeId: fixedEmployeeId,
  onClose,
}: {
  asset?: Asset;
  employeeId?: number;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const { employees, name: employeeName } = useEmployeesById();
  const { name: categoryName } = useAssetCategories();
  const { data: all = [] } = useAllAssets();
  const [assetId, setAssetId] = useState<number | "">(fixedAsset?.id ?? "");
  const [employeeId, setEmployeeId] = useState<number | "">(fixedEmployeeId ?? "");
  const [notes, setNotes] = useState("");
  const [withAccessories, setWithAccessories] = useState(true);

  const asset = fixedAsset ?? all.find((a) => a.id === assetId);
  const available = useMemo(
    () =>
      all.filter(
        (a) => a.status === "in_stock" && a.is_usable && a.parent_asset_id == null,
      ),
    [all],
  );
  const accessories = asset
    ? all.filter(
        (a) => a.parent_asset_id === asset.id && a.status === "in_stock" && a.is_usable,
      )
    : [];
  const today = new Date().toISOString().slice(0, 10);
  const activeEmployees = employees.filter(
    (e) => !LEFT_STATUSES.includes(e.status) && !(e.exit_date && e.exit_date < today),
  );

  const assign = useMutation({
    mutationFn: () =>
      polishApi.assignAsset(asset!.id, Number(employeeId), {
        notes,
        includeAccessories: withAccessories,
      }),
    onSuccess: () => {
      toast.success(`${asset!.asset_tag} assigned to ${employeeName(Number(employeeId))}`);
      invalidateAssets(qc);
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not assign")),
  });

  return (
    <Modal
      title={fixedAsset ? `Assign ${fixedAsset.asset_tag}` : "Assign an asset"}
      description={
        fixedAsset
          ? [fixedAsset.name, makeModel(fixedAsset)].filter(Boolean).join(" · ")
          : `To ${employeeName(fixedEmployeeId)} — only working, in-stock assets are listed.`
      }
      onClose={onClose}
    >
      <div className="space-y-4">
        {!fixedAsset && (
          <div className="space-y-1.5">
            <Label>Asset</Label>
            <select
              className={SELECT_CLASS}
              value={assetId}
              onChange={(e) => setAssetId(e.target.value ? Number(e.target.value) : "")}
            >
              <option value="">— Select an available asset —</option>
              {available.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.asset_tag} · {a.name} ({categoryName(a.category)})
                </option>
              ))}
            </select>
            {available.length === 0 && (
              <p className="text-xs text-brand-brown-light">No working assets in stock.</p>
            )}
          </div>
        )}
        {!fixedEmployeeId && (
          <div className="space-y-1.5">
            <Label>Employee</Label>
            <select
              className={SELECT_CLASS}
              value={employeeId}
              onChange={(e) => setEmployeeId(e.target.value ? Number(e.target.value) : "")}
            >
              <option value="">— Select —</option>
              {activeEmployees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.employee_code} — {e.first_name} {e.last_name}
                </option>
              ))}
            </select>
          </div>
        )}
        {accessories.length > 0 && (
          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              className="mt-1"
              checked={withAccessories}
              onChange={(e) => setWithAccessories(e.target.checked)}
            />
            <span>
              Hand over its accessories too
              <AccessoryList items={accessories} label="" />
            </span>
          </label>
        )}
        <div className="space-y-1.5">
          <Label>Notes</Label>
          <Input
            value={notes}
            placeholder="e.g. Joining kit, handed over by IT"
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
        <div className="flex justify-end gap-2 border-t border-brand-brown-50 pt-4">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button disabled={!asset || !employeeId || assign.isPending} onClick={() => assign.mutate()}>
            {assign.isPending ? "Assigning…" : "Assign"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

/** Take an asset back, recording the condition it came back in. */
export function ReturnAssetModal({
  asset,
  onClose,
}: {
  asset: { id: number; asset_tag: string; name: string; assigned_to?: number | null };
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const { name: employeeName } = useEmployeesById();
  const { data: all = [] } = useAllAssets();
  const [condition, setCondition] = useState("working");
  const [notes, setNotes] = useState("");
  const [withAccessories, setWithAccessories] = useState(true);
  const holder = asset.assigned_to ?? all.find((a) => a.id === asset.id)?.assigned_to;
  const accessories = all.filter(
    (a) => a.parent_asset_id === asset.id && a.status === "assigned" && a.assigned_to === holder,
  );

  const returnIt = useMutation({
    mutationFn: () =>
      polishApi.returnAsset(asset.id, condition, {
        notes,
        includeAccessories: withAccessories,
      }),
    onSuccess: () => {
      toast.success(`${asset.asset_tag} returned`);
      invalidateAssets(qc);
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not return")),
  });

  const options = [
    ...CONDITIONS,
    { value: "lost", label: "Lost", hint: "Not handed back" },
  ];

  return (
    <Modal
      title={`Return ${asset.asset_tag}`}
      description={`${asset.name}${holder ? ` · from ${employeeName(holder)}` : ""}`}
      onClose={onClose}
    >
      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label>Condition on return</Label>
          <div className="grid gap-2 sm:grid-cols-2">
            {options.map((o) => (
              <label
                key={o.value}
                className={cn(
                  "flex cursor-pointer items-start gap-2 rounded-lg border px-3 py-2 text-sm",
                  condition === o.value
                    ? "border-brand-gold-dark bg-brand-gold/10"
                    : "border-brand-brown-100",
                )}
              >
                <input
                  type="radio"
                  className="mt-1"
                  name="return-condition"
                  checked={condition === o.value}
                  onChange={() => setCondition(o.value)}
                />
                <span>
                  <span className="block font-medium">{o.label}</span>
                  <span className="block text-xs text-brand-brown-light">{o.hint}</span>
                </span>
              </label>
            ))}
          </div>
          {condition !== "working" && condition !== "lost" && (
            <p className="text-xs text-warning">
              It goes back on the register as not usable and can't be handed out until
              its condition is set to Working.
            </p>
          )}
        </div>
        {accessories.length > 0 && (
          <label className="flex items-start gap-2 text-sm">
            <input
              type="checkbox"
              className="mt-1"
              checked={withAccessories}
              onChange={(e) => setWithAccessories(e.target.checked)}
            />
            <span>
              Its accessories came back too (in working order)
              <AccessoryList items={accessories} label="" />
            </span>
          </label>
        )}
        <div className="space-y-1.5">
          <Label>Notes</Label>
          <Input
            value={notes}
            placeholder="e.g. Screen scratched, charger missing"
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
        <div className="flex justify-end gap-2 border-t border-brand-brown-50 pt-4">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button disabled={returnIt.isPending} onClick={() => returnIt.mutate()}>
            {returnIt.isPending ? "Saving…" : "Confirm return"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
