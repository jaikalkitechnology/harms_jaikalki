import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { GraduationCap, BookOpen, Award } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { lmsApi, type CourseSummary } from "@/lib/api/lms";

const CATEGORY_COLOR: Record<string, string> = {
  onboarding: "bg-info/15 text-info",
  compliance: "bg-error/15 text-error",
  technical: "bg-brand-gold/15 text-brand-gold-dark",
  leadership: "bg-warning/15 text-warning",
  soft_skills: "bg-success/15 text-success",
  product: "bg-info/25 text-info",
  other: "bg-brand-brown-50 text-brand-brown-darker",
};

export default function CoursesPage() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState("");
  const { data: courses = [], isLoading } = useQuery({
    queryKey: ["lms-courses", filter],
    queryFn: () =>
      lmsApi.listCourses(filter ? { category: filter } : undefined),
  });

  const publish = useMutation({
    mutationFn: (id: number) => lmsApi.publish(id, true),
    onSuccess: () => {
      toast.success("Published");
      qc.invalidateQueries({ queryKey: ["lms-courses"] });
    },
    onError: () => toast.error("Could not publish"),
  });

  if (isLoading) return <LoadingScreen label="Loading courses…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Course Catalog
          </h1>
          <p className="text-sm text-brand-brown-light">
            {courses.length} published course{courses.length === 1 ? "" : "s"}
          </p>
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All categories</option>
          <option value="onboarding">Onboarding</option>
          <option value="compliance">Compliance</option>
          <option value="technical">Technical</option>
          <option value="leadership">Leadership</option>
          <option value="soft_skills">Soft skills</option>
          <option value="product">Product</option>
        </select>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {courses.length === 0 ? (
          <Card className="md:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-brand-brown-light">
              <BookOpen className="mx-auto mb-3 size-10 text-brand-gold-dark" />
              No courses yet. HR can create one via the API.
            </CardContent>
          </Card>
        ) : (
          courses.map((c) => (
            <CourseCard
              key={c.id}
              course={c}
              onPublish={() => publish.mutate(c.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

function CourseCard({
  course,
  onPublish,
}: {
  course: CourseSummary;
  onPublish: () => void;
}) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base">{course.title}</CardTitle>
          {course.is_mandatory && (
            <span className="rounded-full bg-error/15 px-2 py-0.5 text-[10px] uppercase text-error">
              Mandatory
            </span>
          )}
        </div>
        <CardDescription className="font-mono text-xs">
          {course.code} · {course.estimated_hours}h · {course.difficulty}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 flex-1 flex flex-col">
        <div>
          <span
            className={`rounded-full px-2 py-0.5 text-xs ${CATEGORY_COLOR[course.category] ?? ""}`}
          >
            {course.category.replace("_", " ")}
          </span>
        </div>
        {course.description && (
          <p className="text-sm text-brand-brown-light flex-1">
            {course.description}
          </p>
        )}
        <div className="flex items-center justify-between text-sm">
          <span className="inline-flex items-center gap-1 text-brand-gold-dark">
            <Award className="size-4" />
            {course.points} pts
          </span>
          <Button size="sm" variant="outline" onClick={onPublish}>
            <GraduationCap className="size-4 mr-1" />
            View
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
