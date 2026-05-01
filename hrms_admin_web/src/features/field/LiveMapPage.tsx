import { useQuery } from "@tanstack/react-query";
import { Battery, BatteryLow, MapPin, RefreshCw } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { fieldApi } from "@/lib/api/field";

const STATUS_COLOR: Record<string, string> = {
  idle: "bg-brand-brown-50 text-brand-brown-darker",
  on_visit: "bg-success/15 text-success",
  in_transit: "bg-info/15 text-info",
  off_duty: "bg-error/15 text-error",
};

function formatTime(ts: string) {
  const d = new Date(ts);
  const diff = Date.now() - d.getTime();
  if (diff < 60_000) return "Just now";
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} min ago`;
  return d.toLocaleTimeString();
}

export default function LiveMapPage() {
  const { data: locations = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ["field-live-map"],
    queryFn: fieldApi.liveMap,
    refetchInterval: 30_000,
  });

  if (isLoading) return <LoadingScreen label="Loading team map…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Live Team Map
          </h1>
          <p className="text-sm text-brand-brown-light">
            Real-time location of field employees · auto-refreshes every 30s.
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
          <CardTitle>{locations.length} field employees tracked</CardTitle>
          <CardDescription>
            Map renderer (Mapbox/Leaflet) ships with the geo-services upgrade.
            Coordinates are usable in the table below.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Employee</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Last seen</th>
                <th className="px-4 py-3">Coordinates</th>
                <th className="px-4 py-3">Battery</th>
              </tr>
            </thead>
            <tbody>
              {locations.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No location updates yet today.
                  </td>
                </tr>
              ) : (
                locations.map((row) => (
                  <tr
                    key={row.employee_id}
                    className="border-t border-brand-brown-50"
                  >
                    <td className="px-4 py-3 font-medium">
                      <div>{row.name}</div>
                      <div className="text-xs text-brand-brown-light">
                        {row.employee_code}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2 py-1 text-xs ${STATUS_COLOR[row.current_status] ?? ""}`}
                      >
                        {row.current_status.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3">{formatTime(row.timestamp)}</td>
                    <td className="px-4 py-3">
                      <a
                        href={`https://www.google.com/maps?q=${row.lat},${row.lng}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-brand-gold-dark hover:underline"
                      >
                        <MapPin className="size-3" />
                        {row.lat.toFixed(4)}, {row.lng.toFixed(4)}
                      </a>
                    </td>
                    <td className="px-4 py-3">
                      {row.battery_pct !== null ? (
                        <span className="inline-flex items-center gap-1">
                          {row.battery_pct < 20 ? (
                            <BatteryLow className="size-4 text-error" />
                          ) : (
                            <Battery className="size-4 text-success" />
                          )}
                          {row.battery_pct}%
                        </span>
                      ) : (
                        <span className="text-brand-brown-light text-xs">
                          —
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
