import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Bike,
  ChevronLeft,
  ChevronRight,
  Headphones,
  Laptop,
  Pencil,
  Plus,
  Search,
  Smartphone,
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
import { polishApi, type Asset } from "@/lib/api/polish";
import { employeesApi } from "@/lib/api/employees";

const STATUS_COLOR: Record<string, string> = {
  in_stock: "bg-success/15 text-success",
  assigned: "bg-info/15 text-info",
  in_repair: "bg-warning/15 text-warning",
  lost: "bg-error/15 text-error",
  retired: "bg-brand-brown-50 text-brand-brown-darker",
};

const CATEGORIES = [
  "laptop",
  "mobile",
  "headset",
  "monitor",
  "keyboard",
  "mouse",
  "vehicle",
  "other",
];

const PAGE_SIZE = 12;

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

interface CreateDraft {
  asset_tag: string;
  name: string;
  category: string;
  serial_number: string;
  notes: string;
}

interface EditDraft {
  name: string;
  category: string;
  serial_number: string;
  condition: string;
  purchase_date: string;
  warranty_until: string;
  purchase_cost: string;
  notes: string;
}

export default function AssetsPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [page, setPage] = useState(1);

  const [createOpen, setCreateOpen] = useState(false);
  const [createDraft, setCreateDraft] = useState<CreateDraft>({
    asset_tag: "",
    name: "",
    category: "laptop",
    serial_number: "",
    notes: "",
  });

  const [editing, setEditing] = useState<Asset | null>(null);
  const [editDraft, setEditDraft] = useState<EditDraft>({
    name: "",
    category: "laptop",
    serial_number: "",
    condition: "good",
    purchase_date: "",
    warranty_until: "",
    purchase_cost: "",
    notes: "",
  });

  const [assignTarget, setAssignTarget] = useState<Asset | null>(null);
  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [returnTarget, setReturnTarget] = useState<Asset | null>(null);
  const [returnCondition, setReturnCondition] = useState("good");

  const { data: assets = [], isLoading } = useQuery({
    queryKey: ["polish-assets", search, statusFilter, categoryFilter],
    queryFn: () =>
      polishApi.listAssets({
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        category: categoryFilter || undefined,
      }),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });

  const create = useMutation({
    mutationFn: () =>
      polishApi.createAsset({
        asset_tag: createDraft.asset_tag,
        name: createDraft.name,
        category: createDraft.category,
        serial_number: createDraft.serial_number || null,
        notes: createDraft.notes || null,
        condition: "new",
      }),
    onSuccess: () => {
      toast.success("Asset added");
      setCreateOpen(false);
      setCreateDraft({
        asset_tag: "",
        name: "",
        category: "laptop",
        serial_number: "",
        notes: "",
      });
      qc.invalidateQueries({ queryKey: ["polish-assets"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not add"),
  });

  const update = useMutation({
    mutationFn: () =>
      polishApi.updateAsset(editing!.id, {
        name: editDraft.name,
        category: editDraft.category,
        serial_number: editDraft.serial_number || null,
        condition: editDraft.condition,
        purchase_date: editDraft.purchase_date || null,
        warranty_until: editDraft.warranty_until || null,
        purchase_cost: editDraft.purchase_cost
          ? Number(editDraft.purchase_cost)
          : null,
        notes: editDraft.notes || null,
      }),
    onSuccess: () => {
      toast.success("Asset updated");
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["polish-assets"] });
    },
    onError: () => toast.error("Could not update"),
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
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not assign"),
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

  const openEdit = (a: Asset) => {
    setEditing(a);
    setEditDraft({
      name: a.name,
      category: a.category,
      serial_number: a.serial_number ?? "",
      condition: a.condition,
      purchase_date: a.purchase_date ?? "",
      warranty_until: a.warranty_until ?? "",
      purchase_cost: a.purchase_cost ?? "",
      notes: a.notes ?? "",
    });
  };

  const employeeName = (id: number | null) => {
    if (!id) return "—";
    const emp = employees.find((e) => e.id === id);
    return emp ? `${emp.first_name} ${emp.last_name}` : `#${id}`;
  };

  const pageCount = Math.max(1, Math.ceil(assets.length / PAGE_SIZE));
  const pageRows = assets.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (isLoading) return <LoadingScreen label="Loading assets…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Asset Register
          </h1>
          <p className="text-sm text-brand-brown-light">
            {assets.length} asset{assets.length === 1 ? "" : "s"} match current
            filters.
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} className="gap-2">
          <Plus className="size-4" /> New asset
        </Button>
      </div>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-4">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search tag / name / serial / notes…"
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
            <option value="in_stock">In stock</option>
            <option value="assigned">Assigned</option>
            <option value="in_repair">In repair</option>
            <option value="lost">Lost</option>
            <option value="retired">Retired</option>
          </select>
          <select
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-brand-brown-50/40 text-left">
              <tr>
                <th className="px-4 py-3">Tag</th>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Assigned to</th>
                <th className="px-4 py-3">Condition</th>
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
                    No assets match these filters.
                  </td>
                </tr>
              ) : (
                pageRows.map((a) => {
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
                          {a.serial_number && (
                            <span className="text-[10px] text-brand-brown-light">
                              · sn {a.serial_number}
                            </span>
                          )}
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
                      <td className="px-4 py-3 capitalize text-xs">
                        {a.condition}
                      </td>
                      <td className="px-4 py-3 text-right whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="sm"
                          title="Edit"
                          onClick={() => openEdit(a)}
                        >
                          <Pencil className="size-4" />
                        </Button>
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

      {createOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card className="w-full max-w-2xl">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>New asset</CardTitle>
                <CardDescription>
                  The asset starts in <em>in stock</em> and can be assigned
                  later.
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setCreateOpen(false)}
              >
                <X className="size-4" />
              </Button>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Tag *</Label>
                <Input
                  value={createDraft.asset_tag}
                  onChange={(e) =>
                    setCreateDraft({
                      ...createDraft,
                      asset_tag: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label>Name *</Label>
                <Input
                  value={createDraft.name}
                  onChange={(e) =>
                    setCreateDraft({ ...createDraft, name: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>Category</Label>
                <select
                  value={createDraft.category}
                  onChange={(e) =>
                    setCreateDraft({ ...createDraft, category: e.target.value })
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>Serial number</Label>
                <Input
                  value={createDraft.serial_number}
                  onChange={(e) =>
                    setCreateDraft({
                      ...createDraft,
                      serial_number: e.target.value,
                    })
                  }
                />
              </div>
              <div className="md:col-span-2">
                <Label>Notes</Label>
                <Input
                  value={createDraft.notes}
                  onChange={(e) =>
                    setCreateDraft({ ...createDraft, notes: e.target.value })
                  }
                />
              </div>
              <div className="md:col-span-2 flex justify-end gap-2">
                <Button variant="outline" onClick={() => setCreateOpen(false)}>
                  Cancel
                </Button>
                <Button
                  disabled={
                    !createDraft.asset_tag ||
                    !createDraft.name ||
                    create.isPending
                  }
                  onClick={() => create.mutate()}
                >
                  Save
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {editing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card className="w-full max-w-3xl max-h-[92vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Edit asset</CardTitle>
                <CardDescription className="font-mono text-xs">
                  {editing.asset_tag}
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditing(null)}
              >
                <X className="size-4" />
              </Button>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Name</Label>
                <Input
                  value={editDraft.name}
                  onChange={(e) =>
                    setEditDraft({ ...editDraft, name: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>Category</Label>
                <select
                  value={editDraft.category}
                  onChange={(e) =>
                    setEditDraft({ ...editDraft, category: e.target.value })
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>Serial number</Label>
                <Input
                  value={editDraft.serial_number}
                  onChange={(e) =>
                    setEditDraft({
                      ...editDraft,
                      serial_number: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label>Condition</Label>
                <select
                  value={editDraft.condition}
                  onChange={(e) =>
                    setEditDraft({ ...editDraft, condition: e.target.value })
                  }
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  {["new", "good", "fair", "damaged", "retired"].map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>Purchase date</Label>
                <Input
                  type="date"
                  value={editDraft.purchase_date}
                  onChange={(e) =>
                    setEditDraft({
                      ...editDraft,
                      purchase_date: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label>Warranty until</Label>
                <Input
                  type="date"
                  value={editDraft.warranty_until}
                  onChange={(e) =>
                    setEditDraft({
                      ...editDraft,
                      warranty_until: e.target.value,
                    })
                  }
                />
              </div>
              <div>
                <Label>Purchase cost (₹)</Label>
                <Input
                  type="number"
                  value={editDraft.purchase_cost}
                  onChange={(e) =>
                    setEditDraft({
                      ...editDraft,
                      purchase_cost: e.target.value,
                    })
                  }
                />
              </div>
              <div className="md:col-span-2">
                <Label>Notes</Label>
                <Input
                  value={editDraft.notes}
                  onChange={(e) =>
                    setEditDraft({ ...editDraft, notes: e.target.value })
                  }
                />
              </div>
              <div className="md:col-span-2 flex justify-end gap-2">
                <Button variant="outline" onClick={() => setEditing(null)}>
                  Cancel
                </Button>
                <Button
                  disabled={update.isPending}
                  onClick={() => update.mutate()}
                >
                  {update.isPending ? "Saving…" : "Save"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

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
