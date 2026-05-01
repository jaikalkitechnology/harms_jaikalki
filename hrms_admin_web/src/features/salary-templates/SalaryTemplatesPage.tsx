import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import {
  salaryTemplatesApi,
  type SalaryTemplate,
} from "@/lib/api/employees";
import { CategoryBadge } from "@/features/employees/CategoryBadge";

export default function SalaryTemplatesPage() {
  const [selected, setSelected] = useState<SalaryTemplate | null>(null);
  const [ctcOverride, setCtcOverride] = useState<string>("");

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["salary-templates"],
    queryFn: () => salaryTemplatesApi.list(),
  });

  useEffect(() => {
    if (!selected && templates.length > 0) {
      setSelected(templates.find((t) => t.template_code === "JKT-TRAINEE-L1") ?? templates[0]);
    }
  }, [templates, selected]);

  const ctcParam =
    ctcOverride && Number(ctcOverride) > 0 ? Number(ctcOverride) : undefined;

  const { data: breakup } = useQuery({
    queryKey: ["salary-breakup", selected?.id, ctcParam],
    queryFn: () => salaryTemplatesApi.calculate(selected!.id, ctcParam),
    enabled: !!selected,
  });

  if (isLoading) return <LoadingScreen label="Loading templates…" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Phase 2 · Salary Templates
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          Jaikalki <span className="display-em">salary library</span>
        </h2>
        <p className="mt-1 text-sm text-brand-brown-light">
          {templates.length} templates · click one to preview its breakup
          (matches Pooja Kumawat's offer letter exactly).
        </p>
      </div>

      <div className="grid lg:grid-cols-[20rem_1fr] gap-4">
        <div className="space-y-2">
          {templates.map((t) => (
            <button
              key={t.id}
              onClick={() => setSelected(t)}
              className={`w-full text-left p-4 rounded-xl border transition-colors ${
                selected?.id === t.id
                  ? "bg-brand-gold/10 border-brand-gold/40"
                  : "bg-card border-brand-brown-100 hover:border-brand-gold/30"
              }`}
            >
              <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-brand-brown-light">
                {t.template_code}
              </div>
              <div className="font-medium text-brand-brown-darker">
                {t.template_name}
              </div>
              <div className="mt-2 flex items-center gap-2">
                <CategoryBadge code={t.category.toUpperCase()} />
                <span className="text-[10px] text-brand-brown-light">
                  L{t.designation_level}
                </span>
              </div>
            </button>
          ))}
        </div>

        {selected && breakup && (
          <Card>
            <CardHeader className="flex flex-row items-start justify-between gap-4">
              <div>
                <CardTitle>{breakup.template_name}</CardTitle>
                <CardDescription>
                  {breakup.template_code} · {breakup.category}
                </CardDescription>
              </div>
              <div className="flex items-end gap-2">
                <div>
                  <Label htmlFor="ctc">CTC override (₹/yr)</Label>
                  <Input
                    id="ctc"
                    type="number"
                    placeholder={String(selected.ctc_annual_default)}
                    value={ctcOverride}
                    onChange={(e) => setCtcOverride(e.target.value)}
                    className="w-40"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {breakup.is_intern ? (
                <div className="space-y-2">
                  <p className="text-sm">
                    <strong>Intern</strong> — receives travel expense
                    reimbursement only, capped at{" "}
                    <strong>
                      ₹{breakup.travel_expense_max.toLocaleString()}
                    </strong>{" "}
                    per month. No salary, PF, or ESIC.
                  </p>
                  {breakup.notes.map((n, i) => (
                    <p key={i} className="text-xs text-brand-brown-light">
                      {n}
                    </p>
                  ))}
                </div>
              ) : (
                <div className="grid md:grid-cols-3 gap-6 text-sm">
                  <BreakupColumn
                    title="Earnings (monthly)"
                    rows={[
                      ["Basic", breakup.basic],
                      ["HRA", breakup.hra],
                      ["Other Allowance", breakup.other_allowance],
                      ["Special Allowance", breakup.special_allowance],
                      ["Conveyance", breakup.conveyance],
                      ["Medical Allowance", breakup.medical_allowance],
                      ["LTA", breakup.lta],
                      ["Food Coupon", breakup.food_coupon],
                    ]}
                    total={["Gross", breakup.gross]}
                  />
                  <BreakupColumn
                    title="Deductions"
                    rows={[
                      ["PF (Employee)", breakup.pf_employee],
                      ["ESIC (Employee)", breakup.esic_employee],
                      ["Professional Tax", breakup.professional_tax],
                    ]}
                    total={["Total", breakup.total_deductions]}
                    after={["Net Salary", breakup.net_salary]}
                  />
                  <BreakupColumn
                    title="Employer cost"
                    rows={[
                      ["PF (Employer)", breakup.pf_employer],
                      ["ESIC (Employer)", breakup.esic_employer],
                    ]}
                    total={["CTC / month", breakup.total_ctc_monthly]}
                    after={["CTC / year", breakup.total_ctc_annual]}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function BreakupColumn({
  title,
  rows,
  total,
  after,
}: {
  title: string;
  rows: [string, number][];
  total: [string, number];
  after?: [string, number];
}) {
  const inr = (n: number) => `₹${n.toLocaleString("en-IN")}`;
  const visibleRows = rows.filter(([, v]) => v > 0);
  return (
    <div>
      <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-2">
        {title}
      </div>
      <dl className="space-y-1.5">
        {visibleRows.map(([k, v]) => (
          <div key={k} className="flex justify-between">
            <dt className="text-brand-brown-light">{k}</dt>
            <dd className="font-medium">{inr(v)}</dd>
          </div>
        ))}
        <div className="flex justify-between pt-2 border-t border-brand-brown-100 font-semibold">
          <dt>{total[0]}</dt>
          <dd>{inr(total[1])}</dd>
        </div>
        {after && (
          <div className="flex justify-between pt-2 border-t border-brand-brown-100 text-brand-gold-dark font-semibold">
            <dt>{after[0]}</dt>
            <dd>{inr(after[1])}</dd>
          </div>
        )}
      </dl>
    </div>
  );
}
