import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ArrowRight } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { salesApi, type Lead } from "@/lib/api/sales";

const STAGES: Lead["stage"][] = [
  "new",
  "contacted",
  "qualified",
  "proposal",
  "negotiation",
  "won",
  "lost",
];

const STAGE_COLOR: Record<Lead["stage"], string> = {
  new: "bg-info/15 text-info",
  contacted: "bg-brand-gold/15 text-brand-gold-dark",
  qualified: "bg-brand-gold/25 text-brand-gold-dark",
  proposal: "bg-warning/15 text-warning",
  negotiation: "bg-warning/25 text-warning",
  won: "bg-success/15 text-success",
  lost: "bg-error/15 text-error",
};

function nextStage(current: Lead["stage"]): Lead["stage"] | null {
  const idx = STAGES.indexOf(current);
  if (idx < 0 || idx >= STAGES.length - 2) return null;
  // Skip won/lost — those are explicit end states
  return STAGES[idx + 1];
}

export default function PipelinePage() {
  const qc = useQueryClient();
  const { data: columns = [], isLoading } = useQuery({
    queryKey: ["sales-pipeline"],
    queryFn: () => salesApi.pipeline(false),
  });

  const advance = useMutation({
    mutationFn: ({ leadId, stage }: { leadId: number; stage: string }) =>
      salesApi.updateStage(leadId, stage),
    onSuccess: () => {
      toast.success("Stage updated");
      qc.invalidateQueries({ queryKey: ["sales-pipeline"] });
      qc.invalidateQueries({ queryKey: ["sales-leads"] });
    },
    onError: () => toast.error("Could not update stage"),
  });

  const totals = useMemo(
    () =>
      columns.reduce(
        (acc, c) => {
          acc.value += Number(c.total_value);
          acc.count += c.count;
          return acc;
        },
        { value: 0, count: 0 },
      ),
    [columns],
  );

  if (isLoading) return <LoadingScreen label="Loading pipeline…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Sales Pipeline
          </h1>
          <p className="text-sm text-brand-brown-light">
            {totals.count} leads · ₹{totals.value.toLocaleString("en-IN")} in flight
          </p>
        </div>
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 xl:grid-cols-7">
        {columns.map((col) => (
          <Card key={col.stage} className="flex flex-col">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm uppercase tracking-wide flex items-center justify-between">
                <span className={`rounded-full px-2 py-0.5 text-xs ${STAGE_COLOR[col.stage]}`}>
                  {col.stage}
                </span>
                <span className="text-brand-brown-light">{col.count}</span>
              </CardTitle>
              <CardDescription className="text-xs">
                ₹{Number(col.total_value).toLocaleString("en-IN")}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 flex-1">
              {col.leads.length === 0 ? (
                <p className="text-xs text-brand-brown-light italic">
                  No leads here.
                </p>
              ) : (
                col.leads.map((ld) => {
                  const next = nextStage(ld.stage);
                  return (
                    <div
                      key={ld.id}
                      className="rounded-md border border-brand-brown-50 bg-cream p-2 text-xs"
                    >
                      <div className="font-medium">
                        {ld.contact_name ?? `Lead #${ld.id}`}
                      </div>
                      {ld.contact_phone && (
                        <div className="text-brand-brown-light">
                          {ld.contact_phone}
                        </div>
                      )}
                      <div className="mt-1 text-brand-brown-darker">
                        ₹{Number(ld.expected_value).toLocaleString("en-IN")}
                      </div>
                      {ld.next_action && (
                        <div className="mt-1 text-brand-brown-light italic">
                          → {ld.next_action}
                        </div>
                      )}
                      {next && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="mt-2 h-7 px-2 text-xs"
                          disabled={advance.isPending}
                          onClick={() =>
                            advance.mutate({ leadId: ld.id, stage: next })
                          }
                        >
                          Advance to {next}
                          <ArrowRight className="ml-1 size-3" />
                        </Button>
                      )}
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
