import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Star, Plus, Briefcase } from "lucide-react";

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
import { employeesApi } from "@/lib/api/employees";

export default function TrainersPage() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [employeeId, setEmployeeId] = useState<number | "">("");
  const [isExternal, setIsExternal] = useState(false);
  const [fullName, setFullName] = useState("");
  const [headline, setHeadline] = useState("");
  const [bio, setBio] = useState("");
  const [specializations, setSpecializations] = useState("");
  const [yearsExp, setYearsExp] = useState("0");
  const [contactEmail, setContactEmail] = useState("");

  const { data: trainers = [], isLoading } = useQuery({
    queryKey: ["trainers", search],
    queryFn: () =>
      trainerApi.listTrainers(search ? { search } : undefined),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });

  const create = useMutation({
    mutationFn: () =>
      trainerApi.createTrainer({
        employee_id: employeeId || null,
        is_external: isExternal,
        full_name: fullName,
        headline: headline || null,
        bio: bio || null,
        contact_email: contactEmail || null,
        years_experience: Number(yearsExp),
        specializations: specializations
          ? specializations.split(",").map((s) => s.trim()).filter(Boolean)
          : [],
      }),
    onSuccess: () => {
      toast.success("Trainer added");
      setShowForm(false);
      setFullName("");
      setHeadline("");
      setBio("");
      setSpecializations("");
      setEmployeeId("");
      qc.invalidateQueries({ queryKey: ["trainers"] });
    },
    onError: (e: { response?: { data?: { detail?: string } } }) =>
      toast.error(e.response?.data?.detail ?? "Could not add"),
  });

  if (isLoading) return <LoadingScreen label="Loading trainers…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Trainer Marketplace
          </h1>
          <p className="text-sm text-brand-brown-light">
            Internal & external trainers · {trainers.length} active.
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)} className="gap-2">
          <Plus className="size-4" />
          {showForm ? "Cancel" : "Add trainer"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Add trainer</CardTitle>
            <CardDescription>
              Internal trainers must be linked to an existing employee.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2 flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                id="external"
                checked={isExternal}
                onChange={(e) => setIsExternal(e.target.checked)}
              />
              <Label htmlFor="external">External trainer</Label>
            </div>
            {!isExternal && (
              <div className="md:col-span-2">
                <Label>Employee *</Label>
                <select
                  value={employeeId}
                  onChange={(e) =>
                    setEmployeeId(
                      e.target.value ? Number(e.target.value) : "",
                    )
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
            )}
            <div>
              <Label>Full name *</Label>
              <Input
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
              />
            </div>
            <div>
              <Label>Headline</Label>
              <Input
                value={headline}
                onChange={(e) => setHeadline(e.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Label>Bio</Label>
              <Input value={bio} onChange={(e) => setBio(e.target.value)} />
            </div>
            <div>
              <Label>Years experience</Label>
              <Input
                type="number"
                value={yearsExp}
                onChange={(e) => setYearsExp(e.target.value)}
              />
            </div>
            <div>
              <Label>Contact email</Label>
              <Input
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Label>Specializations (comma-separated)</Label>
              <Input
                value={specializations}
                onChange={(e) => setSpecializations(e.target.value)}
                placeholder="POSH, Onboarding, Leadership"
              />
            </div>
            <div className="md:col-span-2 flex justify-end">
              <Button
                disabled={!fullName || create.isPending}
                onClick={() => create.mutate()}
              >
                Save
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Input
        placeholder="Search by name…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm"
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {trainers.length === 0 ? (
          <Card className="md:col-span-2 xl:col-span-3">
            <CardContent className="py-10 text-center text-brand-brown-light">
              No trainers yet.
            </CardContent>
          </Card>
        ) : (
          trainers.map((t) => (
            <Card key={t.id}>
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base">{t.full_name}</CardTitle>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] uppercase ${
                      t.is_external
                        ? "bg-info/15 text-info"
                        : "bg-brand-gold/15 text-brand-gold-dark"
                    }`}
                  >
                    {t.is_external ? "External" : "Internal"}
                  </span>
                </div>
                {t.headline && (
                  <CardDescription>{t.headline}</CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex items-center gap-3 text-xs">
                  <span className="inline-flex items-center gap-1 text-brand-gold-dark">
                    <Star className="size-3 fill-current" />
                    {Number(t.rating_average).toFixed(1)}
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <Briefcase className="size-3" />
                    {t.sessions_completed} sessions
                  </span>
                  <span>{t.years_experience}y exp</span>
                </div>
                {t.specializations && t.specializations.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {t.specializations.map((s) => (
                      <span
                        key={s}
                        className="rounded bg-brand-brown-50 px-2 py-0.5 text-[10px]"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
