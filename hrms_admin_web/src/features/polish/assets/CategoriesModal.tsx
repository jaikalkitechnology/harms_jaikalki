// Manage asset categories and the configuration fields each one asks for.
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil, Plus, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { polishApi, type AssetCategory } from "@/lib/api/polish";
import { Modal } from "./AssetDialogs";
import { categoryIcon, errDetail, useAssetCategories } from "./shared";

interface Draft {
  name: string;
  is_accessory: boolean;
  spec_labels: string[];
}

const blank: Draft = { name: "", is_accessory: false, spec_labels: [] };

export function CategoriesModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const { categories } = useAssetCategories(true);
  const [editing, setEditing] = useState<AssetCategory | "new" | null>(null);
  const [d, setD] = useState<Draft>(blank);

  const refresh = () => qc.invalidateQueries({ queryKey: ["asset-categories"] });

  const open = (c: AssetCategory | "new") => {
    setEditing(c);
    setD(
      c === "new"
        ? blank
        : {
            name: c.name,
            is_accessory: c.is_accessory,
            spec_labels: (c.spec_fields ?? []).map((f) => f.label),
          },
    );
  };

  const save = useMutation({
    mutationFn: () => {
      const existing = editing !== "new" && editing ? editing.spec_fields ?? [] : [];
      // Keep the stored key for labels that already existed so saved
      // configuration values stay attached.
      const spec_fields = d.spec_labels
        .map((l) => l.trim())
        .filter(Boolean)
        .map((label) => ({ label, key: existing.find((f) => f.label === label)?.key }));
      const body = { name: d.name.trim(), is_accessory: d.is_accessory, spec_fields };
      return editing === "new"
        ? polishApi.createAssetCategory(body)
        : polishApi.updateAssetCategory((editing as AssetCategory).id, body);
    },
    onSuccess: () => {
      toast.success("Category saved");
      refresh();
      setEditing(null);
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });

  const toggle = useMutation({
    mutationFn: (c: AssetCategory) =>
      polishApi.updateAssetCategory(c.id, { is_active: !c.is_active }),
    onSuccess: refresh,
    onError: (e) => toast.error(errDetail(e, "Could not update")),
  });

  return (
    <Modal
      wide
      title="Asset categories"
      description="What kinds of asset you track, and the configuration recorded for each."
      onClose={onClose}
    >
      {editing ? (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Name *</Label>
              <Input
                value={d.name}
                placeholder="e.g. Tablet, Docking station"
                onChange={(e) => setD({ ...d, name: e.target.value })}
              />
            </div>
            <label className="flex items-center gap-2 self-end pb-2 text-sm">
              <input
                type="checkbox"
                checked={d.is_accessory}
                onChange={(e) => setD({ ...d, is_accessory: e.target.checked })}
              />
              Accessory (usually belongs to another asset, e.g. a charger)
            </label>
          </div>
          <div className="space-y-2">
            <Label>Configuration fields</Label>
            {d.spec_labels.map((label, i) => (
              <div key={i} className="flex gap-2">
                <Input
                  value={label}
                  placeholder="e.g. RAM"
                  onChange={(e) =>
                    setD({
                      ...d,
                      spec_labels: d.spec_labels.map((l, j) => (j === i ? e.target.value : l)),
                    })
                  }
                />
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label="Remove field"
                  onClick={() =>
                    setD({ ...d, spec_labels: d.spec_labels.filter((_, j) => j !== i) })
                  }
                >
                  <Trash2 className="size-4 text-error" />
                </Button>
              </div>
            ))}
            <Button
              variant="outline"
              size="sm"
              className="gap-1"
              onClick={() => setD({ ...d, spec_labels: [...d.spec_labels, ""] })}
            >
              <Plus className="size-3.5" /> Add field
            </Button>
          </div>
          <div className="flex justify-end gap-2 border-t border-brand-brown-50 pt-4">
            <Button variant="outline" onClick={() => setEditing(null)}>
              Back
            </Button>
            <Button disabled={!d.name.trim() || save.isPending} onClick={() => save.mutate()}>
              {save.isPending ? "Saving…" : "Save category"}
            </Button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="divide-y divide-brand-brown-50 rounded-lg border border-brand-brown-50">
            {categories.map((c) => {
              const Icon = categoryIcon(c.code);
              return (
                <div key={c.id} className="flex items-center gap-3 px-3 py-2.5">
                  <Icon className="size-4 shrink-0 text-brand-gold-dark" />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium">
                      {c.name}
                      {c.is_accessory && (
                        <span className="ml-2 text-xs text-brand-brown-light">accessory</span>
                      )}
                      {!c.is_active && (
                        <span className="ml-2 text-xs text-error">disabled</span>
                      )}
                    </div>
                    <div className="truncate text-xs text-brand-brown-light">
                      {(c.spec_fields ?? []).map((f) => f.label).join(" · ") ||
                        "No configuration fields"}
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => toggle.mutate(c)}>
                    {c.is_active ? "Disable" : "Enable"}
                  </Button>
                  <Button variant="ghost" size="icon" aria-label={`Edit ${c.name}`} onClick={() => open(c)}>
                    <Pencil className="size-4" />
                  </Button>
                </div>
              );
            })}
          </div>
          <Button className="gap-1" onClick={() => open("new")}>
            <Plus className="size-4" /> New category
          </Button>
        </div>
      )}
    </Modal>
  );
}
