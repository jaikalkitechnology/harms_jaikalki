import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Check, X, Wallet } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { internExpensesApi, type InternExpense } from "@/lib/api/employees";

export default function InternExpensesPage() {
  const queryClient = useQueryClient();

  const { data: pending = [], isLoading } = useQuery({
    queryKey: ["intern-expenses", "pending"],
    queryFn: internExpensesApi.pending,
  });
  const { data: all = [] } = useQuery({
    queryKey: ["intern-expenses", "report"],
    queryFn: internExpensesApi.report,
  });

  const approve = useMutation({
    mutationFn: (id: number) => internExpensesApi.approve(id),
    onSuccess: () => {
      toast.success("Expense approved");
      queryClient.invalidateQueries({ queryKey: ["intern-expenses"] });
    },
    onError: () => toast.error("Could not approve"),
  });
  const reject = useMutation({
    mutationFn: (id: number) =>
      internExpensesApi.reject(id, "Rejected by HR"),
    onSuccess: () => {
      toast.success("Expense rejected");
      queryClient.invalidateQueries({ queryKey: ["intern-expenses"] });
    },
    onError: () => toast.error("Could not reject"),
  });
  const reimburse = useMutation({
    mutationFn: (id: number) => internExpensesApi.reimburse(id),
    onSuccess: () => {
      toast.success("Marked as reimbursed");
      queryClient.invalidateQueries({ queryKey: ["intern-expenses"] });
    },
    onError: () => toast.error("Could not reimburse"),
  });

  if (isLoading) return <LoadingScreen label="Loading expenses…" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Phase 2 · Intern Travel Expenses
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          Approval <span className="display-em">queue</span>
        </h2>
        <p className="mt-1 text-sm text-brand-brown-light">
          {pending.length} pending · {all.length} total
        </p>
      </div>

      {pending.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-brand-brown-light">
            All caught up — nothing pending.
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 gap-3">
          {pending.map((exp) => (
            <ExpenseCard
              key={exp.id}
              expense={exp}
              onApprove={() => approve.mutate(exp.id)}
              onReject={() => reject.mutate(exp.id)}
            />
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Recent activity</CardTitle>
          <CardDescription>All intern travel expenses</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {all.slice(0, 20).map((exp) => (
              <ActivityRow
                key={exp.id}
                exp={exp}
                onReimburse={() => reimburse.mutate(exp.id)}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function ExpenseCard({
  expense,
  onApprove,
  onReject,
}: {
  expense: InternExpense;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <Card>
      <CardContent className="pt-5 space-y-3">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
              {expense.expense_type.replace(/_/g, " ")}
            </div>
            <div className="font-display text-2xl font-bold text-brand-brown-darker">
              ₹{Number(expense.amount).toLocaleString("en-IN")}
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light">
              Date
            </div>
            <div className="text-sm">{expense.expense_date}</div>
          </div>
        </div>
        {expense.description && (
          <p className="text-sm text-brand-brown-light">{expense.description}</p>
        )}
        <div className="flex gap-2 pt-2">
          <Button onClick={onApprove} variant="gold" size="sm" className="flex-1">
            <Check className="h-4 w-4" /> Approve
          </Button>
          <Button onClick={onReject} variant="outline" size="sm" className="flex-1">
            <X className="h-4 w-4" /> Reject
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function ActivityRow({
  exp,
  onReimburse,
}: {
  exp: InternExpense;
  onReimburse: () => void;
}) {
  const statusColor: Record<InternExpense["status"], string> = {
    pending: "bg-warning/15 text-warning",
    approved: "bg-info/15 text-info",
    rejected: "bg-error/15 text-error",
    reimbursed: "bg-success/15 text-success",
  };
  return (
    <div className="flex items-center justify-between py-2 border-b border-brand-brown-100/50 last:border-0">
      <div className="min-w-0">
        <div className="text-sm font-medium">
          ₹{Number(exp.amount).toLocaleString("en-IN")} ·{" "}
          {exp.expense_type.replace(/_/g, " ")}
        </div>
        <div className="text-xs text-brand-brown-light">
          {exp.expense_date} · employee #{exp.employee_id}
        </div>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={`text-[10px] font-mono uppercase tracking-[0.2em] px-2 py-1 rounded ${statusColor[exp.status]}`}
        >
          {exp.status}
        </span>
        {exp.status === "approved" && (
          <Button size="sm" variant="ghost" onClick={onReimburse}>
            <Wallet className="h-3.5 w-3.5" /> Reimburse
          </Button>
        )}
      </div>
    </div>
  );
}
