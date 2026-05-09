import { forwardRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";

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
import { Spinner } from "@/components/shared/LoadingScreen";
import {
  employeesApi,
  lookupsApi,
  salaryTemplatesApi,
  type CreateEmployeePayload,
} from "@/lib/api/employees";

// Helpers — `<select>` and `<input type="number">` hand react-hook-form
// strings ("") or sometimes undefined when the field is empty. If we
// pipe those straight into `z.coerce.number()` we get NaN which fails
// validation with "Expected number, received nan" even on optional
// fields. Preprocess: anything blank → null *before* coercion. We also
// guard against literal "NaN" / actual NaN so a stale form state can't
// re-trip the validator.
function _blank(v: unknown): boolean {
  if (v === "" || v === null || v === undefined) return true;
  if (typeof v === "number" && Number.isNaN(v)) return true;
  if (typeof v === "string" && v.trim() === "") return true;
  return false;
}
const blankToNull = (v: unknown) => (_blank(v) ? null : v);

const optionalPositiveIntFk = z.preprocess(
  blankToNull,
  z.coerce.number().int().positive().nullable(),
);
const optionalNonNegativeNumber = z.preprocess(
  blankToNull,
  z.coerce.number().nonnegative().nullable(),
);

// `category_id` is required, but if the user submits before picking
// one we want a friendly "Choose a category" error — not Zod's default
// "Expected number, received nan". Preprocess blanks → 0 so the
// `.positive()` rule fires the right message.
const requiredPositiveIntFk = z.preprocess(
  (v) => (_blank(v) ? 0 : v),
  z.coerce.number().int().positive("Choose a category"),
);

const schema = z
  .object({
    first_name: z.string().min(1, "Required"),
    last_name: z.string().min(1, "Required"),
    category_id: requiredPositiveIntFk,
    designation_id: optionalPositiveIntFk,
    department_id: optionalPositiveIntFk,
    salary_template_id: optionalPositiveIntFk,
    ctc_annual: optionalNonNegativeNumber,
    date_of_joining: z.string().min(1, "Required"),
    personal_email: z.string().email().optional().or(z.literal("")),
    personal_phone: z.string().optional(),
    create_user_account: z.boolean().default(false),
    user_email: z.string().email().optional().or(z.literal("")),
  })
  .refine(
    (v) => !v.create_user_account || (v.user_email && v.user_email.length > 0),
    { message: "user_email is required when creating a user account", path: ["user_email"] },
  );

type FormValues = z.infer<typeof schema>;

export default function EmployeeCreatePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [submitting, setSubmitting] = useState(false);

  const { data: categories = [] } = useQuery({
    queryKey: ["categories"],
    queryFn: lookupsApi.categories,
  });
  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: lookupsApi.departments,
  });
  const { data: designations = [] } = useQuery({
    queryKey: ["designations"],
    queryFn: lookupsApi.designations,
  });
  const { data: templates = [] } = useQuery({
    queryKey: ["salary-templates"],
    queryFn: () => salaryTemplatesApi.list(),
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    // Note: empty strings (not 0/null) for the select-backed numeric
    // fields so the rendered <option value=""> placeholder stays
    // selected. RHF then captures the user's real pick on change. The
    // schema's preprocess turns "" → 0/null at validation time.
    defaultValues: {
      first_name: "",
      last_name: "",
      category_id: "" as unknown as number,
      designation_id: "" as unknown as number,
      department_id: "" as unknown as number,
      salary_template_id: "" as unknown as number,
      ctc_annual: "" as unknown as number,
      date_of_joining: new Date().toISOString().slice(0, 10),
      personal_email: "",
      personal_phone: "",
      create_user_account: false,
      user_email: "",
    },
  });

  const categoryId = form.watch("category_id");
  const selectedCategory = categories.find((c) => c.id === Number(categoryId));
  const isIntern = selectedCategory?.code === "INTERN";

  const filteredTemplates = templates.filter((t) =>
    isIntern ? t.category === "intern" : t.category !== "intern",
  );

  const create = useMutation({
    mutationFn: (payload: CreateEmployeePayload) => employeesApi.create(payload),
    onSuccess: (emp) => {
      queryClient.invalidateQueries({ queryKey: ["employees"] });
      toast.success(`Created ${emp.employee_code}`);
      navigate(`/employees/${emp.id}`);
    },
    onError: (err: unknown) => {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Failed to create employee";
      toast.error(detail);
    },
  });

  async function onSubmit(values: FormValues) {
    setSubmitting(true);
    const payload: CreateEmployeePayload = {
      first_name: values.first_name,
      last_name: values.last_name,
      category_id: values.category_id,
      designation_id: values.designation_id || null,
      department_id: values.department_id || null,
      salary_template_id: values.salary_template_id || null,
      ctc_annual: isIntern ? null : values.ctc_annual,
      date_of_joining: values.date_of_joining,
      personal_email: values.personal_email || null,
      personal_phone: values.personal_phone || null,
      create_user_account: values.create_user_account,
      user_email: values.user_email || null,
    };
    try {
      await create.mutateAsync(payload);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <button
        onClick={() => navigate("/employees")}
        className="flex items-center gap-2 text-sm text-brand-brown-light hover:text-brand-brown-darker"
      >
        <ArrowLeft className="h-4 w-4" /> Back to directory
      </button>

      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ New employee
        </div>
        <h1 className="font-display text-3xl font-bold text-brand-brown-darker">
          Add an <span className="display-em">employee</span>
        </h1>
        <p className="mt-1 text-sm text-brand-brown-light">
          Employee code is auto-generated (next in the {"{prefix}"}### sequence).
          KYC, marksheets and bank documents can be uploaded on the
          employee profile page right after this step.
        </p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Personal</CardTitle>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4">
            <Field label="First name" error={form.formState.errors.first_name?.message}>
              <Input {...form.register("first_name")} />
            </Field>
            <Field label="Last name" error={form.formState.errors.last_name?.message}>
              <Input {...form.register("last_name")} />
            </Field>
            <Field label="Personal email">
              <Input type="email" {...form.register("personal_email")} />
            </Field>
            <Field label="Personal phone">
              <Input {...form.register("personal_phone")} />
            </Field>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Employment</CardTitle>
            <CardDescription>
              Pick a category first — interns receive only travel reimbursement.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4">
            <Field label="Category" error={form.formState.errors.category_id?.message}>
              <Select {...form.register("category_id")}>
                <option value="">Select…</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Date of joining" error={form.formState.errors.date_of_joining?.message}>
              <Input type="date" {...form.register("date_of_joining")} />
            </Field>
            <Field label="Department">
              <Select {...form.register("department_id")}>
                <option value="">—</option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Designation">
              <Select {...form.register("designation_id")}>
                <option value="">—</option>
                {designations.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} (L{d.level})
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Salary template">
              <Select {...form.register("salary_template_id")}>
                <option value="">—</option>
                {filteredTemplates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.template_code} · {t.template_name}
                  </option>
                ))}
              </Select>
            </Field>
            {!isIntern && (
              <Field label="CTC (annual ₹)">
                <Input type="number" min={0} {...form.register("ctc_annual")} />
              </Field>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Login account (optional)</CardTitle>
            <CardDescription>
              Create a user record so this employee can sign in to the mobile
              app. Default password is <code>changeme123</code>.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="accent-brand-gold-dark"
                {...form.register("create_user_account")}
              />
              Also create a login account
            </label>
            {form.watch("create_user_account") && (
              <Field label="Login email" error={form.formState.errors.user_email?.message}>
                <Input type="email" {...form.register("user_email")} />
              </Field>
            )}
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Button type="submit" disabled={submitting}>
            {submitting ? <Spinner /> : "Create employee"}
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate(-1)}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  );
}

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-xs text-error">{error}</p>}
    </div>
  );
}

const Select = forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(({ className = "", ...props }, ref) => (
  <select
    {...props}
    ref={ref}
    className={`flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${className}`}
  />
));
Select.displayName = "Select";
