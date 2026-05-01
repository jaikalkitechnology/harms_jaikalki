import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { LogIn, LogOut } from "lucide-react";

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
import { polishApi } from "@/lib/api/polish";

const STATUS_COLOR: Record<string, string> = {
  scheduled: "bg-info/15 text-info",
  checked_in: "bg-success/15 text-success",
  checked_out: "bg-brand-brown-50 text-brand-brown-darker",
  no_show: "bg-error/15 text-error",
  cancelled: "bg-error/15 text-error",
};

export default function VisitorsPage() {
  const qc = useQueryClient();
  const [qrToken, setQrToken] = useState("");
  const [badge, setBadge] = useState("");

  const { data: visitors = [], isLoading } = useQuery({
    queryKey: ["visitors-today"],
    queryFn: polishApi.todayVisitors,
  });

  const checkIn = useMutation({
    mutationFn: () => polishApi.visitorCheckIn(qrToken.trim(), badge || undefined),
    onSuccess: (v) => {
      toast.success(`Checked in ${v.full_name}`);
      setQrToken("");
      setBadge("");
      qc.invalidateQueries({ queryKey: ["visitors-today"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Check-in failed"),
  });

  const checkOut = useMutation({
    mutationFn: (id: number) => polishApi.visitorCheckOut(id),
    onSuccess: () => {
      toast.success("Checked out");
      qc.invalidateQueries({ queryKey: ["visitors-today"] });
    },
    onError: () => toast.error("Could not check out"),
  });

  if (isLoading) return <LoadingScreen label="Loading visitors…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Visitor Reception
        </h1>
        <p className="text-sm text-brand-brown-light">
          {visitors.length} visitor{visitors.length === 1 ? "" : "s"} expected today.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>QR check-in</CardTitle>
          <CardDescription>
            Scan or paste the visitor's QR token. Optionally assign a badge.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="md:col-span-2">
            <Label>QR token *</Label>
            <Input
              value={qrToken}
              onChange={(e) => setQrToken(e.target.value)}
              placeholder="Paste or scan…"
            />
          </div>
          <div>
            <Label>Badge #</Label>
            <Input value={badge} onChange={(e) => setBadge(e.target.value)} />
          </div>
          <div className="md:col-span-3 flex justify-end">
            <Button
              disabled={!qrToken.trim() || checkIn.isPending}
              onClick={() => checkIn.mutate()}
              className="gap-2"
            >
              <LogIn className="size-4" />
              Check in
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Visitor</th>
                <th className="px-4 py-3">Company</th>
                <th className="px-4 py-3">Purpose</th>
                <th className="px-4 py-3">Expected</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {visitors.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No visitors expected today.
                  </td>
                </tr>
              ) : (
                visitors.map((v) => (
                  <tr key={v.id} className="border-t border-brand-brown-50">
                    <td className="px-4 py-3">
                      <div className="font-medium">{v.full_name}</div>
                      <div className="text-xs text-brand-brown-light">
                        {v.contact_phone ?? v.contact_email ?? "—"}
                      </div>
                    </td>
                    <td className="px-4 py-3">{v.company ?? "—"}</td>
                    <td className="px-4 py-3">{v.purpose}</td>
                    <td className="px-4 py-3 text-xs">
                      {new Date(v.expected_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2 py-1 text-xs ${STATUS_COLOR[v.status] ?? ""}`}
                      >
                        {v.status.replaceAll("_", " ")}
                      </span>
                      {v.badge_number && (
                        <span className="ml-2 text-xs text-brand-brown-light">
                          {v.badge_number}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {v.status === "checked_in" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => checkOut.mutate(v.id)}
                          className="gap-1"
                        >
                          <LogOut className="size-4" />
                          Check out
                        </Button>
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
