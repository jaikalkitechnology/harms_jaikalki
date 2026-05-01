import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Trash2, Share2, Lock } from "lucide-react";

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
import { reportsApi } from "@/lib/api/reports";

const TYPES = [
  "headcount",
  "attrition",
  "attendance",
  "payroll_cost",
  "compliance",
  "sales",
  "performance",
  "verification",
  "training",
  "custom",
];

export default function SavedReportsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [reportType, setReportType] = useState("headcount");
  const [isShared, setIsShared] = useState(false);

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ["saved-reports"],
    queryFn: reportsApi.listSaved,
  });

  const create = useMutation({
    mutationFn: () =>
      reportsApi.createSaved({
        code,
        name,
        report_type: reportType,
        is_shared: isShared,
      }),
    onSuccess: () => {
      toast.success("Saved");
      setShowForm(false);
      setCode("");
      setName("");
      qc.invalidateQueries({ queryKey: ["saved-reports"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Could not save"),
  });

  const remove = useMutation({
    mutationFn: (id: number) => reportsApi.deleteSaved(id),
    onSuccess: () => {
      toast.success("Deleted");
      qc.invalidateQueries({ queryKey: ["saved-reports"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Could not delete"),
  });

  if (isLoading) return <LoadingScreen label="Loading saved reports…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Saved Reports
          </h1>
          <p className="text-sm text-brand-brown-light">
            Bookmark report definitions for quick access. Mark as shared to
            expose them to teammates.
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
          <Plus className="size-4" />
          {showForm ? "Cancel" : "New"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Save a report</CardTitle>
            <CardDescription>
              Pick a base report type. Filters and scheduling can be added via
              API for now.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Code *</Label>
              <Input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="RPT-XYZ"
              />
            </div>
            <div>
              <Label>Name *</Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div>
              <Label>Type</Label>
              <select
                value={reportType}
                onChange={(e) => setReportType(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="shared"
                checked={isShared}
                onChange={(e) => setIsShared(e.target.checked)}
              />
              <Label htmlFor="shared">Share with teammates</Label>
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                disabled={!code || !name || create.isPending}
                onClick={() => create.mutate()}
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Code</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Sharing</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {reports.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-4 py-10 text-center text-brand-brown-light"
                  >
                    No saved reports yet.
                  </td>
                </tr>
              ) : (
                reports.map((r) => (
                  <tr key={r.id} className="border-t border-brand-brown-50">
                    <td className="px-4 py-3 font-mono text-xs">{r.code}</td>
                    <td className="px-4 py-3">{r.name}</td>
                    <td className="px-4 py-3 capitalize">{r.report_type}</td>
                    <td className="px-4 py-3">
                      {r.is_shared ? (
                        <span className="inline-flex items-center gap-1 text-success text-xs">
                          <Share2 className="size-3" />
                          Shared
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-brand-brown-light text-xs">
                          <Lock className="size-3" />
                          Private
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => remove.mutate(r.id)}
                        className="text-error"
                      >
                        <Trash2 className="size-4" />
                      </Button>
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
