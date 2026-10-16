// Create / edit an asset. The category decides which configuration
// fields appear (e.g. processor / RAM / storage for a laptop).
import { useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { polishApi, type Asset } from "@/lib/api/polish";
import { Modal, useAllAssets } from "./AssetDialogs";
import {
  CONDITIONS,
  SELECT_CLASS,
  STATUS_LABEL,
  errDetail,
  invalidateAssets,
  useAssetCategories,
} from "./shared";

interface Draft {
  asset_tag: string;
  name: string;
  category: string;
  brand: string;
  model: string;
  serial_number: string;
  condition: string;
  status: string;
  parent_asset_id: string;
  purchase_date: string;
  purchase_cost: string;
  warranty_until: string;
  notes: string;
  specs: Record<string, string>;
}

function draftFrom(a: Asset | null): Draft {
  return {
    asset_tag: a?.asset_tag ?? "",
    name: a?.name ?? "",
    category: a?.category ?? "laptop",
    brand: a?.brand ?? "",
    model: a?.model ?? "",
    serial_number: a?.serial_number ?? "",
    condition: a?.condition ?? "working",
    status: a?.status ?? "in_stock",
    parent_asset_id: a?.parent_asset_id ? String(a.parent_asset_id) : "",
    purchase_date: a?.purchase_date ?? "",
    purchase_cost: a?.purchase_cost ?? "",
    warranty_until: a?.warranty_until ?? "",
    notes: a?.notes ?? "",
    specs: { ...(a?.specs ?? {}) },
  };
}

function Field({ label, children, wide = false }: { label: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <div className={wide ? "space-y-1.5 sm:col-span-2" : "space-y-1.5"}>
      <Label>{label}</Label>
      {children}
    </div>
  );
}

export function AssetFormModal({
  asset,
  onClose,
}: {
  /** null = new asset */
  asset: Asset | null;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const { categories, byCode } = useAssetCategories();
  const { data: all = [] } = useAllAssets();
  const [d, setD] = useState<Draft>(() => draftFrom(asset));
  const category = byCode.get(d.category);
  const specFields = category?.spec_fields ?? [];
  // Main assets an accessory can belong to.
  const parents = useMemo(
    () => all.filter((a) => a.parent_asset_id == null && a.id !== asset?.id),
    [all, asset?.id],
  );

  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setD((p) => ({ ...p, [k]: v }));

  const save = useMutation({
    mutationFn: () => {
      const specs = Object.fromEntries(
        specFields
          .map((f) => [f.key, (d.specs[f.key] ?? "").trim()] as const)
          .filter(([, v]) => v),
      );
      const body: Record<string, unknown> = {
        name: d.name.trim(),
        category: d.category,
        brand: d.brand.trim() || null,
        model: d.model.trim() || null,
        serial_number: d.serial_number.trim() || null,
        condition: d.condition,
        parent_asset_id: d.parent_asset_id ? Number(d.parent_asset_id) : null,
        purchase_date: d.purchase_date || null,
        purchase_cost: d.purchase_cost ? Number(d.purchase_cost) : null,
        warranty_until: d.warranty_until || null,
        notes: d.notes.trim() || null,
        specs: Object.keys(specs).length ? specs : null,
      };
      if (!asset) return polishApi.createAsset({ ...body, asset_tag: d.asset_tag.trim() });
      if (asset.status !== "assigned" && d.status !== asset.status) body.status = d.status;
      return polishApi.updateAsset(asset.id, body);
    },
    onSuccess: () => {
      toast.success(asset ? "Asset updated" : "Asset added");
      invalidateAssets(qc);
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });

  const selectedCategoryMissing = d.category && !byCode.has(d.category);

  return (
    <Modal
      wide
      title={asset ? `Edit ${asset.asset_tag}` : "New asset"}
      description={
        asset
          ? undefined
          : "Starts in stock. Only assets in Working condition can be handed out."
      }
      onClose={onClose}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        {!asset && (
          <Field label="Asset tag *">
            <Input
              value={d.asset_tag}
              placeholder="JK-LT-001"
              onChange={(e) => set("asset_tag", e.target.value)}
            />
          </Field>
        )}
        <Field label="Name *">
          <Input
            value={d.name}
            placeholder="ThinkPad E14"
            onChange={(e) => set("name", e.target.value)}
          />
        </Field>
        <Field label="Category">
          <select
            className={SELECT_CLASS}
            value={d.category}
            onChange={(e) => set("category", e.target.value)}
          >
            {selectedCategoryMissing && <option value={d.category}>{d.category}</option>}
            {categories.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name}
                {c.is_accessory ? " (accessory)" : ""}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Accessory of">
          <select
            className={SELECT_CLASS}
            value={d.parent_asset_id}
            onChange={(e) => set("parent_asset_id", e.target.value)}
          >
            <option value="">— Standalone asset —</option>
            {parents.map((a) => (
              <option key={a.id} value={a.id}>
                {a.asset_tag} · {a.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Brand">
          <Input value={d.brand} placeholder="Lenovo" onChange={(e) => set("brand", e.target.value)} />
        </Field>
        <Field label="Model">
          <Input value={d.model} placeholder="E14 Gen 5" onChange={(e) => set("model", e.target.value)} />
        </Field>
        <Field label="Serial number">
          <Input value={d.serial_number} onChange={(e) => set("serial_number", e.target.value)} />
        </Field>
        <Field label="Condition">
          <select
            className={SELECT_CLASS}
            value={d.condition}
            onChange={(e) => set("condition", e.target.value)}
          >
            {CONDITIONS.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label} — {c.hint}
              </option>
            ))}
          </select>
        </Field>

        {specFields.length > 0 && (
          <div className="sm:col-span-2">
            <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-brand-gold-dark">
              {category?.name} configuration
            </div>
            <div className="grid gap-3 rounded-lg border border-brand-brown-50 p-3 sm:grid-cols-2">
              {specFields.map((f) => (
                <Field key={f.key} label={f.label}>
                  <Input
                    value={d.specs[f.key] ?? ""}
                    onChange={(e) =>
                      setD((p) => ({ ...p, specs: { ...p.specs, [f.key]: e.target.value } }))
                    }
                  />
                </Field>
              ))}
            </div>
          </div>
        )}

        <Field label="Purchase date">
          <Input type="date" value={d.purchase_date} onChange={(e) => set("purchase_date", e.target.value)} />
        </Field>
        <Field label="Warranty until">
          <Input type="date" value={d.warranty_until} onChange={(e) => set("warranty_until", e.target.value)} />
        </Field>
        <Field label="Purchase cost (₹)">
          <Input
            type="number"
            min={0}
            value={d.purchase_cost}
            onChange={(e) => set("purchase_cost", e.target.value)}
          />
        </Field>
        {asset && (
          <Field label="Status">
            <select
              className={SELECT_CLASS}
              value={d.status}
              disabled={asset.status === "assigned"}
              onChange={(e) => set("status", e.target.value)}
            >
              {asset.status === "assigned" ? (
                <option value="assigned">Assigned — use Return to change</option>
              ) : (
                (["in_stock", "in_repair", "retired", "lost"] as const).map((s) => (
                  <option key={s} value={s}>
                    {STATUS_LABEL[s]}
                  </option>
                ))
              )}
            </select>
          </Field>
        )}
        <Field label="Notes" wide>
          <Input value={d.notes} onChange={(e) => set("notes", e.target.value)} />
        </Field>

        <div className="flex justify-end gap-2 border-t border-brand-brown-50 pt-4 sm:col-span-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            disabled={(!asset && !d.asset_tag.trim()) || !d.name.trim() || save.isPending}
            onClick={() => save.mutate()}
          >
            {save.isPending ? "Saving…" : asset ? "Save changes" : "Add asset"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
