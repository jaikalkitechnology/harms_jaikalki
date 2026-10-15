import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ChevronLeft,
  ChevronRight,
  Info,
  Layers,
  Plus,
  Search,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { polishApi, type Asset } from "@/lib/api/polish";
import { cn } from "@/lib/utils";
import { AssetDetailPanel } from "./assets/AssetDetail";
import { AssignAssetModal, ReturnAssetModal } from "./assets/AssetDialogs";
import { AssetFormModal } from "./assets/AssetForm";
import { CategoriesModal } from "./assets/CategoriesModal";
import {
  CONDITIONS,
  ConditionChip,
  SELECT_CLASS,
  STATUS_LABEL,
  StatusChip,
  categoryIcon,
  makeModel,
  useAssetCategories,
  useEmployeesById,
} from "./assets/shared";

const PAGE_SIZE = 15;

type Quick = "all" | "available" | "assigned" | "not_usable";

export default function AssetsPage() {
  const [search, setSearch] = useState("");
  const [quick, setQuick] = useState<Quick>("all");
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [condition, setCondition] = useState("");
  const [page, setPage] = useState(1);

  const [form, setForm] = useState<Asset | "new" | null>(null);
  const [detailId, setDetailId] = useState<number | null>(null);
  const [assigning, setAssigning] = useState<Asset | null>(null);
  const [returning, setReturning] = useState<Asset | null>(null);
  const [categoriesOpen, setCategoriesOpen] = useState(false);

  const { categories, name: categoryName } = useAssetCategories();
  const { name: employeeName } = useEmployeesById();
  const { data: all = [], isLoading } = useQuery({
    queryKey: ["polish-assets", "all"],
    queryFn: () => polishApi.listAssets(),
  });
  const { data: summary } = useQuery({
    queryKey: ["asset-summary"],
    queryFn: polishApi.assetSummary,
  });

  const byId = useMemo(() => new Map(all.map((a) => [a.id, a])), [all]);
  const accessoryCount = useMemo(() => {
    const m = new Map<number, number>();
    for (const a of all) if (a.parent_asset_id) m.set(a.parent_asset_id, (m.get(a.parent_asset_id) ?? 0) + 1);
    return m;
  }, [all]);

  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return all.filter((a) => {
      if (quick === "available" && !(a.status === "in_stock" && a.is_usable)) return false;
      if (quick === "assigned" && a.status !== "assigned") return false;
      if (quick === "not_usable" && a.is_usable) return false;
      if (category && a.category !== category) return false;
      if (status && a.status !== status) return false;
      if (condition && a.condition !== condition) return false;
      if (!q) return true;
      return [a.asset_tag, a.name, a.brand, a.model, a.serial_number, employeeName(a.assigned_to)]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(q));
    });
  }, [all, quick, category, status, condition, search, employeeName]);

  const pageCount = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const current = Math.min(page, pageCount);
  const pageRows = rows.slice((current - 1) * PAGE_SIZE, current * PAGE_SIZE);
  const detail = detailId ? byId.get(detailId) ?? null : null;

  if (isLoading) return <LoadingScreen label="Loading assets…" />;

  const tiles: { key: Quick; label: string; value: number; tone: string }[] = [
    { key: "all", label: "All assets", value: summary?.total ?? all.length, tone: "text-brand-brown-darker" },
    { key: "available", label: "Available to assign", value: summary?.in_stock_usable ?? 0, tone: "text-success" },
    { key: "assigned", label: "With employees", value: summary?.assigned ?? 0, tone: "text-brand-gold-dark" },
    { key: "not_usable", label: "Not usable", value: summary?.not_usable ?? 0, tone: "text-warning" },
  ];

  const resetPage = () => setPage(1);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold text-brand-brown-darker">
            Asset <span className="display-em">register</span>
          </h1>
          <p className="text-sm text-brand-brown-light">
            Company devices, who has them, their configuration and condition.
          </p>
        </div>
        <PermissionGate permission="admin.users.manage">
          <div className="flex gap-2">
            <Button variant="outline" className="gap-2" onClick={() => setCategoriesOpen(true)}>
              <Layers className="size-4" /> Categories
            </Button>
            <Button className="gap-2" onClick={() => setForm("new")}>
              <Plus className="size-4" /> New asset
            </Button>
          </div>
        </PermissionGate>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {tiles.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => {
              setQuick(t.key);
              resetPage();
            }}
            className={cn(
              "rounded-2xl border bg-card px-4 py-3 text-left shadow-sm transition-colors",
              quick === t.key
                ? "border-brand-gold-dark ring-1 ring-brand-gold-dark/40"
                : "border-brand-brown-100 hover:border-brand-gold/60",
            )}
          >
            <div className="text-xs text-brand-brown-light">{t.label}</div>
            <div className={cn("mt-1 font-display text-2xl font-bold", t.tone)}>{t.value}</div>
          </button>
        ))}
      </div>
      {summary && (summary.in_repair > 0 || summary.lost > 0) && (
        <p className="flex items-center gap-1.5 text-xs text-brand-brown-light">
          <Info className="size-3.5" />
          {summary.in_repair} in repair · {summary.lost} lost · {summary.retired} retired
        </p>
      )}

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-5">
          <div className="relative md:col-span-2">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search tag, name, brand, serial, employee…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                resetPage();
              }}
              className="pl-9"
            />
          </div>
          <select
            className={SELECT_CLASS}
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              resetPage();
            }}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.code} value={c.code}>
                {c.name}
              </option>
            ))}
          </select>
          <select
            className={SELECT_CLASS}
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              resetPage();
            }}
          >
            <option value="">All statuses</option>
            {Object.entries(STATUS_LABEL).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
          <select
            className={SELECT_CLASS}
            value={condition}
            onChange={(e) => {
              setCondition(e.target.value);
              resetPage();
            }}
          >
            <option value="">All conditions</option>
            {CONDITIONS.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full min-w-[860px] text-sm">
            <thead className="bg-brand-brown-50/40 text-left text-xs text-brand-brown-light">
              <tr>
                <th className="px-4 py-3">Asset</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Condition</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">With</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-brand-brown-light">
                    {all.length === 0
                      ? "No assets yet — add the first one with New asset."
                      : "No assets match these filters."}
                  </td>
                </tr>
              ) : (
                pageRows.map((a) => {
                  const Icon = categoryIcon(a.category);
                  const parent = a.parent_asset_id ? byId.get(a.parent_asset_id) : null;
                  const accessories = accessoryCount.get(a.id) ?? 0;
                  return (
                    <tr
                      key={a.id}
                      className="cursor-pointer border-t border-brand-brown-50 hover:bg-brand-brown-50/30"
                      onClick={() => setDetailId(a.id)}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className="grid size-9 shrink-0 place-items-center rounded-lg bg-brand-gold/15 text-brand-gold-dark">
                            <Icon className="size-4" />
                          </div>
                          <div className="min-w-0">
                            <div className="truncate font-medium">{a.name}</div>
                            <div className="truncate text-xs text-brand-brown-light">
                              <span className="font-mono">{a.asset_tag}</span>
                              {makeModel(a) && ` · ${makeModel(a)}`}
                              {parent && ` · with ${parent.asset_tag}`}
                              {accessories > 0 &&
                                ` · +${accessories} accessor${accessories === 1 ? "y" : "ies"}`}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">{categoryName(a.category)}</td>
                      <td className="px-4 py-3">
                        <ConditionChip condition={a.condition} />
                      </td>
                      <td className="px-4 py-3">
                        <StatusChip status={a.status} />
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {a.assigned_to ? (
                          <Link
                            to={`/employees/${a.assigned_to}?tab=assets`}
                            className="hover:text-brand-gold-dark hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {employeeName(a.assigned_to)}
                          </Link>
                        ) : (
                          <span className="text-brand-brown-light">—</span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <PermissionGate permission="admin.users.manage">
                          {a.status === "in_stock" && a.is_usable && (
                            <Button size="sm" variant="outline" onClick={() => setAssigning(a)}>
                              Assign
                            </Button>
                          )}
                          {a.status === "assigned" && (
                            <Button size="sm" variant="outline" onClick={() => setReturning(a)}>
                              Take back
                            </Button>
                          )}
                        </PermissionGate>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {pageCount > 1 && (
        <div className="flex items-center justify-end gap-2">
          <span className="mr-auto text-sm text-brand-brown-light">
            {rows.length} asset{rows.length === 1 ? "" : "s"}
          </span>
          <Button variant="outline" size="sm" disabled={current <= 1} onClick={() => setPage(current - 1)} aria-label="Previous page">
            <ChevronLeft className="size-4" />
          </Button>
          <span className="text-sm text-brand-brown-light">
            Page {current} of {pageCount}
          </span>
          <Button variant="outline" size="sm" disabled={current >= pageCount} onClick={() => setPage(current + 1)} aria-label="Next page">
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}

      {detail && (
        <AssetDetailPanel
          asset={detail}
          onClose={() => setDetailId(null)}
          onEdit={() => setForm(detail)}
          onAssign={() => setAssigning(detail)}
          onReturn={() => setReturning(detail)}
          onOpen={(a) => setDetailId(a.id)}
        />
      )}
      {form && <AssetFormModal asset={form === "new" ? null : form} onClose={() => setForm(null)} />}
      {assigning && <AssignAssetModal asset={assigning} onClose={() => setAssigning(null)} />}
      {returning && <ReturnAssetModal asset={returning} onClose={() => setReturning(null)} />}
      {categoriesOpen && <CategoriesModal onClose={() => setCategoriesOpen(false)} />}
    </div>
  );
}
