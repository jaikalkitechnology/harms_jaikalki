import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Clock, Award, CheckCircle2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { examApi } from "@/lib/api/exam";

const TYPE_COLOR: Record<string, string> = {
  practice: "bg-info/15 text-info",
  assessment: "bg-warning/15 text-warning",
  certification: "bg-brand-gold/15 text-brand-gold-dark",
  mandatory: "bg-error/15 text-error",
};

export default function ExamsPage() {
  const qc = useQueryClient();
  const { data: exams = [], isLoading } = useQuery({
    queryKey: ["exams"],
    queryFn: examApi.listExams,
  });

  const publish = useMutation({
    mutationFn: ({ id, on }: { id: number; on: boolean }) =>
      examApi.publish(id, on),
    onSuccess: () => {
      toast.success("Updated");
      qc.invalidateQueries({ queryKey: ["exams"] });
    },
    onError: () => toast.error("Could not update"),
  });

  if (isLoading) return <LoadingScreen label="Loading exams…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Examinations
        </h1>
        <p className="text-sm text-brand-brown-light">
          {exams.length} exam{exams.length === 1 ? "" : "s"} configured.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {exams.length === 0 ? (
          <Card className="md:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-brand-brown-light">
              No exams configured.
            </CardContent>
          </Card>
        ) : (
          exams.map((e) => (
            <Card key={e.id} className="flex flex-col">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base">{e.title}</CardTitle>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${TYPE_COLOR[e.exam_type] ?? ""}`}
                  >
                    {e.exam_type}
                  </span>
                </div>
                <CardDescription className="font-mono text-xs">
                  {e.code}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1 space-y-2 text-sm">
                {e.description && (
                  <p className="text-brand-brown-light">{e.description}</p>
                )}
                <div className="flex gap-3 flex-wrap">
                  <span className="inline-flex items-center gap-1 text-xs">
                    <Clock className="size-3" />
                    {e.time_limit_minutes} min
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs">
                    <Award className="size-3" />
                    Pass {e.passing_percentage}%
                  </span>
                  <span className="text-xs">
                    {e.total_questions} Qs · {e.attempts_allowed} attempts
                  </span>
                </div>
                <div className="pt-2">
                  {e.is_published ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1"
                      onClick={() => publish.mutate({ id: e.id, on: false })}
                    >
                      <CheckCircle2 className="size-4 text-success" />
                      Published — unpublish
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      onClick={() => publish.mutate({ id: e.id, on: true })}
                    >
                      Publish
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
