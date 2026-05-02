import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Clock, Plus, Save, Trash2 } from "lucide-react";

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
import { organizationApi, type Shift } from "@/lib/api/organization";

function toHM(t: string): string {
  // backend returns "HH:MM:SS" — strip seconds for the time input
  return (t ?? "").slice(0, 5);
}

function ensureSeconds(t: string): string {
  if (!t) return t;
  return t.length === 5 ? `${t}:00` : t;
}

export default function ShiftsPage() {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["shifts"],
    queryFn: organizationApi.listShifts,
  });

  const [draft, setDraft] = useState({
    code: "",
    name: "",
    start_time: "09:00",
    end_time: "18:00",
    break_duration_min: 60,
    is_default: false,
    is_active: true,
  });

  const create = useMutation({
    mutationFn: () =>
      organizationApi.createShift({
        ...draft,
        start_time: ensureSeconds(draft.start_time),
        end_time: ensureSeconds(draft.end_time),
      }),
    onSuccess: () => {
      toast.success("Shift added");
      setDraft({
        code: "",
        name: "",
        start_time: "09:00",
        end_time: "18:00",
        break_duration_min: 60,
        is_default: false,
        is_active: true,
      });
      qc.invalidateQueries({ queryKey: ["shifts"] });
    },
    onError: () => toast.error("Could not add shift"),
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" /> Shifts
          </CardTitle>
          <CardDescription>
            Working windows assigned to employees. One shift can be marked as
            default for new hires.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid sm:grid-cols-2 md:grid-cols-6 gap-3">
          <div>
            <Label>Code</Label>
            <Input
              value={draft.code}
              onChange={(e) =>
                setDraft({ ...draft, code: e.target.value.toUpperCase() })
              }
              placeholder="GEN"
            />
          </div>
          <div className="md:col-span-2">
            <Label>Name</Label>
            <Input
              value={draft.name}
              onChange={(e) => setDraft({ ...draft, name: e.target.value })}
              placeholder="General 9–6"
            />
          </div>
          <div>
            <Label>Start</Label>
            <Input
              type="time"
              value={draft.start_time}
              onChange={(e) =>
                setDraft({ ...draft, start_time: e.target.value })
              }
            />
          </div>
          <div>
            <Label>End</Label>
            <Input
              type="time"
              value={draft.end_time}
              onChange={(e) => setDraft({ ...draft, end_time: e.target.value })}
            />
          </div>
          <div>
            <Label>Break (min)</Label>
            <Input
              type="number"
              min={0}
              max={480}
              value={draft.break_duration_min}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  break_duration_min: Number(e.target.value),
                })
              }
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={draft.is_default}
              onChange={(e) =>
                setDraft({ ...draft, is_default: e.target.checked })
              }
            />
            Default
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={draft.is_active}
              onChange={(e) =>
                setDraft({ ...draft, is_active: e.target.checked })
              }
            />
            Active
          </label>
          <div className="sm:col-span-2 md:col-span-6">
            <Button
              disabled={!draft.code || !draft.name}
              onClick={() => create.mutate()}
            >
              <Plus className="h-4 w-4 mr-1" /> Add
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm min-w-[800px]">
            <thead className="text-left text-brand-brown-light">
              <tr>
                <th className="py-2 px-4">Code</th>
                <th>Name</th>
                <th>Start</th>
                <th>End</th>
                <th>Break</th>
                <th>Default</th>
                <th>Active</th>
                <th className="text-right pr-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(data as Shift[]).map((s) => (
                <ShiftRow key={s.id} shift={s} />
              ))}
              {data.length === 0 && (
                <tr>
                  <td colSpan={8} className="text-center py-6 text-brand-brown-light">
                    No shifts yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}

function ShiftRow({ shift }: { shift: Shift }) {
  const qc = useQueryClient();
  const [name, setName] = useState(shift.name);
  const [startTime, setStartTime] = useState(toHM(shift.start_time));
  const [endTime, setEndTime] = useState(toHM(shift.end_time));
  const [breakMin, setBreakMin] = useState(shift.break_duration_min);
  const [isDefault, setIsDefault] = useState(shift.is_default);
  const [isActive, setIsActive] = useState(shift.is_active);

  const save = useMutation({
    mutationFn: () =>
      organizationApi.updateShift(shift.id, {
        name,
        start_time: ensureSeconds(startTime),
        end_time: ensureSeconds(endTime),
        break_duration_min: breakMin,
        is_default: isDefault,
        is_active: isActive,
      }),
    onSuccess: () => {
      toast.success("Saved");
      qc.invalidateQueries({ queryKey: ["shifts"] });
    },
    onError: () => toast.error("Save failed"),
  });
  const remove = useMutation({
    mutationFn: () => organizationApi.deleteShift(shift.id),
    onSuccess: () => {
      toast.success("Removed");
      qc.invalidateQueries({ queryKey: ["shifts"] });
    },
    onError: () => toast.error("Could not delete (assigned to employees?)"),
  });

  return (
    <tr className="border-t border-brand-brown-50">
      <td className="py-2 px-4 font-mono">{shift.code}</td>
      <td>
        <Input value={name} onChange={(e) => setName(e.target.value)} />
      </td>
      <td>
        <Input
          type="time"
          value={startTime}
          onChange={(e) => setStartTime(e.target.value)}
        />
      </td>
      <td>
        <Input
          type="time"
          value={endTime}
          onChange={(e) => setEndTime(e.target.value)}
        />
      </td>
      <td>
        <Input
          type="number"
          min={0}
          max={480}
          value={breakMin}
          onChange={(e) => setBreakMin(Number(e.target.value))}
        />
      </td>
      <td>
        <input
          type="checkbox"
          checked={isDefault}
          onChange={(e) => setIsDefault(e.target.checked)}
        />
      </td>
      <td>
        <input
          type="checkbox"
          checked={isActive}
          onChange={(e) => setIsActive(e.target.checked)}
        />
      </td>
      <td className="text-right pr-4">
        <Button size="sm" variant="outline" onClick={() => save.mutate()}>
          <Save className="h-3 w-3" />
        </Button>{" "}
        <Button
          size="sm"
          variant="ghost"
          onClick={() => {
            if (confirm(`Delete ${shift.name}?`)) remove.mutate();
          }}
        >
          <Trash2 className="h-3 w-3" />
        </Button>
      </td>
    </tr>
  );
}
