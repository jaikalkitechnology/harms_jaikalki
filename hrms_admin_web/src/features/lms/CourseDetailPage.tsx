import { useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  FileText,
  Image as ImageIcon,
  Plus,
  Trash2,
  Upload,
  Video,
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
import { lmsApi, type CourseModule, type Lesson } from "@/lib/api/lms";

const CONTENT_TYPES = [
  "video",
  "pdf",
  "article",
  "external_link",
  "image",
  "audio",
  "quiz",
  "scorm",
  "live_session",
] as const;
type ContentType = (typeof CONTENT_TYPES)[number];

const NEEDS_URL = new Set<ContentType>([
  "video",
  "pdf",
  "external_link",
  "image",
  "audio",
  "scorm",
  "live_session",
]);

const TYPE_ICON: Record<string, typeof Video> = {
  video: Video,
  pdf: FileText,
  external_link: ExternalLink,
  image: ImageIcon,
  audio: Video,
  article: FileText,
  quiz: CheckCircle2,
  scorm: FileText,
  live_session: Video,
};

export default function CourseDetailPage() {
  const { id } = useParams();
  const courseId = Number(id);
  const nav = useNavigate();
  const qc = useQueryClient();

  const { data: course, isLoading } = useQuery({
    queryKey: ["course", courseId],
    queryFn: () => lmsApi.getCourse(courseId),
    enabled: Number.isFinite(courseId),
  });

  const publish = useMutation({
    mutationFn: () => lmsApi.publish(courseId, !course?.is_published),
    onSuccess: () => {
      toast.success(course?.is_published ? "Unpublished" : "Published");
      qc.invalidateQueries({ queryKey: ["course", courseId] });
      qc.invalidateQueries({ queryKey: ["lms-courses"] });
    },
  });

  if (isLoading || !course) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <button
            onClick={() => nav(-1)}
            className="text-xs font-mono uppercase tracking-[0.2em] text-brand-brown-light hover:text-brand-brown-darker flex items-center gap-1 mb-1"
          >
            <ArrowLeft className="h-3 w-3" /> Back
          </button>
          <h1 className="font-display text-2xl md:text-3xl font-bold text-brand-brown-darker">
            {course.title}
          </h1>
          <div className="text-sm text-brand-brown-light font-mono">
            {course.code} · {course.estimated_hours}h · {course.difficulty} ·{" "}
            {course.is_published ? "Published" : "Draft"}
          </div>
        </div>
        <Button
          variant={course.is_published ? "outline" : "default"}
          onClick={() => publish.mutate()}
        >
          <CheckCircle2 className="h-4 w-4 mr-1" />
          {course.is_published ? "Unpublish" : "Publish"}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Course content</CardTitle>
          <CardDescription>
            Modules group lessons. Lessons can link a YouTube video, point at
            an external URL, embed a PDF (uploaded or pasted), or hold a
            written article.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {(course.modules ?? []).length === 0 && (
            <div className="text-sm text-brand-brown-light italic">
              No modules yet. Add the first one below.
            </div>
          )}
          {(course.modules ?? []).map((m) => (
            <ModuleCard key={m.id} module={m} courseId={courseId} />
          ))}
          <NewModuleRow courseId={courseId} />
        </CardContent>
      </Card>
    </div>
  );
}

function NewModuleRow({ courseId }: { courseId: number }) {
  const qc = useQueryClient();
  const [title, setTitle] = useState("");

  const create = useMutation({
    mutationFn: () => lmsApi.addModule(courseId, { title }),
    onSuccess: () => {
      toast.success("Module added");
      setTitle("");
      qc.invalidateQueries({ queryKey: ["course", courseId] });
    },
    onError: () => toast.error("Could not add module"),
  });

  return (
    <div className="flex gap-2 items-end pt-3 border-t border-brand-brown-50">
      <div className="flex-1">
        <Label>New module title</Label>
        <Input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Week 1 — Getting Started"
        />
      </div>
      <Button disabled={!title || create.isPending} onClick={() => create.mutate()}>
        <Plus className="h-4 w-4 mr-1" /> Add module
      </Button>
    </div>
  );
}

function ModuleCard({
  module,
  courseId,
}: {
  module: CourseModule;
  courseId: number;
}) {
  const qc = useQueryClient();
  const [editingTitle, setEditingTitle] = useState(false);
  const [title, setTitle] = useState(module.title);

  const update = useMutation({
    mutationFn: () => lmsApi.updateModule(module.id, { title }),
    onSuccess: () => {
      toast.success("Saved");
      setEditingTitle(false);
      qc.invalidateQueries({ queryKey: ["course", courseId] });
    },
  });
  const remove = useMutation({
    mutationFn: () => lmsApi.deleteModule(module.id),
    onSuccess: () => {
      toast.success("Module removed");
      qc.invalidateQueries({ queryKey: ["course", courseId] });
    },
    onError: () => toast.error("Could not delete module"),
  });

  return (
    <div className="border border-brand-brown-50 rounded-lg p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        {editingTitle ? (
          <div className="flex gap-2 flex-1">
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <Button size="sm" onClick={() => update.mutate()}>
              Save
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setTitle(module.title);
                setEditingTitle(false);
              }}
            >
              Cancel
            </Button>
          </div>
        ) : (
          <button
            className="text-left flex-1"
            onClick={() => setEditingTitle(true)}
          >
            <div className="font-medium">{module.title}</div>
            {module.description && (
              <div className="text-xs text-brand-brown-light">
                {module.description}
              </div>
            )}
          </button>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => {
            if (confirm(`Delete module "${module.title}" and its lessons?`))
              remove.mutate();
          }}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      <div className="space-y-2">
        {(module.lessons ?? []).map((l) => (
          <LessonRow key={l.id} lesson={l} courseId={courseId} />
        ))}
        <NewLessonRow moduleId={module.id} courseId={courseId} />
      </div>
    </div>
  );
}

function LessonRow({
  lesson,
  courseId,
}: {
  lesson: Lesson;
  courseId: number;
}) {
  const qc = useQueryClient();
  const Icon = TYPE_ICON[lesson.content_type] ?? FileText;

  const remove = useMutation({
    mutationFn: () => lmsApi.deleteLesson(lesson.id),
    onSuccess: () => {
      toast.success("Lesson removed");
      qc.invalidateQueries({ queryKey: ["course", courseId] });
    },
  });

  return (
    <div className="flex items-start gap-3 p-2 rounded bg-brand-brown-50/40 border border-brand-brown-50">
      <Icon className="h-4 w-4 text-brand-gold-dark mt-0.5 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium">{lesson.title}</div>
        <div className="text-[11px] text-brand-brown-light flex flex-wrap gap-2">
          <span className="font-mono uppercase tracking-wider">
            {lesson.content_type.replace("_", " ")}
          </span>
          {lesson.content_url && (
            <a
              href={lesson.content_url}
              target="_blank"
              rel="noreferrer"
              className="underline truncate max-w-xs"
            >
              {lesson.content_url}
            </a>
          )}
          <span>· {lesson.duration_minutes} min</span>
          <span>· {lesson.points} pts</span>
        </div>
      </div>
      <Button
        size="sm"
        variant="ghost"
        onClick={() => {
          if (confirm(`Delete lesson "${lesson.title}"?`)) remove.mutate();
        }}
      >
        <Trash2 className="h-3 w-3" />
      </Button>
    </div>
  );
}

function NewLessonRow({
  moduleId,
  courseId,
}: {
  moduleId: number;
  courseId: number;
}) {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState({
    title: "",
    content_type: "video" as ContentType,
    content_url: "",
    article_body: "",
    duration_minutes: 10,
    points: 1,
  });

  const create = useMutation({
    mutationFn: () =>
      lmsApi.addLesson(moduleId, {
        title: draft.title,
        content_type: draft.content_type,
        content_url: NEEDS_URL.has(draft.content_type)
          ? draft.content_url
          : undefined,
        article_body:
          draft.content_type === "article" ? draft.article_body : undefined,
        duration_minutes: draft.duration_minutes,
        points: draft.points,
      }),
    onSuccess: () => {
      toast.success("Lesson added");
      setDraft({
        title: "",
        content_type: "video",
        content_url: "",
        article_body: "",
        duration_minutes: 10,
        points: 1,
      });
      setOpen(false);
      qc.invalidateQueries({ queryKey: ["course", courseId] });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(err?.response?.data?.detail ?? "Could not add lesson"),
  });

  const upload = useMutation({
    mutationFn: (file: File) => lmsApi.uploadAsset(file),
    onSuccess: (resp) => {
      setDraft((d) => ({ ...d, content_url: resp.url }));
      toast.success(`Uploaded ${resp.filename}`);
    },
    onError: () => toast.error("Upload failed"),
  });

  const showUrl = NEEDS_URL.has(draft.content_type);
  const showUpload = ["pdf", "image", "audio"].includes(draft.content_type);
  const showArticle = draft.content_type === "article";

  if (!open) {
    return (
      <Button
        size="sm"
        variant="outline"
        className="w-full justify-start"
        onClick={() => setOpen(true)}
      >
        <Plus className="h-3 w-3 mr-1" /> Add lesson
      </Button>
    );
  }

  return (
    <div className="border border-brand-gold-dark/40 rounded-lg p-3 bg-brand-gold/5 space-y-3">
      <div className="grid sm:grid-cols-2 gap-2">
        <div className="sm:col-span-2">
          <Label>Title</Label>
          <Input
            value={draft.title}
            onChange={(e) => setDraft({ ...draft, title: e.target.value })}
            placeholder="e.g. Welcome video"
          />
        </div>
        <div>
          <Label>Content type</Label>
          <select
            value={draft.content_type}
            onChange={(e) =>
              setDraft({
                ...draft,
                content_type: e.target.value as ContentType,
              })
            }
            className="w-full h-10 px-3 rounded border border-brand-brown-50 bg-card text-sm"
          >
            {CONTENT_TYPES.map((t) => (
              <option key={t} value={t}>
                {t.replace("_", " ")}
              </option>
            ))}
          </select>
        </div>
        <div>
          <Label>Duration (min)</Label>
          <Input
            type="number"
            min={1}
            max={480}
            value={draft.duration_minutes}
            onChange={(e) =>
              setDraft({ ...draft, duration_minutes: Number(e.target.value) })
            }
          />
        </div>
      </div>

      {showUrl && (
        <div>
          <Label>
            {draft.content_type === "video"
              ? "Video URL (YouTube / Vimeo / direct)"
              : draft.content_type === "pdf"
              ? "PDF URL (or upload below)"
              : draft.content_type === "external_link"
              ? "External URL"
              : "Asset URL"}
          </Label>
          <Input
            value={draft.content_url}
            onChange={(e) =>
              setDraft({ ...draft, content_url: e.target.value })
            }
            placeholder="https://…"
          />
          {showUpload && (
            <div className="mt-2 flex items-center gap-2 flex-wrap">
              <input
                type="file"
                hidden
                ref={fileRef}
                accept={
                  draft.content_type === "pdf"
                    ? "application/pdf"
                    : draft.content_type === "image"
                    ? "image/*"
                    : draft.content_type === "audio"
                    ? "audio/*"
                    : undefined
                }
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) upload.mutate(f);
                  e.target.value = "";
                }}
              />
              <Button
                size="sm"
                variant="outline"
                disabled={upload.isPending}
                onClick={() => fileRef.current?.click()}
              >
                <Upload className="h-3 w-3 mr-1" />
                {upload.isPending ? "Uploading…" : "Upload file"}
              </Button>
              <span className="text-xs text-brand-brown-light">
                Up to 25 MB. The URL above auto-fills on success.
              </span>
            </div>
          )}
        </div>
      )}

      {showArticle && (
        <div>
          <Label>Article body</Label>
          <textarea
            rows={5}
            className="w-full border border-brand-brown-50 rounded p-2 text-sm bg-card"
            value={draft.article_body}
            onChange={(e) =>
              setDraft({ ...draft, article_body: e.target.value })
            }
            placeholder="Markdown / plain text"
          />
        </div>
      )}

      <div className="flex justify-end gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setOpen(false)}
        >
          Cancel
        </Button>
        <Button
          size="sm"
          disabled={
            !draft.title ||
            (showUrl && !draft.content_url) ||
            (showArticle && !draft.article_body) ||
            create.isPending
          }
          onClick={() => create.mutate()}
        >
          Add lesson
        </Button>
      </div>
    </div>
  );
}
