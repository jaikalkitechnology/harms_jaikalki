import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Laptop, Smartphone, Headphones, Bike } from "lucide-react";

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
import { polishApi, type Asset } from "@/lib/api/polish";
import { employeesApi } from "@/lib/api/employees";

const STATUS_COLOR: Record<string, string> = {
  in_stock: "bg-success/15 text-success",
  assigned: "bg-info/15 text-info",
  in_repair: "bg-warning/15 text-warning",
  lost: "bg-error/15 text-error",
  retired: "bg-brand-brown-50 text-brand-brown-darker",
};

function categoryIcon(c: string) {
  switch (c) {
    case "laptop":
      return Laptop;
    case "mobile":
      return Smartphone;
    case "headset":
      return Headphones;
    case "vehicle":
      return Bike;
    default:
      return Laptop;
  }
}

export default function AssetsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");

  const [tag, setTag] = useState("");
  const [name, setName] = useState("");
  const [category, setCategory] = useState("laptop");

  const [assignTarget, setAssignTarget] = useState<Asset | null>(null);
  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [returnTarget, setReturnTarget] = useState<Asset | null>(null);
  const [returnCondition, setReturnCondition] = useState("good");

  const { data: assets = [], isLoading } = useQuery({
    queryKey: ["polish-assets", statusFilter],
    queryFn: () =>
      polishApi.listAssets(statusFilter ? { status: statusFilter } : undefined),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });

  const create = useMutation({
    mutationFn: () =>
      polishApi.createAsset({
        asset_tag: tag,
        name,
        category,
        condition: "new",
      }),
    onSuccess: () => {
      toast.success("Asset added");
      setShowForm(false);
      setTag("");
      setName("");
      qc.invalidateQueries({ queryKey: ["polish-assets"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Could not add"),
  });

  const assign = useMutation({
    mutationFn: () =>
      polishApi.assignAsset(assignTarget!.id, Number(employeeId)),
    onSuccess: () => {
      toast.success("Assigned");
      setAssignTarget(null);
      setEmployeeId("");
      qc.invalidateQueries({ queryKey: ["polish-assets"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Could not assign"),
  });

  const returnIt = useMutation({
    mutationFn: () =>
      polishApi.returnAsset(returnTarget!.id, returnCondition),
    onSuccess: () => {
      toast.success("Returned");
      setReturnTarget(null);
      setReturnCondition("good");
      qc.invalidateQueries({ queryKey: ["polish-assets"] });
    },
    onError: () => toast.error("Could not return"),
  });

  if (isLoading) return <LoadingScreen label="Loading assets…" />;

  const employeeName = (id: number | null) => {
    if (!id) return "—";
    const emp = employees.find((e) => e.id === id);
    return emp ? `${emp.first_name} ${emp.last_name}` : `#${id}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Asset Register
          </h1>
          <p className="text-sm text-brand-brown-light">
            {assets.length} asset{assets.length === 1 ? "" : "s"} tracked.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="h-9 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All</option>
            <option value="in_stock">In stock</option>
            <option value="assigned">Assigned</option>
            <option value="in_repair">In repair</option>
            <option value="retired">Retired</option>
          </select>
          <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
            <Plus className="size-4" />
            {showForm ? "Cancel" : "New asset"}
          </Button>
        </div>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add asset</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            <div>
              <Label>Tag *</Label>
              <Input value={tag} onChange={(e) => setTag(e.target.value)} />
            </div>
            <div>
              <Label>Name *</Label>
              <Input value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <Label>Category</Label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {[
                  "laptop",
                  "mobile",
                  "headset",
                  "monitor",
                  "keyboard",
                  "mouse",
                  "vehicle",
                  "other",
                ].map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="md:col-span-3 flex justify-end">
              <Button
                disabled={!tag || !name || create.isPending}
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
                <th className="px-4 py-3">Tag</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Assigned to</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {assets.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-brand-brown-light">
                    No assets.
                  </td>
                </tr>
              ) : (
                assets.map((a) => {
                  const Icon = categoryIcon(a.category);
                  return (
                    <tr key={a.id} className="border-t border-brand-brown-50">
                      <td className="px-4 py-3 font-mono text-xs">
                        {a.asset_tag}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Icon className="size-4 text-brand-brown-light" />
                          {a.name}
                        </div>
                      </td>
                      <td className="px-4 py-3 capitalize">{a.category}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-1 text-xs ${STATUS_COLOR[a.status] ?? ""}`}
                        >
                          {a.status.replaceAll("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {employeeName(a.assigned_to)}
                      </td>
                      <td className="px-4 py-3">
                        {a.status === "in_stock" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setAssignTarget(a)}
                          >
                            Assign
                          </Button>
                        )}
                        {a.status === "assigned" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setReturnTarget(a)}
                          >
                            Return
                          </Button>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {assignTarget && (
        <Card>
          <CardHeader>
            <CardTitle>Assign {assignTarget.asset_tag}</CardTitle>
            <CardDescription>{assignTarget.name}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label>Employee *</Label>
              <select
                value={employeeId}
                onChange={(e) =>
                  setEmployeeId(e.target.value ? Number(e.target.value) : "")
                }
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">— Select —</option>
                {employees.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.employee_code} — {emp.first_name} {emp.last_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" onClick={() => setAssignTarget(null)}>
                Cancel
              </Button>
              <Button
                disabled={!employeeId || assign.isPending}
                onClick={() => assign.mutate()}
              >
                Assign
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {returnTarget && (
        <Card>
          <CardHeader>
            <CardTitle>Return {returnTarget.asset_tag}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <Label>Return condition</Label>
              <select
                value={returnCondition}
                onChange={(e) => setReturnCondition(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="good">Good</option>
                <option value="fair">Fair</option>
                <option value="damaged">Damaged → in repair</option>
                <option value="lost">Lost</option>
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" onClick={() => setReturnTarget(null)}>
                Cancel
              </Button>
              <Button
                disabled={returnIt.isPending}
                onClick={() => returnIt.mutate()}
              >
                Confirm return
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
