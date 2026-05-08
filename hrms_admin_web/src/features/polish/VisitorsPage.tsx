import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Camera,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  LogIn,
  LogOut,
  QrCode,
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
import { Label } from "@/components/ui/label";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { polishApi, type Visitor } from "@/lib/api/polish";
import { fmtIst } from "@/lib/datetime";

const STATUS_COLOR: Record<string, string> = {
  scheduled: "bg-info/15 text-info",
  checked_in: "bg-success/15 text-success",
  checked_out: "bg-brand-brown-50 text-brand-brown-darker",
  no_show: "bg-error/15 text-error",
  cancelled: "bg-error/15 text-error",
};

const PAGE_SIZE = 12;

export default function VisitorsPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [page, setPage] = useState(1);

  const [scannerOpen, setScannerOpen] = useState(false);
  const [manualToken, setManualToken] = useState("");
  const [badge, setBadge] = useState("");

  const { data: visitors = [], isLoading } = useQuery({
    queryKey: ["visitors", search, statusFilter, fromDate, toDate],
    queryFn: () =>
      polishApi.listVisitors({
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        from_date: fromDate || undefined,
        to_date: toDate || undefined,
      }),
  });

  const checkIn = useMutation({
    mutationFn: ({ token, badgeNum }: { token: string; badgeNum?: string }) =>
      polishApi.visitorCheckIn(token, badgeNum),
    onSuccess: (v) => {
      toast.success(`Checked in ${v.full_name}`);
      qc.invalidateQueries({ queryKey: ["visitors"] });
      setManualToken("");
      setBadge("");
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Check-in failed"),
  });

  const checkOut = useMutation({
    mutationFn: (id: number) => polishApi.visitorCheckOut(id),
    onSuccess: () => {
      toast.success("Checked out");
      qc.invalidateQueries({ queryKey: ["visitors"] });
    },
    onError: () => toast.error("Could not check out"),
  });

  const finish = useMutation({
    mutationFn: (id: number) => polishApi.visitorCheckOut(id),
    onSuccess: () => {
      toast.success("Visit finished");
      qc.invalidateQueries({ queryKey: ["visitors"] });
    },
    onError: () => toast.error("Could not finish"),
  });

  const handleScan = (token: string) => {
    setScannerOpen(false);
    if (!token) return;
    checkIn.mutate({ token: token.trim(), badgeNum: badge || undefined });
  };

  const counts = useMemo(() => {
    const c = { scheduled: 0, checked_in: 0, checked_out: 0, total: visitors.length };
    visitors.forEach((v) => {
      if (v.status in c) (c as any)[v.status]++;
    });
    return c;
  }, [visitors]);

  const pageCount = Math.max(1, Math.ceil(visitors.length / PAGE_SIZE));
  const pageRows = visitors.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (isLoading) return <LoadingScreen label="Loading visitors…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Visitor Reception
          </h1>
          <p className="text-sm text-brand-brown-light">
            {counts.total} visitor{counts.total === 1 ? "" : "s"} match current
            filters · {counts.scheduled} scheduled · {counts.checked_in} on
            site · {counts.checked_out} finished.
          </p>
        </div>
        <Button onClick={() => setScannerOpen(true)} className="gap-2">
          <Camera className="size-4" /> Scan visitor QR
        </Button>
      </div>

      {/* Manual token entry as fallback */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <QrCode className="size-4" /> Manual check-in
          </CardTitle>
          <CardDescription>
            If the camera scanner isn't available, paste the QR token here.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="md:col-span-2">
            <Label>QR token</Label>
            <Input
              value={manualToken}
              onChange={(e) => setManualToken(e.target.value)}
              placeholder="Paste or scan…"
            />
          </div>
          <div>
            <Label>Badge #</Label>
            <Input value={badge} onChange={(e) => setBadge(e.target.value)} />
          </div>
          <div className="md:col-span-3 flex justify-end">
            <Button
              disabled={!manualToken.trim() || checkIn.isPending}
              onClick={() =>
                checkIn.mutate({
                  token: manualToken.trim(),
                  badgeNum: badge || undefined,
                })
              }
              className="gap-2"
            >
              <LogIn className="size-4" /> Check in
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-4">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search name / company / purpose / phone / email…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All statuses</option>
            {Object.keys(STATUS_COLOR).map((s) => (
              <option key={s} value={s}>
                {s.replaceAll("_", " ")}
              </option>
            ))}
          </select>
          <div className="flex gap-2">
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => {
                setFromDate(e.target.value);
                setPage(1);
              }}
            />
            <Input
              type="date"
              value={toDate}
              onChange={(e) => {
                setToDate(e.target.value);
                setPage(1);
              }}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Visitor</th>
                <th className="px-4 py-3">Company</th>
                <th className="px-4 py-3">Purpose</th>
                <th className="px-4 py-3">Expected</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {pageRows.length === 0 ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No visitors match these filters.
                  </td>
                </tr>
              ) : (
                pageRows.map((v) => (
                  <VisitorRow
                    key={v.id}
                    v={v}
                    onCheckOut={() => checkOut.mutate(v.id)}
                    onFinish={() => finish.mutate(v.id)}
                    busy={checkOut.isPending || finish.isPending}
                  />
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

      {scannerOpen && (
        <ScannerModal
          onClose={() => setScannerOpen(false)}
          onScan={handleScan}
        />
      )}
    </div>
  );
}

function VisitorRow({
  v,
  onCheckOut,
  onFinish,
  busy,
}: {
  v: Visitor;
  onCheckOut: () => void;
  onFinish: () => void;
  busy: boolean;
}) {
  return (
    <tr className="border-t border-brand-brown-50">
      <td className="px-4 py-3">
        <div className="font-medium">{v.full_name}</div>
        <div className="text-xs text-brand-brown-light">
          {v.contact_phone ?? v.contact_email ?? "—"}
        </div>
      </td>
      <td className="px-4 py-3">{v.company ?? "—"}</td>
      <td className="px-4 py-3">{v.purpose}</td>
      <td className="px-4 py-3 text-xs">{fmtIst(v.expected_at)}</td>
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
      <td className="px-4 py-3 text-right whitespace-nowrap">
        {v.status === "checked_in" && (
          <>
            <Button
              size="sm"
              variant="outline"
              onClick={onCheckOut}
              disabled={busy}
              className="gap-1"
            >
              <LogOut className="size-3" /> Check out
            </Button>{" "}
            <Button
              size="sm"
              variant="outline"
              className="border-success/40 text-success hover:bg-success/10 gap-1"
              onClick={onFinish}
              disabled={busy}
            >
              <CheckCircle2 className="size-3" /> Finish
            </Button>
          </>
        )}
      </td>
    </tr>
  );
}

function ScannerModal({
  onClose,
  onScan,
}: {
  onClose: () => void;
  onScan: (token: string) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const scannerIdRef = useRef<string>(`qr-reader-${Math.random().toString(36).slice(2, 8)}`);
  const [error, setError] = useState<string | null>(null);
  const [camerasMissing, setCamerasMissing] = useState(false);

  useEffect(() => {
    let stopped = false;
    let html5QrCode: any;

    (async () => {
      try {
        const mod = await import("html5-qrcode");
        const Html5Qrcode = mod.Html5Qrcode;
        html5QrCode = new Html5Qrcode(scannerIdRef.current);
        const cams = await Html5Qrcode.getCameras();
        if (!cams || cams.length === 0) {
          setCamerasMissing(true);
          return;
        }
        // Prefer the back camera if available.
        const cam =
          cams.find((c: any) => /back|rear|environment/i.test(c.label)) ??
          cams[0];
        await html5QrCode.start(
          { deviceId: { exact: cam.id } },
          { fps: 10, qrbox: { width: 240, height: 240 } },
          (decoded: string) => {
            if (stopped) return;
            stopped = true;
            html5QrCode
              .stop()
              .catch(() => undefined)
              .finally(() => onScan(decoded));
          },
          () => {
            // ignore frame-level decode failures
          },
        );
      } catch (e: any) {
        setError(e?.message ?? "Could not start camera");
      }
    })();

    return () => {
      stopped = true;
      try {
        if (html5QrCode) {
          html5QrCode
            .stop()
            .catch(() => undefined)
            .finally(() => html5QrCode.clear?.());
        }
      } catch {
        /* noop */
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
      onClick={onClose}
    >
      <Card
        className="w-full max-w-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Camera className="size-4" /> Scan visitor QR
          </CardTitle>
          <CardDescription>
            Point the camera at the visitor's QR code. Check-in happens
            automatically on a successful scan.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div
            id={scannerIdRef.current}
            ref={containerRef}
            className="w-full aspect-square rounded-md bg-black overflow-hidden"
          />
          {camerasMissing && (
            <div className="text-sm text-error">
              No camera detected on this device. Use the manual token field
              below to check in.
            </div>
          )}
          {error && (
            <div className="text-sm text-error">{error}</div>
          )}
          <div className="flex justify-end">
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
