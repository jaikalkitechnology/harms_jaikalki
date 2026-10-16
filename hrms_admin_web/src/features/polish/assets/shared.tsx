// Shared bits for the asset register, the employee Assets tab and the
// exit (NOC) panel: labels, chips, icons and data hooks.
import { useMemo } from "react";
import { useQuery, type QueryClient } from "@tanstack/react-query";
import {
  Battery,
  Bike,
  Headphones,
  Keyboard,
  Laptop,
  Monitor,
  Mouse,
  Package,
  Smartphone,
  type LucideIcon,
} from "lucide-react";

import { employeesApi, type EmployeeListItem } from "@/lib/api/employees";
import {
  polishApi,
  type Asset,
  type AssetCategory,
  type AssetCondition,
  type AssetStatus,
} from "@/lib/api/polish";
import { cn } from "@/lib/utils";

export const SELECT_CLASS =
  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

export const CONDITIONS: { value: AssetCondition; label: string; hint: string }[] = [
  { value: "working", label: "Working", hint: "Fit to hand out" },
  { value: "damaged", label: "Damaged", hint: "Not usable — needs repair" },
  { value: "not_working", label: "Not working", hint: "Not usable" },
  { value: "expired", label: "Expired", hint: "End of life — not usable" },
];

const CONDITION_TONE: Record<string, string> = {
  working: "bg-success/15 text-success",
  damaged: "bg-warning/15 text-warning",
  not_working: "bg-error/15 text-error",
  expired: "bg-brand-brown-50 text-brand-brown-light",
  lost: "bg-error/15 text-error",
};

export const STATUS_LABEL: Record<AssetStatus, string> = {
  in_stock: "In stock",
  assigned: "Assigned",
  in_repair: "In repair",
  lost: "Lost",
  retired: "Retired",
};

const STATUS_TONE: Record<string, string> = {
  in_stock: "bg-info/15 text-info",
  assigned: "bg-brand-gold/15 text-brand-gold-dark",
  in_repair: "bg-warning/15 text-warning",
  lost: "bg-error/15 text-error",
  retired: "bg-brand-brown-50 text-brand-brown-light",
};

export function conditionLabel(c: string | null | undefined): string {
  if (!c) return "—";
  if (c === "lost") return "Lost";
  return CONDITIONS.find((x) => x.value === c)?.label ?? c.replace(/_/g, " ");
}

function Pill({ tone, children }: { tone: string; children: React.ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium",
        tone,
      )}
    >
      {children}
    </span>
  );
}

export function ConditionChip({ condition }: { condition: string }) {
  return <Pill tone={CONDITION_TONE[condition] ?? ""}>{conditionLabel(condition)}</Pill>;
}

export function StatusChip({ status }: { status: string }) {
  return (
    <Pill tone={STATUS_TONE[status] ?? ""}>
      {STATUS_LABEL[status as AssetStatus] ?? status}
    </Pill>
  );
}

const ICONS: [RegExp, LucideIcon][] = [
  [/charger|battery|adapter/, Battery],
  [/laptop|notebook/, Laptop],
  [/mobile|phone|sim/, Smartphone],
  [/headset|headphone/, Headphones],
  [/monitor|screen|display/, Monitor],
  [/keyboard/, Keyboard],
  [/mouse/, Mouse],
  [/vehicle|bike|car/, Bike],
];

export function categoryIcon(code: string): LucideIcon {
  return ICONS.find(([re]) => re.test(code))?.[1] ?? Package;
}

/** "2026-03-01" -> "01 Mar 2026". */
export function fmtDay(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso.length <= 10 ? `${iso}T00:00:00` : `${iso}Z`);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export function errDetail(e: unknown, fallback: string): string {
  return (
    (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
    fallback
  );
}

/** Refresh every view that shows assets or exit clearance. */
export function invalidateAssets(qc: QueryClient) {
  for (const key of [
    "polish-assets",
    "asset-summary",
    "asset-history",
    "employee-assets",
    "resignation-assets",
    "resignations",
  ]) {
    qc.invalidateQueries({ queryKey: [key] });
  }
}

export function useAssetCategories(includeInactive = false) {
  const { data = [] } = useQuery({
    queryKey: ["asset-categories", includeInactive],
    queryFn: () => polishApi.assetCategories(includeInactive),
    staleTime: 60_000,
  });
  const byCode = useMemo(
    () => new Map<string, AssetCategory>(data.map((c) => [c.code, c])),
    [data],
  );
  const name = (code: string) =>
    byCode.get(code)?.name ?? code.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase());
  return { categories: data, byCode, name };
}

export function useEmployeesById() {
  const { data = [] } = useQuery({
    queryKey: ["employees-all", "assets"],
    queryFn: () => employeesApi.list({ limit: 500 }),
    staleTime: 60_000,
  });
  const byId = useMemo(
    () => new Map<number, EmployeeListItem>(data.map((e) => [e.id, e])),
    [data],
  );
  const name = (id: number | null | undefined) => {
    if (!id) return "—";
    const e = byId.get(id);
    return e ? `${e.first_name} ${e.last_name}` : `#${id}`;
  };
  return { employees: data, byId, name };
}

/** "Lenovo E14 G5" style subtitle. */
export function makeModel(a: Pick<Asset, "brand" | "model">): string {
  return [a.brand, a.model].filter(Boolean).join(" ");
}
