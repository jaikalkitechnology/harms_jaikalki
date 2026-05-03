import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Trash2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { PermissionGate } from "@/components/shared/PermissionGate";
import { leavesApi } from "@/lib/api/leaves";
import { fmtIstDate } from "@/lib/datetime";

export default function HolidaysPage() {
  const queryClient = useQueryClient();
  const [year, setYear] = useState(new Date().getFullYear());

  const { data: holidays = [], isLoading } = useQuery({
    queryKey: ["holidays", year],
    queryFn: () => leavesApi.holidays(year),
  });

  const [date, setDate] = useState("");
  const [name, setName] = useState("");
  const [type, setType] = useState<"national" | "regional" | "company">(
    "national",
  );

  const create = useMutation({
    mutationFn: () =>
      leavesApi.createHoliday({
        date,
        name,
        type,
        is_optional: false,
        location: "ALL",
      }),
    onSuccess: () => {
      toast.success("Holiday added");
      setDate("");
      setName("");
      queryClient.invalidateQueries({ queryKey: ["holidays"] });
    },
    onError: () => toast.error("Could not add holiday"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => leavesApi.deleteHoliday(id),
    onSuccess: () => {
      toast.success("Holiday removed");
      queryClient.invalidateQueries({ queryKey: ["holidays"] });
    },
  });

  if (isLoading) return <LoadingScreen label="Loading holidays…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Phase 3 · Holidays
          </div>
          <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
            Holiday <span className="display-em">calendar</span>
          </h2>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="year">Year</Label>
          <Input
            id="year"
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="w-28"
          />
        </div>
      </div>

      <PermissionGate permission="admin.users.manage">
        <Card>
          <CardHeader>
            <CardTitle>Add holiday</CardTitle>
            <CardDescription>
              Holidays are excluded from leave-day calculations.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (date && name) create.mutate();
              }}
              className="grid md:grid-cols-4 gap-3 items-end"
            >
              <div className="space-y-1.5">
                <Label htmlFor="hdate">Date</Label>
                <Input
                  id="hdate"
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                />
              </div>
              <div className="space-y-1.5 md:col-span-2">
                <Label htmlFor="hname">Name</Label>
                <Input
                  id="hname"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Diwali"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="htype">Type</Label>
                <select
                  id="htype"
                  value={type}
                  onChange={(e) => setType(e.target.value as typeof type)}
                  className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
                >
                  <option value="national">National</option>
                  <option value="regional">Regional</option>
                  <option value="company">Company</option>
                </select>
              </div>
              <Button
                type="submit"
                disabled={!date || !name || create.isPending}
                className="md:col-span-4"
              >
                <Plus className="h-4 w-4" /> Add holiday
              </Button>
            </form>
          </CardContent>
        </Card>
      </PermissionGate>

      <Card>
        <CardHeader>
          <CardTitle>{year} holidays</CardTitle>
          <CardDescription>{holidays.length} entries</CardDescription>
        </CardHeader>
        <CardContent>
          {holidays.length === 0 ? (
            <p className="text-sm text-brand-brown-light">
              No holidays configured for {year}.
            </p>
          ) : (
            <div className="space-y-1">
              {holidays.map((h) => (
                <div
                  key={h.id}
                  className="flex items-center justify-between py-2 border-b border-brand-brown-100/50 last:border-0"
                >
                  <div>
                    <div className="font-medium">{h.name}</div>
                    <div className="text-xs text-brand-brown-light">
                      {fmtIstDate(h.date)}{" "}
                      · {h.type}
                    </div>
                  </div>
                  <PermissionGate permission="admin.users.manage">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => remove.mutate(h.id)}
                    >
                      <Trash2 className="h-4 w-4 text-error" />
                    </Button>
                  </PermissionGate>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
