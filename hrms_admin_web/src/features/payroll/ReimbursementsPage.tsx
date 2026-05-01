import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, Receipt, X } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { payrollApi } from "@/lib/api/payroll";

function inr(n: string) {
  return `₹${Math.round(Number(n)).toLocaleString("en-IN")}`;
}

export default function ReimbursementsPage() {
  const queryClient = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["reimbursements-pending"],
    queryFn: payrollApi.pendingReimbursements,
  });

  const approve = useMutation({
    mutationFn: (id: number) => payrollApi.approveReimbursement(id),
    onSuccess: () => {
      toast.success("Reimbursement approved");
      queryClient.invalidateQueries({ queryKey: ["reimbursements-pending"] });
    },
  });
  const reject = useMutation({
    mutationFn: (id: number) =>
      payrollApi.rejectReimbursement(id, "Rejected"),
    onSuccess: () => {
      toast.success("Reimbursement rejected");
      queryClient.invalidateQueries({ queryKey: ["reimbursements-pending"] });
    },
  });

  if (isLoading) return <LoadingScreen label="Loading reimbursements…" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Phase 7 · Reimbursements
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          Pending <span className="display-em">claims</span>
        </h2>
        <p className="mt-1 text-sm text-brand-brown-light">
          {data.length} claim{data.length === 1 ? "" : "s"} awaiting approval.
          Approved claims are added to the next payroll run.
        </p>
      </div>

      {data.length === 0 ? (
        <Card>
          <CardContent className="py-12 flex flex-col items-center gap-3 text-brand-brown-light">
            <Receipt className="h-10 w-10" />
            <div>All caught up.</div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {data.map((r) => (
            <Card key={r.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-base">
                      {inr(r.amount)}
                    </CardTitle>
                    <CardDescription>
                      Employee #{r.employee_id} · {r.bill_date}
                    </CardDescription>
                  </div>
                  <span className="text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded bg-brand-brown-50 text-brand-brown-darker">
                    {r.category}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {r.description && (
                  <p className="text-sm">{r.description}</p>
                )}
                {r.bill_url && (
                  <a
                    href={r.bill_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs font-mono uppercase tracking-[0.2em] text-brand-gold-dark hover:text-brand-brown-darker"
                  >
                    View bill →
                  </a>
                )}
                <div className="flex gap-2 pt-2">
                  <Button
                    onClick={() => approve.mutate(r.id)}
                    variant="gold"
                    size="sm"
                    className="flex-1"
                  >
                    <Check className="h-4 w-4" /> Approve
                  </Button>
                  <Button
                    onClick={() => reject.mutate(r.id)}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    <X className="h-4 w-4" /> Reject
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
