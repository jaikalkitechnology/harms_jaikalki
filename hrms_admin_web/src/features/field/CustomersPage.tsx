import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Search, MapPin } from "lucide-react";

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
import { fieldApi, type Customer } from "@/lib/api/field";

const TYPE_COLOR: Record<string, string> = {
  lead: "bg-info/15 text-info",
  prospect: "bg-warning/15 text-warning",
  customer: "bg-success/15 text-success",
  partner: "bg-brand-gold/15 text-brand-gold-dark",
};

export default function CustomersPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [name, setName] = useState("");
  const [type, setType] = useState<Customer["type"]>("lead");
  const [city, setCity] = useState("");
  const [territory, setTerritory] = useState("");
  const [geoLat, setGeoLat] = useState("");
  const [geoLng, setGeoLng] = useState("");

  const { data: customers = [], isLoading } = useQuery({
    queryKey: ["field-customers", search],
    queryFn: () =>
      fieldApi.listCustomers(search.trim() ? { search: search.trim() } : undefined),
  });

  const create = useMutation({
    mutationFn: () =>
      fieldApi.createCustomer({
        name,
        type,
        city: city || undefined,
        territory: territory || undefined,
        geo_lat: geoLat ? Number(geoLat) : undefined,
        geo_lng: geoLng ? Number(geoLng) : undefined,
      }),
    onSuccess: () => {
      toast.success("Customer added");
      setName("");
      setCity("");
      setTerritory("");
      setGeoLat("");
      setGeoLng("");
      setShowForm(false);
      qc.invalidateQueries({ queryKey: ["field-customers"] });
    },
    onError: () => toast.error("Could not save customer"),
  });

  if (isLoading) return <LoadingScreen label="Loading customers…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Customers
          </h1>
          <p className="text-sm text-brand-brown-light">
            Field force CRM — leads, prospects, customers, partners.
          </p>
        </div>
        <Button
          onClick={() => setShowForm((s) => !s)}
          className="gap-2"
        >
          <Plus className="size-4" />
          {showForm ? "Cancel" : "Add customer"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>New customer</CardTitle>
            <CardDescription>
              Geo coordinates are used to enforce visit-time geo-fencing.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="type">Type</Label>
              <select
                id="type"
                value={type}
                onChange={(e) =>
                  setType(e.target.value as Customer["type"])
                }
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="lead">Lead</option>
                <option value="prospect">Prospect</option>
                <option value="customer">Customer</option>
                <option value="partner">Partner</option>
              </select>
            </div>
            <div>
              <Label htmlFor="city">City</Label>
              <Input
                id="city"
                value={city}
                onChange={(e) => setCity(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="territory">Territory</Label>
              <Input
                id="territory"
                value={territory}
                onChange={(e) => setTerritory(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="lat">Latitude</Label>
              <Input
                id="lat"
                value={geoLat}
                onChange={(e) => setGeoLat(e.target.value)}
                placeholder="12.9716"
              />
            </div>
            <div>
              <Label htmlFor="lng">Longitude</Label>
              <Input
                id="lng"
                value={geoLng}
                onChange={(e) => setGeoLng(e.target.value)}
                placeholder="77.5946"
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                disabled={!name || create.isPending}
                onClick={() => create.mutate()}
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="flex items-center gap-2">
        <Search className="size-4 text-brand-brown-light" />
        <Input
          placeholder="Search by name…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Territory</th>
                <th className="px-4 py-3">City</th>
                <th className="px-4 py-3">Geo</th>
              </tr>
            </thead>
            <tbody>
              {customers.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No customers found.
                  </td>
                </tr>
              ) : (
                customers.map((c) => (
                  <tr
                    key={c.id}
                    className="border-t border-brand-brown-50"
                  >
                    <td className="px-4 py-3 font-medium">{c.name}</td>
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
                        <span className="inline-flex items-center gap-1 text-xs">
                          <MapPin className="size-3" />
                          {Number(c.geo_lat).toFixed(4)},{" "}
                          {Number(c.geo_lng).toFixed(4)}
                        </span>
                      ) : (
                        <span className="text-brand-brown-light text-xs">
                          No coords
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
