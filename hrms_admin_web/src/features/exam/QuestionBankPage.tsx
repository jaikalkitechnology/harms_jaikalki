import { useQuery } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { examApi } from "@/lib/api/exam";

const DIFFICULTY_COLOR: Record<string, string> = {
  easy: "bg-success/15 text-success",
  medium: "bg-warning/15 text-warning",
  hard: "bg-error/15 text-error",
};

export default function QuestionBankPage() {
  const { data: questions = [], isLoading } = useQuery({
    queryKey: ["exam-questions"],
    queryFn: examApi.listQuestions,
  });

  if (isLoading) return <LoadingScreen label="Loading question bank…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Question Bank
        </h1>
        <p className="text-sm text-brand-brown-light">
          {questions.length} active question{questions.length === 1 ? "" : "s"} ·
          Manage MCQs powering certification exams.
        </p>
      </div>

      {questions.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-brand-brown-light">
            No questions yet. Add via API.
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {questions.map((q) => (
            <Card key={q.id}>
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <CardTitle className="text-base">
                    {q.question_text}
                  </CardTitle>
                  <span
                    className={`rounded-full px-2 py-1 text-xs ${DIFFICULTY_COLOR[q.difficulty] ?? ""}`}
                  >
                    {q.difficulty}
                  </span>
                </div>
                <CardDescription>
                  {q.question_type.replace("_", " ")} · {q.topic ?? "no topic"} ·
                  {" "}
                  {q.marks} marks · {q.time_seconds}s
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {q.options.map((o) => (
                    <li
                      key={o.id}
                      className={`flex items-start gap-2 text-sm ${o.is_correct ? "font-semibold text-success" : ""}`}
                    >
                      {o.is_correct ? (
                        <CheckCircle2 className="size-4 mt-0.5 flex-shrink-0" />
                      ) : (
                        <span className="size-4 mt-0.5 flex-shrink-0" />
                      )}
                      {o.option_text}
                    </li>
                  ))}
                </ul>
                {q.explanation && (
                  <p className="mt-3 text-xs italic text-brand-brown-light">
                    {q.explanation}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
