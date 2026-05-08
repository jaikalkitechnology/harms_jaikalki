import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  MapPin,
  Pencil,
  Plus,
  Search,
  X,
} from "lucide-react";

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
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import {
  fieldApi,
  type Customer,
  type CustomerCreate,
} from "@/lib/api/field";

const TYPE_COLOR: Record<string, string> = {
  lead: "bg-info/15 text-info",
  prospect: "bg-warning/15 text-warning",
  customer: "bg-success/15 text-success",
  partner: "bg-brand-gold/15 text-brand-gold-dark",
};

const TYPES: Customer["type"][] = ["lead", "prospect", "customer", "partner"];
const PAGE_SIZE = 12;

interface Draft {
  name: string;
  type: Customer["type"];
  city: string;
  state: string;
  pincode: string;
  address: string;
  industry: string;
  gst: string;
  pan: string;
  territory: string;
  geo_lat: string;
  geo_lng: string;
  is_active: boolean;
}

const EMPTY_DRAFT: Draft = {
  name: "",
  type: "lead",
  city: "",
  state: "",
  pincode: "",
  address: "",
  industry: "",
  gst: "",
  pan: "",
  territory: "",
  geo_lat: "",
  geo_lng: "",
  is_active: true,
};

export default function CustomersPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [territoryFilter, setTerritoryFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState<"" | "true" | "false">("");
  const [page, setPage] = useState(1);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);

  const { data: customers = [], isLoading } = useQuery({
    queryKey: [
      "field-customers",
      search,
      typeFilter,
      territoryFilter,
      activeFilter,
    ],
    queryFn: () =>
      fieldApi.listCustomers({
        search: search.trim() || undefined,
        type: (typeFilter || undefined) as Customer["type"] | undefined,
        territory: territoryFilter.trim() || undefined,
        is_active:
          activeFilter === "" ? undefined : activeFilter === "true",
      }),
  });

  const territories = useMemo(() => {
    const s = new Set<string>();
    customers.forEach((c) => c.territory && s.add(c.territory));
    return Array.from(s).sort();
  }, [customers]);

  const create = useMutation({
    mutationFn: () => fieldApi.createCustomer(draftToPayload(draft)),
    onSuccess: () => {
      toast.success("Customer added");
      setEditorOpen(false);
      qc.invalidateQueries({ queryKey: ["field-customers"] });
    },
    onError: () => toast.error("Could not save customer"),
  });

  const update = useMutation({
    mutationFn: () =>
      fieldApi.updateCustomer(editing!.id, {
        ...draftToPayload(draft),
      }),
    onSuccess: () => {
      toast.success("Customer updated");
      setEditorOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["field-customers"] });
    },
    onError: () => toast.error("Could not update customer"),
  });

  const openCreate = () => {
    setEditing(null);
    setDraft(EMPTY_DRAFT);
    setEditorOpen(true);
  };
  const openEdit = (c: Customer) => {
    setEditing(c);
    setDraft({
      name: c.name,
      type: c.type,
      city: c.city ?? "",
      state: c.state ?? "",
      pincode: c.pincode ?? "",
      address: c.address ?? "",
      industry: c.industry ?? "",
      gst: c.gst ?? "",
      pan: c.pan ?? "",
      territory: c.territory ?? "",
      geo_lat: c.geo_lat ?? "",
      geo_lng: c.geo_lng ?? "",
      is_active: c.is_active,
    });
    setEditorOpen(true);
  };

  const pageCount = Math.max(1, Math.ceil(customers.length / PAGE_SIZE));
  const pageRows = customers.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (isLoading) return <LoadingScreen label="Loading customers…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Customers
          </h1>
          <p className="text-sm text-brand-brown-light">
            {customers.length} record{customers.length === 1 ? "" : "s"} match
            current filters.
          </p>
        </div>
        <Button onClick={openCreate} className="gap-2">
          <Plus className="size-4" />
          Add customer
        </Button>
      </div>

      {/* Filter bar */}
      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-5">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search name / city / GST / PAN / industry…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9"
            />
          </div>
          <select
            value={typeFilter}
            onChange={(e) => {
              setTypeFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All types</option>
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <select
            value={territoryFilter}
            onChange={(e) => {
              setTerritoryFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All territories</option>
            {territories.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <select
            value={activeFilter}
            onChange={(e) => {
              setActiveFilter(e.target.value as "" | "true" | "false");
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">Active + inactive</option>
            <option value="true">Active only</option>
            <option value="false">Inactive only</option>
          </select>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Territory</th>
                <th className="px-4 py-3">City</th>
                <th className="px-4 py-3">Geo</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No customers match these filters.
                  </td>
                </tr>
              ) : (
                pageRows.map((c) => (
                  <tr key={c.id} className="border-t border-brand-brown-50">
                    <td className="px-4 py-3 font-medium">
                      {c.name}
                      {(c.gst || c.pan) && (
                        <div className="text-[10px] font-mono text-brand-brown-light">
                          {c.gst && `GST ${c.gst}`}
                          {c.gst && c.pan && " · "}
                          {c.pan && `PAN ${c.pan}`}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2 py-1 text-xs ${TYPE_COLOR[c.type] ?? ""}`}
                      >
                        {c.type}
                      </span>
                    </td>
                    <td className="px-4 py-3">{c.territory ?? "—"}</td>
                    <td className="px-4 py-3">{c.city ?? "—"}</td>
                    <td className="px-4 py-3">
                      {c.geo_lat && c.geo_lng ? (
                        <a
                          href={`https://www.openstreetmap.org/?mlat=${c.geo_lat}&mlon=${c.geo_lng}#map=18/${c.geo_lat}/${c.geo_lng}`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs text-brand-gold-dark hover:underline"
                        >
                          <MapPin className="size-3" />
                          {Number(c.geo_lat).toFixed(4)},{" "}
                          {Number(c.geo_lng).toFixed(4)}
                        </a>
                      ) : (
                        <span className="text-brand-brown-light text-xs">
                          —
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2 py-1 text-xs ${c.is_active ? "bg-success/15 text-success" : "bg-brand-brown-50 text-brand-brown-darker"}`}
                      >
                        {c.is_active ? "active" : "inactive"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        title="Edit"
                        onClick={() => openEdit(c)}
                      >
                        <Pencil className="size-4" />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {pageCount > 1 && (
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <div className="text-sm text-brand-brown-light">
            Page {page} of {pageCount}
          </div>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= pageCount}
            onClick={() => setPage(page + 1)}
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      )}

      {editorOpen && (
        <CustomerEditor
          mode={editing ? "edit" : "create"}
          draft={draft}
          setDraft={setDraft}
          onClose={() => {
            setEditorOpen(false);
            setEditing(null);
          }}
          onSave={() => (editing ? update.mutate() : create.mutate())}
          saving={create.isPending || update.isPending}
        />
      )}
    </div>
  );
}

function draftToPayload(d: Draft): CustomerCreate {
  return {
    name: d.name,
    type: d.type,
    city: d.city || undefined,
    state: d.state || undefined,
    pincode: d.pincode || undefined,
    address: d.address || undefined,
    industry: d.industry || undefined,
    gst: d.gst || undefined,
    pan: d.pan || undefined,
    territory: d.territory || undefined,
    geo_lat: d.geo_lat ? Number(d.geo_lat) : undefined,
    geo_lng: d.geo_lng ? Number(d.geo_lng) : undefined,
  };
}

function CustomerEditor({
  mode,
  draft,
  setDraft,
  onClose,
  onSave,
  saving,
}: {
  mode: "create" | "edit";
  draft: Draft;
  setDraft: (d: Draft) => void;
  onClose: () => void;
  onSave: () => void;
  saving: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-3xl max-h-[92vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>
              {mode === "create" ? "New customer" : "Edit customer"}
            </CardTitle>
            <CardDescription>
              Use the map below to pin the exact location — the coordinates
              are used to enforce visit-time geo-fencing.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="size-4" />
          </Button>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <Label>Name *</Label>
            <Input
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
          </div>
          <div>
            <Label>Type</Label>
            <select
              value={draft.type}
              onChange={(e) =>
                setDraft({ ...draft, type: e.target.value as Customer["type"] })
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label>Territory</Label>
            <Input
              value={draft.territory}
              onChange={(e) =>
                setDraft({ ...draft, territory: e.target.value })
              }
            />
          </div>
          <div>
            <Label>Industry</Label>
            <Input
              value={draft.industry}
              onChange={(e) =>
                setDraft({ ...draft, industry: e.target.value })
              }
            />
          </div>
          <div>
            <Label>GST</Label>
            <Input
              value={draft.gst}
              onChange={(e) => setDraft({ ...draft, gst: e.target.value })}
            />
          </div>
          <div>
            <Label>PAN</Label>
            <Input
              value={draft.pan}
              onChange={(e) => setDraft({ ...draft, pan: e.target.value })}
            />
          </div>
          <div className="md:col-span-2">
            <Label>Address</Label>
            <Input
              value={draft.address}
              onChange={(e) =>
                setDraft({ ...draft, address: e.target.value })
              }
            />
          </div>
          <div>
            <Label>City</Label>
            <Input
              value={draft.city}
              onChange={(e) => setDraft({ ...draft, city: e.target.value })}
            />
          </div>
          <div>
            <Label>State</Label>
            <Input
              value={draft.state}
              onChange={(e) => setDraft({ ...draft, state: e.target.value })}
            />
          </div>
          <div>
            <Label>Pincode</Label>
            <Input
              value={draft.pincode}
              onChange={(e) =>
                setDraft({ ...draft, pincode: e.target.value })
              }
            />
          </div>
          {mode === "edit" && (
            <label className="flex items-center gap-2 mt-7">
              <input
                type="checkbox"
                checked={draft.is_active}
                onChange={(e) =>
                  setDraft({ ...draft, is_active: e.target.checked })
                }
              />
              <span className="text-sm">Active</span>
            </label>
          )}

          <div className="md:col-span-2">
            <Label>Location</Label>
            <MapPicker
              lat={draft.geo_lat}
              lng={draft.geo_lng}
              onPick={(lat, lng, address) =>
                setDraft({
                  ...draft,
                  geo_lat: lat,
                  geo_lng: lng,
                  address: draft.address || address || draft.address,
                })
              }
              suggestSearch={[draft.name, draft.address, draft.city, draft.state]
                .filter(Boolean)
                .join(", ")}
            />
          </div>

          <div className="md:col-span-2 flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button disabled={saving || !draft.name} onClick={onSave}>
              {saving ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

interface NominatimHit {
  display_name: string;
  lat: string;
  lon: string;
}

function MapPicker({
  lat,
  lng,
  onPick,
  suggestSearch,
}: {
  lat: string;
  lng: string;
  onPick: (lat: string, lng: string, address?: string) => void;
  suggestSearch: string;
}) {
  const [query, setQuery] = useState(suggestSearch);
  const [hits, setHits] = useState<NominatimHit[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Update the search box when the parent has a meaningful suggestion
  // (eg. user typed name/city in the upper form). Only set once.
  useEffect(() => {
    if (!query && suggestSearch) setQuery(suggestSearch);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const url =
        "https://nominatim.openstreetmap.org/search?format=json&limit=5&q=" +
        encodeURIComponent(query.trim());
      const r = await fetch(url, {
        headers: { Accept: "application/json" },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data: NominatimHit[] = await r.json();
      setHits(data);
      if (data.length === 0) setError("No matches.");
    } catch (err: any) {
      setError(err?.message ?? "Search failed");
      setHits([]);
    } finally {
      setSearching(false);
    }
  };

  const useDeviceLocation = () => {
    if (!navigator.geolocation) {
      setError("Geolocation not supported in this browser");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        onPick(
          pos.coords.latitude.toFixed(6),
          pos.coords.longitude.toFixed(6),
        );
      },
      (err) => setError(err.message),
    );
  };

  const previewMapUrl = useMemo(() => {
    const la = Number(lat);
    const lo = Number(lng);
    if (!Number.isFinite(la) || !Number.isFinite(lo)) return null;
    const half = 0.005;
    return `https://www.openstreetmap.org/export/embed.html?bbox=${lo - half}%2C${la - half}%2C${lo + half}%2C${la + half}&layer=mapnik&marker=${la}%2C${lo}`;
  }, [lat, lng]);

  return (
    <div className="space-y-3">
      <form onSubmit={onSearch} className="flex flex-col sm:flex-row gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
          <Input
            placeholder="Search the map (address, landmark, city)…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button type="submit" disabled={searching || !query.trim()}>
          {searching ? "Searching…" : "Search"}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={useDeviceLocation}
          title="Use my current location"
        >
          <MapPin className="size-4" />
        </Button>
      </form>

      {error && <div className="text-xs text-error">{error}</div>}

      {hits.length > 0 && (
        <div className="rounded-md border border-brand-brown-50 max-h-44 overflow-y-auto divide-y">
          {hits.map((h, i) => (
            <button
              type="button"
              key={`${h.lat}-${h.lon}-${i}`}
              onClick={() => {
                onPick(
                  Number(h.lat).toFixed(6),
                  Number(h.lon).toFixed(6),
                  h.display_name,
                );
                setHits([]);
              }}
              className="w-full text-left p-2 text-sm hover:bg-brand-brown-50/40"
            >
              <div className="font-medium truncate">{h.display_name}</div>
              <div className="text-[10px] text-brand-brown-light">
                {Number(h.lat).toFixed(5)}, {Number(h.lon).toFixed(5)}
              </div>
            </button>
          ))}
        </div>
      )}

      <div className="grid grid-cols-2 gap-2">
        <div>
          <Label>Latitude</Label>
          <Input
            value={lat}
            placeholder="12.9716"
            onChange={(e) => onPick(e.target.value, lng)}
          />
        </div>
        <div>
          <Label>Longitude</Label>
          <Input
            value={lng}
            placeholder="77.5946"
            onChange={(e) => onPick(lat, e.target.value)}
          />
        </div>
      </div>

      {previewMapUrl ? (
        <div className="space-y-2">
          <iframe
            title="Customer location"
            src={previewMapUrl}
            className="w-full h-72 rounded-md border border-brand-brown-50"
          />
          <a
            href={`https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=18/${lat}/${lng}`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs text-brand-gold-dark hover:underline"
          >
            <ExternalLink className="size-3" /> Open in OpenStreetMap
          </a>
        </div>
      ) : (
        <div className="rounded-md border border-dashed border-brand-brown-50 p-6 text-center text-sm text-brand-brown-light">
          Pick a result above, drop your device location, or paste lat/lng to
          preview the map here.
        </div>
      )}
    </div>
  );
}
