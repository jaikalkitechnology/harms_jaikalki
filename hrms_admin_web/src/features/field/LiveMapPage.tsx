import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Battery,
  BatteryLow,
  Circle,
  ExternalLink,
  MapPin,
  RefreshCw,
  Search,
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
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { fieldApi, type LiveMapEntry } from "@/lib/api/field";
import { fmtIst } from "@/lib/datetime";

const STATUS_COLOR: Record<string, string> = {
  idle: "bg-brand-brown-50 text-brand-brown-darker",
  on_visit: "bg-success/15 text-success",
  in_transit: "bg-info/15 text-info",
  off_duty: "bg-error/15 text-error",
};

function ago(minutes: number): string {
  if (minutes <= 0) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 60 * 24) return `${Math.floor(minutes / 60)}h ago`;
  return `${Math.floor(minutes / 60 / 24)}d ago`;
}

export default function LiveMapPage() {
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [onlineOnly, setOnlineOnly] = useState(false);

  const { data: locations = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ["field-live-map"],
    queryFn: fieldApi.liveMap,
    refetchInterval: 30_000,
  });

  const filtered = useMemo(() => {
    let list: LiveMapEntry[] = locations;
    if (onlineOnly) list = list.filter((r) => r.is_online);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (r) =>
          r.name.toLowerCase().includes(q) ||
          r.employee_code.toLowerCase().includes(q),
      );
    }
    return list;
  }, [locations, search, onlineOnly]);

  const selected = useMemo(
    () => locations.find((r) => r.employee_id === selectedId) ?? null,
    [locations, selectedId],
  );

  const onlineCount = locations.filter((r) => r.is_online).length;

  if (isLoading) return <LoadingScreen label="Loading team map…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Field Force · Live map
          </div>
          <h1 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            Live <span className="display-em">team map</span>
          </h1>
          <p className="text-sm text-brand-brown-light mt-1">
            {locations.length} employees tracked · {onlineCount} online ·
            auto-refresh 30s.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => refetch()}
          disabled={isFetching}
          className="gap-2"
        >
          <RefreshCw className={`size-4 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filter</CardTitle>
          <CardDescription>
            Pick an employee on the right to centre the map on their last
            known location.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid sm:grid-cols-[1fr_auto_auto] gap-3 items-end">
          <div className="relative">
            <Search className="h-4 w-4 absolute left-2 top-1/2 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search by name or code…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>
          <label className="flex items-center gap-2 text-sm h-10">
            <input
              type="checkbox"
              checked={onlineOnly}
              onChange={(e) => setOnlineOnly(e.target.checked)}
            />
            Online only
          </label>
          {selectedId !== null && (
            <Button variant="ghost" onClick={() => setSelectedId(null)}>
              Clear selection
            </Button>
          )}
        </CardContent>
      </Card>

      <div className="grid lg:grid-cols-[1fr_22rem] gap-4">
        {/* Map preview */}
        <Card>
          <CardHeader>
            <CardTitle>
              {selected ? `${selected.name} (${selected.employee_code})` : "Team map"}
            </CardTitle>
            <CardDescription>
              {selected
                ? `${selected.is_online ? "Online" : "Offline"} · last seen ${ago(selected.last_seen_minutes)}`
                : "Click any row to focus the map on a single employee."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selected ? (
              <iframe
                key={`${selected.employee_id}-${selected.timestamp}`}
                title="Live location"
                src={mapUrl(selected.lat, selected.lng)}
                className="w-full h-[420px] rounded-lg border border-brand-brown-50"
              />
            ) : (
              <div className="text-sm text-brand-brown-light h-[420px] grid place-items-center border border-dashed border-brand-brown-50 rounded-lg">
                <div className="text-center">
                  <MapPin className="mx-auto h-10 w-10 text-brand-gold-dark mb-2" />
                  Pick an employee to see their last known location.
                </div>
              </div>
            )}
            {selected && (
              <a
                href={`https://www.openstreetmap.org/?mlat=${selected.lat}&mlon=${selected.lng}#map=18/${selected.lat}/${selected.lng}`}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-brand-gold-dark underline mt-2 inline-flex items-center gap-1"
              >
                Open in OpenStreetMap <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </CardContent>
        </Card>

        {/* Roster */}
        <Card>
          <CardHeader>
            <CardTitle>Employees</CardTitle>
            <CardDescription>
              {filtered.length} match{filtered.length === 1 ? "" : "es"}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0 max-h-[480px] overflow-y-auto">
            {filtered.length === 0 ? (
              <div className="px-4 py-10 text-center text-brand-brown-light text-sm">
                No location updates yet.
              </div>
            ) : (
              filtered.map((row) => {
                const active = row.employee_id === selectedId;
                return (
                  <button
                    key={row.employee_id}
                    onClick={() => setSelectedId(row.employee_id)}
                    className={`w-full text-left px-4 py-3 border-b border-brand-brown-50 hover:bg-brand-brown-50 ${
                      active ? "bg-brand-gold/10" : ""
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Circle
                        className={`h-3 w-3 ${
                          row.is_online ? "fill-success text-success" : "fill-brand-brown-light text-brand-brown-light"
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{row.name}</div>
                        <div className="text-[11px] text-brand-brown-light">
                          {row.employee_code} ·{" "}
                          <span
                            className={`${
                              STATUS_COLOR[row.current_status] ?? ""
                            } px-1.5 py-0.5 rounded text-[10px]`}
                          >
                            {row.current_status.replace("_", " ")}
                          </span>{" "}
                          · {ago(row.last_seen_minutes)}
                        </div>
                      </div>
                      {row.battery_pct != null && (
                        <span className="text-[11px] inline-flex items-center gap-0.5">
                          {row.battery_pct < 20 ? (
                            <BatteryLow className="h-3 w-3 text-error" />
                          ) : (
                            <Battery className="h-3 w-3 text-success" />
                          )}
                          {row.battery_pct}%
                        </span>
                      )}
                    </div>
                  </button>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>

      {/* Detail row beneath the map */}
      {selected && (
        <Card>
          <CardContent className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-4">
            <Field label="Employee">
              {selected.name} ({selected.employee_code})
            </Field>
            <Field label="Status">
              <span
                className={`text-xs px-2 py-0.5 rounded ${STATUS_COLOR[selected.current_status] ?? ""}`}
              >
                {selected.current_status.replace("_", " ")}
              </span>
            </Field>
            <Field label="Last seen">
              {ago(selected.last_seen_minutes)} ({fmtIst(selected.timestamp)})
            </Field>
            <Field label="Battery">
              {selected.battery_pct != null ? `${selected.battery_pct}%` : "—"}
            </Field>
            <Field label="Coordinates">
              <a
                href={`https://www.google.com/maps?q=${selected.lat},${selected.lng}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-brand-gold-dark hover:underline"
              >
                <MapPin className="h-3 w-3" />
                {selected.lat.toFixed(5)}, {selected.lng.toFixed(5)}
              </a>
            </Field>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function mapUrl(lat: number, lng: number): string {
  // OpenStreetMap embed with a small bbox around the point and a marker.
  const halfDeg = 0.005; // ~500 m at the equator
  const left = lng - halfDeg;
  const right = lng + halfDeg;
  const top = lat + halfDeg;
  const bottom = lat - halfDeg;
  return `https://www.openstreetmap.org/export/embed.html?bbox=${left}%2C${bottom}%2C${right}%2C${top}&layer=mapnik&marker=${lat}%2C${lng}`;
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-0.5">
        {label}
      </div>
      <div className="text-sm text-brand-brown-darker break-words">
        {children}
      </div>
    </div>
  );
}
