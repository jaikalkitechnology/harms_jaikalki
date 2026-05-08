import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Calendar,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Pencil,
  Play,
  Plus,
  Search,
  Users,
  Video,
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
import { trainerApi, type TrainingSession } from "@/lib/api/trainer";
import { fmtIst, fmtIstTime } from "@/lib/datetime";

const STATUS_COLOR: Record<string, string> = {
  scheduled: "bg-info/15 text-info",
  open_for_registration: "bg-brand-gold/15 text-brand-gold-dark",
  in_progress: "bg-warning/15 text-warning",
  completed: "bg-success/15 text-success",
  cancelled: "bg-error/15 text-error",
};

const PAGE_SIZE = 9;

interface Draft {
  code: string;
  title: string;
  description: string;
  trainer_id: number | "";
  start: string;
  end: string;
  session_type: string;
  capacity: string;
  meeting_url: string;
  location: string;
}

const EMPTY_DRAFT: Draft = {
  code: "",
  title: "",
  description: "",
  trainer_id: "",
  start: "",
  end: "",
  session_type: "virtual",
  capacity: "30",
  meeting_url: "",
  location: "",
};

function toLocalDateTime(iso: string): string {
  // backend gives ISO; HTML datetime-local needs "YYYY-MM-DDTHH:mm".
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const off = d.getTimezoneOffset();
  const local = new Date(d.getTime() - off * 60_000);
  return local.toISOString().slice(0, 16);
}

export default function SessionsPage() {
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [trainerFilter, setTrainerFilter] = useState<number | "">("");
  const [upcomingOnly, setUpcomingOnly] = useState(false);
  const [page, setPage] = useState(1);

  const [editorOpen, setEditorOpen] = useState(false);
  const [editing, setEditing] = useState<TrainingSession | null>(null);
  const [draft, setDraft] = useState<Draft>(EMPTY_DRAFT);

  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ["sessions", search, statusFilter, trainerFilter, upcomingOnly],
    queryFn: () =>
      trainerApi.listSessions({
        search: search.trim() || undefined,
        status: statusFilter || undefined,
        trainer_id: trainerFilter === "" ? undefined : trainerFilter,
        upcoming_only: upcomingOnly || undefined,
      }),
  });
  const { data: trainers = [] } = useQuery({
    queryKey: ["trainers"],
    queryFn: () => trainerApi.listTrainers(),
  });

  const create = useMutation({
    mutationFn: () =>
      trainerApi.createSession({
        code: draft.code,
        title: draft.title,
        description: draft.description || null,
        trainer_id: Number(draft.trainer_id),
        scheduled_start: draft.start,
        scheduled_end: draft.end,
        session_type: draft.session_type,
        capacity: Number(draft.capacity),
        meeting_url: draft.meeting_url || null,
        location: draft.location || null,
      }),
    onSuccess: () => {
      toast.success("Session scheduled");
      setEditorOpen(false);
      setDraft(EMPTY_DRAFT);
      qc.invalidateQueries({ queryKey: ["sessions"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not schedule"),
  });

  const update = useMutation({
    mutationFn: () =>
      trainerApi.updateSession(editing!.id, {
        title: draft.title,
        description: draft.description || null,
        trainer_id: Number(draft.trainer_id),
        scheduled_start: draft.start,
        scheduled_end: draft.end,
        session_type: draft.session_type,
        capacity: Number(draft.capacity),
        meeting_url: draft.meeting_url || null,
        location: draft.location || null,
      }),
    onSuccess: () => {
      toast.success("Session updated");
      setEditorOpen(false);
      setEditing(null);
      qc.invalidateQueries({ queryKey: ["sessions"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not update"),
  });

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      trainerApi.setStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["sessions"] });
    },
    onError: () => toast.error("Could not update status"),
  });

  const openCreate = () => {
    setEditing(null);
    setDraft(EMPTY_DRAFT);
    setEditorOpen(true);
  };
  const openEdit = (s: TrainingSession) => {
    setEditing(s);
    setDraft({
      code: s.code,
      title: s.title,
      description: s.description ?? "",
      trainer_id: s.trainer_id,
      start: toLocalDateTime(s.scheduled_start),
      end: toLocalDateTime(s.scheduled_end),
      session_type: s.session_type,
      capacity: String(s.capacity),
      meeting_url: s.meeting_url ?? "",
      location: s.location ?? "",
    });
    setEditorOpen(true);
  };

  const launchMeeting = (s: TrainingSession) => {
    if (!s.meeting_url) {
      toast.error("This session has no meeting URL.");
      return;
    }
    // Flip to in_progress so participants see "live" state.
    if (s.status === "scheduled" || s.status === "open_for_registration") {
      setStatus.mutate({ id: s.id, status: "in_progress" });
    }
    window.open(s.meeting_url, "_blank", "noreferrer");
  };

  const trainerById = new Map(trainers.map((t) => [t.id, t]));

  const pageCount = Math.max(1, Math.ceil(sessions.length / PAGE_SIZE));
  const pageRows = sessions.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (isLoading) return <LoadingScreen label="Loading sessions…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Training Sessions
          </h1>
          <p className="text-sm text-brand-brown-light">
            {sessions.length} session{sessions.length === 1 ? "" : "s"} match
            current filters.
          </p>
        </div>
        <Button onClick={openCreate} className="gap-2">
          <Plus className="size-4" /> Schedule
        </Button>
      </div>

      <Card>
        <CardContent className="grid gap-3 p-4 md:grid-cols-4">
          <div className="md:col-span-2 relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-brand-brown-light" />
            <Input
              placeholder="Search code / title / description / location…"
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
          <select
            value={trainerFilter}
            onChange={(e) => {
              setTrainerFilter(e.target.value ? Number(e.target.value) : "");
              setPage(1);
            }}
            className="h-10 rounded-md border border-input bg-background px-3 text-sm"
          >
            <option value="">All trainers</option>
            {trainers.map((t) => (
              <option key={t.id} value={t.id}>
                {t.full_name}
              </option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm md:col-span-4">
            <input
              type="checkbox"
              checked={upcomingOnly}
              onChange={(e) => {
                setUpcomingOnly(e.target.checked);
                setPage(1);
              }}
            />
            Show upcoming only
          </label>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {pageRows.length === 0 ? (
          <Card className="md:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-brand-brown-light">
              No sessions match these filters.
            </CardContent>
          </Card>
        ) : (
          pageRows.map((s) => {
            const t = trainerById.get(s.trainer_id);
            const editable =
              s.status !== "completed" && s.status !== "cancelled";
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
                    {fmtIst(s.scheduled_start)} →{" "}
                    {fmtIstTime(s.scheduled_end)}
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
                  {s.meeting_url && (
                    <div className="flex items-center gap-1 text-xs text-brand-gold-dark truncate">
                      <Video className="size-3 shrink-0" />
                      <a
                        href={s.meeting_url}
                        target="_blank"
                        rel="noreferrer"
                        className="truncate hover:underline"
                      >
                        {s.meeting_url}
                      </a>
                    </div>
                  )}
                  <div className="pt-2 flex gap-2 flex-wrap">
                    {s.meeting_url && editable && (
                      <Button
                        size="sm"
                        className="gap-1"
                        onClick={() => launchMeeting(s)}
                      >
                        <Play className="size-3" /> Start &amp; Launch
                      </Button>
                    )}
                    {!s.meeting_url && editable && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          setStatus.mutate({ id: s.id, status: "in_progress" })
                        }
                      >
                        Start
                      </Button>
                    )}
                    {editable && (
                      <Button
                        size="sm"
                        variant="ghost"
                        title="Edit"
                        onClick={() => openEdit(s)}
                      >
                        <Pencil className="size-3" />
                      </Button>
                    )}
                    {editable && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          setStatus.mutate({ id: s.id, status: "completed" })
                        }
                      >
                        Complete
                      </Button>
                    )}
                    {editable && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() =>
                          setStatus.mutate({ id: s.id, status: "cancelled" })
                        }
                      >
                        Cancel
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

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

      {editorOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <Card className="w-full max-w-3xl max-h-[92vh] overflow-y-auto">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>
                  {editing ? "Edit session" : "Schedule session"}
                </CardTitle>
                <CardDescription>
                  Conflict detection runs against the trainer's other sessions.
                  When a meeting URL is set, "Start &amp; Launch" opens it for
                  attendees and flips the session to <em>in progress</em>.
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setEditorOpen(false);
                  setEditing(null);
                }}
              >
                <X className="size-4" />
              </Button>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2">
              <div>
                <Label>Code *</Label>
                <Input
                  value={draft.code}
                  disabled={!!editing}
                  placeholder="JKT-TS-XXX"
                  onChange={(e) => setDraft({ ...draft, code: e.target.value })}
                />
              </div>
              <div>
                <Label>Title *</Label>
                <Input
                  value={draft.title}
                  onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                />
              </div>
              <div>
                <Label>Trainer *</Label>
                <select
                  value={draft.trainer_id}
                  onChange={(e) =>
                    setDraft({
                      ...draft,
                      trainer_id: e.target.value ? Number(e.target.value) : "",
                    })
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
                  value={draft.session_type}
                  onChange={(e) =>
                    setDraft({ ...draft, session_type: e.target.value })
                  }
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
                  value={draft.start}
                  onChange={(e) => setDraft({ ...draft, start: e.target.value })}
                />
              </div>
              <div>
                <Label>End *</Label>
                <Input
                  type="datetime-local"
                  value={draft.end}
                  onChange={(e) => setDraft({ ...draft, end: e.target.value })}
                />
              </div>
              <div>
                <Label>Capacity</Label>
                <Input
                  type="number"
                  value={draft.capacity}
                  onChange={(e) =>
                    setDraft({ ...draft, capacity: e.target.value })
                  }
                />
              </div>
              <div>
                <Label>Meeting URL</Label>
                <Input
                  value={draft.meeting_url}
                  placeholder="https://meet.jit.si/jkt-..."
                  onChange={(e) =>
                    setDraft({ ...draft, meeting_url: e.target.value })
                  }
                />
              </div>
              <div className="md:col-span-2">
                <Label>Location</Label>
                <Input
                  value={draft.location}
                  onChange={(e) =>
                    setDraft({ ...draft, location: e.target.value })
                  }
                />
              </div>
              <div className="md:col-span-2">
                <Label>Description</Label>
                <textarea
                  value={draft.description}
                  rows={3}
                  onChange={(e) =>
                    setDraft({ ...draft, description: e.target.value })
                  }
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                />
              </div>
              <div className="md:col-span-2 flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => {
                    setEditorOpen(false);
                    setEditing(null);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  disabled={
                    !draft.title ||
                    !draft.trainer_id ||
                    !draft.start ||
                    !draft.end ||
                    (!editing && !draft.code) ||
                    create.isPending ||
                    update.isPending
                  }
                  onClick={() =>
                    editing ? update.mutate() : create.mutate()
                  }
                >
                  Save
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

