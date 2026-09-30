// Shared building blocks for the employee profile: section cards with
// view / edit modes, label-value grids and small date helpers.
import { createContext, useContext, type ReactNode } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Pencil } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { employeesApi, type EmployeeDetail } from "@/lib/api/employees";
import { cn } from "@/lib/utils";

export const SELECT_CLASS =
  "flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm";

// ── Editability ─────────────────────────────────────────────────────────
// False for an employee who has already left, until HR unlocks editing.
const EditableContext = createContext(true);
export const EditableProvider = EditableContext.Provider;
export const useCanEdit = () => useContext(EditableContext);

// ── Dates ──────────────────────────────────────────────────────────────
const DATE_FMT = new Intl.DateTimeFormat("en-IN", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

/** "2026-08-12" → "12 Aug 2026". Date-only strings, no timezone shift. */
export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "";
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  if (!y || !m || !d) return iso;
  return DATE_FMT.format(new Date(y, m - 1, d));
}

export function todayIso(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** Whole days from today to `iso` (negative when in the past). */
export function daysUntil(iso: string): number {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  const target = new Date(y, m - 1, d).getTime();
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  return Math.round((target - today) / 86_400_000);
}

/** "1 yr 2 mo" between two dates (to = today by default). */
export function tenure(fromIso: string | null | undefined, toIso?: string | null): string {
  if (!fromIso) return "";
  const [fy, fm, fd] = fromIso.slice(0, 10).split("-").map(Number);
  const to = toIso ? toIso.slice(0, 10).split("-").map(Number) : null;
  const now = new Date();
  const [ty, tm, td] = to ?? [now.getFullYear(), now.getMonth() + 1, now.getDate()];
  let months = (ty - fy) * 12 + (tm - fm);
  if (td < fd) months -= 1;
  if (months < 0) return "Not joined yet";
  const y = Math.floor(months / 12);
  const m = months % 12;
  if (!y && !m) return "Under a month";
  return [y && `${y} yr`, m && `${m} mo`].filter(Boolean).join(" ");
}

export function age(dobIso: string | null | undefined): string {
  if (!dobIso) return "";
  const t = tenure(dobIso);
  const yrs = /(\d+) yr/.exec(t)?.[1];
  return yrs ? `${yrs} yrs` : "";
}

export function titleCase(s: string | null | undefined): string {
  if (!s) return "";
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function errDetail(e: unknown, fallback: string): string {
  return (
    (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
    fallback
  );
}

// ── Saving ─────────────────────────────────────────────────────────────
/** PUT /employees/{id} and refresh everything that reads the employee. */
export function useSaveEmployee(employeeId: number, successMessage: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      employeesApi.update(employeeId, body as Partial<EmployeeDetail>),
    onSuccess: () => {
      toast.success(successMessage);
      qc.invalidateQueries({ queryKey: ["employee", employeeId] });
      qc.invalidateQueries({ queryKey: ["employee-completeness", employeeId] });
      qc.invalidateQueries({ queryKey: ["employees"] });
      qc.invalidateQueries({ queryKey: ["salary-breakup"] });
      qc.invalidateQueries({ queryKey: ["lifecycle", employeeId] });
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });
}

// ── Layout ─────────────────────────────────────────────────────────────
export function SectionCard({
  title,
  description,
  onEdit,
  editing = false,
  action,
  className,
  children,
}: {
  title: ReactNode;
  description?: ReactNode;
  /** Shows a pencil button (when editing is allowed and not already editing). */
  onEdit?: () => void;
  editing?: boolean;
  action?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  const canEdit = useCanEdit();
  return (
    <Card className={cn("overflow-hidden", className)}>
      <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0 border-b border-brand-brown-50 px-5 py-4">
        <div className="min-w-0">
          <CardTitle className="text-lg">{title}</CardTitle>
          {description && (
            <CardDescription className="mt-0.5 text-xs">{description}</CardDescription>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {action}
          {onEdit && canEdit && !editing && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 gap-1.5 text-brand-brown-light hover:text-brand-brown-darker"
              onClick={onEdit}
            >
              <Pencil className="h-3.5 w-3.5" /> Edit
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="px-5 py-4">{children}</CardContent>
    </Card>
  );
}

export function InfoGrid({
  children,
  cols = 2,
}: {
  children: ReactNode;
  cols?: 2 | 3;
}) {
  return (
    <dl
      className={cn(
        "grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2",
        cols === 3 && "lg:grid-cols-3",
      )}
    >
      {children}
    </dl>
  );
}

export function InfoItem({
  label,
  value,
  hint,
  onAdd,
  mono = false,
  wide = false,
}: {
  label: string;
  value: ReactNode;
  /** Secondary text under the value, e.g. tenure or age. */
  hint?: ReactNode;
  /** Shown as "· Add" next to an empty value. */
  onAdd?: () => void;
  mono?: boolean;
  wide?: boolean;
}) {
  const canEdit = useCanEdit();
  const empty = value === null || value === undefined || value === "";
  return (
    <div className={cn("min-w-0", wide && "sm:col-span-2 lg:col-span-full")}>
      <dt className="text-[11px] font-medium uppercase tracking-[0.12em] text-brand-brown-light">
        {label}
      </dt>
      <dd className="mt-1 text-sm text-brand-brown-darker">
        {empty ? (
          <span className="text-brand-brown-light/80">
            Not added
            {onAdd && canEdit && (
              <>
                {" · "}
                <button
                  type="button"
                  onClick={onAdd}
                  className="font-medium text-brand-gold-dark hover:underline"
                >
                  Add
                </button>
              </>
            )}
          </span>
        ) : (
          <span className={cn("break-words", mono && "font-mono")}>{value}</span>
        )}
        {!empty && hint && (
          <span className="ml-2 text-xs text-brand-brown-light">{hint}</span>
        )}
      </dd>
    </div>
  );
}

export function Field({
  label,
  children,
  className,
  help,
}: {
  label: string;
  children: ReactNode;
  className?: string;
  help?: ReactNode;
}) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <Label>{label}</Label>
      {children}
      {help && <p className="text-xs text-brand-brown-light">{help}</p>}
    </div>
  );
}

export function FormActions({
  onCancel,
  onSave,
  saving,
  disabled,
  saveLabel = "Save",
  extra,
}: {
  onCancel: () => void;
  onSave: () => void;
  saving?: boolean;
  disabled?: boolean;
  saveLabel?: string;
  extra?: ReactNode;
}) {
  return (
    <div className="col-span-full flex flex-wrap items-center justify-end gap-2 border-t border-brand-brown-50 pt-4">
      {extra && <div className="mr-auto">{extra}</div>}
      <Button variant="outline" onClick={onCancel} disabled={saving}>
        Cancel
      </Button>
      <Button onClick={onSave} disabled={disabled || saving}>
        {saving ? "Saving…" : saveLabel}
      </Button>
    </div>
  );
}

export function EmptyState({
  message,
  actionLabel,
  onAction,
}: {
  message: ReactNode;
  actionLabel?: string;
  onAction?: () => void;
}) {
  const canEdit = useCanEdit();
  return (
    <div className="flex flex-col items-start gap-3 rounded-lg border border-dashed border-brand-brown-100 px-4 py-5 text-sm text-brand-brown-light sm:flex-row sm:items-center sm:justify-between">
      <div>{message}</div>
      {actionLabel && onAction && canEdit && (
        <Button variant="outline" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

export function Chip({
  tone = "neutral",
  children,
}: {
  tone?: "neutral" | "success" | "warning" | "error" | "info" | "gold";
  children: ReactNode;
}) {
  const tones: Record<string, string> = {
    neutral: "bg-brand-brown-50 text-brand-brown-darker",
    success: "bg-success/10 text-success",
    warning: "bg-warning/10 text-warning",
    error: "bg-error/10 text-error",
    info: "bg-info/10 text-info",
    gold: "bg-brand-gold/15 text-brand-gold-dark",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        tones[tone],
      )}
    >
      {children}
    </span>
  );
}
