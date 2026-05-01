import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  AlertTriangle,
  CheckCircle2,
  MessageSquare,
  Star,
  Sun,
  Sunset,
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
import { dwpApi, type DwpTeamItem } from "@/lib/api/dwp";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export default function DwpTeamPage() {
  const [date, setDate] = useState(todayISO());

  const { data: today = [], isLoading: loadingToday } = useQuery({
    queryKey: ["dwp-team-today", date],
    queryFn: () => dwpApi.teamToday(date),
  });
  const { data: blockers = [] } = useQuery({
    queryKey: ["dwp-team-blockers", date],
    queryFn: () => dwpApi.teamBlockers(date),
  });

  if (loadingToday) return <LoadingScreen label="Loading DWP…" />;

  const morning = today.filter((i) => i.submission.type === "morning");
  const eod = today.filter((i) => i.submission.type === "eod");

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
            ★ Phase 6 · Daily Work Planning
          </div>
          <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
            Team <span className="display-em">DWP</span>
          </h2>
          <p className="mt-1 text-sm text-brand-brown-light">
            {today.length} submissions today · {blockers.length} blocker
            {blockers.length === 1 ? "" : "s"}
          </p>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="date">Date</Label>
          <Input
            id="date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-44"
          />
        </div>
      </div>

      {blockers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-warning" />
              Blockers
            </CardTitle>
            <CardDescription>
              EOD submissions where someone flagged a blocker.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {blockers.map((b) => (
              <BlockerRow key={b.submission.id} item={b} />
            ))}
          </CardContent>
        </Card>
      )}

      <div className="grid lg:grid-cols-2 gap-4">
        <Section
          icon={<Sun className="h-5 w-5 text-brand-gold-dark" />}
          title="Morning plans"
          items={morning}
          emptyText="No morning DWPs submitted yet."
        />
        <Section
          icon={<Sunset className="h-5 w-5 text-brand-brown-light" />}
          title="EOD summaries"
          items={eod}
          emptyText="No EOD summaries yet."
        />
      </div>
    </div>
  );
}

function Section({
  icon,
  title,
  items,
  emptyText,
}: {
  icon: React.ReactNode;
  title: string;
  items: DwpTeamItem[];
  emptyText: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
        <CardDescription>
          {items.length} submission{items.length === 1 ? "" : "s"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-brand-brown-light">{emptyText}</p>
        ) : (
          items.map((i) => <SubmissionCard key={i.submission.id} item={i} />)
        )}
      </CardContent>
    </Card>
  );
}

function SubmissionCard({ item }: { item: DwpTeamItem }) {
  const fields = Object.fromEntries(
    item.submission.fields.map((f) => [f.field_key, f.value]),
  );
  return (
    <div className="rounded-xl border border-brand-brown-100 p-4 space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-medium">{item.employee_full_name}</div>
          <div className="text-xs font-mono text-brand-brown-light">
            {item.employee_code}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {item.submission.total_hours && (
            <span className="text-xs text-brand-brown-light">
              {item.submission.total_hours}h
            </span>
          )}
          {item.submission.mood_rating && (
            <span className="flex items-center gap-1 text-xs text-brand-gold-dark">
              <Star className="h-3 w-3 fill-current" />
              {item.submission.mood_rating}
            </span>
          )}
        </div>
      </div>
      {fields.tasks && (
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
            Tasks
          </div>
          <p className="text-sm whitespace-pre-line">{String(fields.tasks)}</p>
        </div>
      )}
      {fields.blockers && String(fields.blockers).trim() && (
        <div className="rounded-lg bg-warning/10 p-2.5">
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-warning">
            ⚠ Blocker
          </div>
          <p className="text-sm">{String(fields.blockers)}</p>
        </div>
      )}
      {fields.tomorrow_plan && (
        <div>
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
            Tomorrow
          </div>
          <p className="text-sm whitespace-pre-line">
            {String(fields.tomorrow_plan)}
          </p>
        </div>
      )}
      <CommentRow submissionId={item.submission.id} />
      {item.submission.comments.length > 0 && (
        <div className="space-y-1 pt-2 border-t border-brand-brown-100/60">
          {item.submission.comments.map((c) => (
            <div
              key={c.id}
              className="text-sm flex items-start gap-2"
            >
              {c.is_kudos ? (
                <Star className="h-4 w-4 text-brand-gold-dark mt-0.5" />
              ) : (
                <MessageSquare className="h-4 w-4 text-brand-brown-light mt-0.5" />
              )}
              <span>{c.comment}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function BlockerRow({ item }: { item: DwpTeamItem }) {
  const blocker =
    item.submission.fields.find((f) => f.field_key === "blockers")?.value ?? "";
  return (
    <div className="flex items-start justify-between gap-3 py-2 border-b border-brand-brown-100/60 last:border-0">
      <div className="min-w-0">
        <div className="font-medium text-sm">{item.employee_full_name}</div>
        <p className="text-sm text-brand-brown-darker">{blocker}</p>
      </div>
      <span className="text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded bg-warning/15 text-warning shrink-0">
        Blocker
      </span>
    </div>
  );
}

function CommentRow({ submissionId }: { submissionId: number }) {
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();

  const post = useMutation({
    mutationFn: ({ kudos }: { kudos: boolean }) =>
      dwpApi.addComment(submissionId, text, kudos),
    onSuccess: () => {
      toast.success("Comment posted");
      setText("");
      setOpen(false);
      queryClient.invalidateQueries({ queryKey: ["dwp-team-today"] });
    },
    onError: () => toast.error("Could not post comment"),
  });

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="text-xs font-mono uppercase tracking-[0.2em] text-brand-brown-light hover:text-brand-brown-darker"
      >
        + Add comment
      </button>
    );
  }
  return (
    <div className="flex gap-2">
      <Input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Comment or kudos…"
        className="flex-1"
      />
      <Button
        size="sm"
        variant="gold"
        onClick={() => text && post.mutate({ kudos: true })}
      >
        <Star className="h-4 w-4" />
      </Button>
      <Button
        size="sm"
        variant="outline"
        onClick={() => text && post.mutate({ kudos: false })}
      >
        <CheckCircle2 className="h-4 w-4" />
      </Button>
    </div>
  );
}
