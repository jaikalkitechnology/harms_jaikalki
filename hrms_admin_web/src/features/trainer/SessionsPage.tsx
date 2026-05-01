import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Plus, Calendar, Users, MapPin } from "lucide-react";

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
import { trainerApi } from "@/lib/api/trainer";

const STATUS_COLOR: Record<string, string> = {
  scheduled: "bg-info/15 text-info",
  open_for_registration: "bg-brand-gold/15 text-brand-gold-dark",
  in_progress: "bg-warning/15 text-warning",
  completed: "bg-success/15 text-success",
  cancelled: "bg-error/15 text-error",
};

export default function SessionsPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const [code, setCode] = useState("");
  const [title, setTitle] = useState("");
  const [trainerId, setTrainerId] = useState<number | "">("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [sessionType, setSessionType] = useState("virtual");
  const [capacity, setCapacity] = useState("30");
  const [meetingUrl, setMeetingUrl] = useState("");
  const [location, setLocation] = useState("");

  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => trainerApi.listSessions(),
  });
  const { data: trainers = [] } = useQuery({
    queryKey: ["trainers"],
    queryFn: () => trainerApi.listTrainers(),
  });

  const create = useMutation({
    mutationFn: () =>
      trainerApi.createSession({
        code,
        title,
        trainer_id: Number(trainerId),
        scheduled_start: start,
        scheduled_end: end,
        session_type: sessionType,
        capacity: Number(capacity),
        meeting_url: meetingUrl || null,
        location: location || null,
      }),
    onSuccess: () => {
      toast.success("Session scheduled");
      setShowForm(false);
      setCode("");
      setTitle("");
      setTrainerId("");
      setStart("");
      setEnd("");
      setMeetingUrl("");
      setLocation("");
      qc.invalidateQueries({ queryKey: ["sessions"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Could not schedule"),
  });

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      trainerApi.setStatus(id, status),
    onSuccess: () => {
      toast.success("Updated");
      qc.invalidateQueries({ queryKey: ["sessions"] });
    },
    onError: () => toast.error("Could not update"),
  });

  if (isLoading) return <LoadingScreen label="Loading sessions…" />;

  const trainerById = new Map(trainers.map((t) => [t.id, t]));

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Training Sessions
          </h1>
          <p className="text-sm text-brand-brown-light">
            {sessions.length} session{sessions.length === 1 ? "" : "s"} on the
            calendar.
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
          <Plus className="size-4" />
          {showForm ? "Cancel" : "Schedule"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Schedule session</CardTitle>
            <CardDescription>
              Conflict detection runs against the trainer's other sessions.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div>
              <Label>Code *</Label>
              <Input
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="JKT-TS-XXX"
              />
            </div>
            <div>
              <Label>Title *</Label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </div>
            <div>
              <Label>Trainer *</Label>
              <select
                value={trainerId}
                onChange={(e) =>
                  setTrainerId(e.target.value ? Number(e.target.value) : "")
                }
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">— Select —</option>
                {trainers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.full_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Type</Label>
              <select
                value={sessionType}
                onChange={(e) => setSessionType(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="virtual">Virtual</option>
                <option value="in_person">In-person</option>
                <option value="hybrid">Hybrid</option>
                <option value="self_paced">Self-paced</option>
              </select>
            </div>
            <div>
              <Label>Start *</Label>
              <Input
                type="datetime-local"
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </div>
            <div>
              <Label>End *</Label>
              <Input
                type="datetime-local"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </div>
            <div>
              <Label>Capacity</Label>
              <Input
                type="number"
                value={capacity}
                onChange={(e) => setCapacity(e.target.value)}
              />
            </div>
            <div>
              <Label>Meeting URL</Label>
              <Input
                value={meetingUrl}
                onChange={(e) => setMeetingUrl(e.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Label>Location</Label>
              <Input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                disabled={
                  !code ||
                  !title ||
                  !trainerId ||
                  !start ||
                  !end ||
                  create.isPending
                }
                onClick={() => create.mutate()}
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {sessions.length === 0 ? (
          <Card className="md:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-brand-brown-light">
              No sessions scheduled.
            </CardContent>
          </Card>
        ) : (
          sessions.map((s) => {
            const t = trainerById.get(s.trainer_id);
            return (
              <Card key={s.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base">{s.title}</CardTitle>
                    <span
                      className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${STATUS_COLOR[s.status] ?? ""}`}
                    >
                      {s.status.replaceAll("_", " ")}
                    </span>
                  </div>
                  <CardDescription className="font-mono text-xs">
                    {s.code} · {t?.full_name ?? `Trainer #${s.trainer_id}`}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex items-center gap-1 text-xs">
                    <Calendar className="size-3" />
                    {new Date(s.scheduled_start).toLocaleString()} →{" "}
                    {new Date(s.scheduled_end).toLocaleTimeString()}
                  </div>
                  <div className="flex items-center gap-1 text-xs">
                    <Users className="size-3" />
                    {s.participants_count} / {s.capacity} registered
                  </div>
                  {s.location && (
                    <div className="flex items-center gap-1 text-xs">
                      <MapPin className="size-3" />
                      {s.location}
                    </div>
                  )}
                  {s.qr_token && (
                    <div className="font-mono text-[10px] text-brand-brown-light truncate">
                      QR: {s.qr_token}
                    </div>
                  )}
                  <div className="pt-2 flex gap-2 flex-wrap">
                    {s.status !== "completed" && s.status !== "cancelled" && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            setStatus.mutate({ id: s.id, status: "in_progress" })
                          }
                        >
                          Start
                        </Button>
                        <Button
                          size="sm"
                          onClick={() =>
                            setStatus.mutate({ id: s.id, status: "completed" })
                          }
                        >
                          Complete
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() =>
                            setStatus.mutate({ id: s.id, status: "cancelled" })
                          }
                        >
                          Cancel
                        </Button>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>
    </div>
  );
}
