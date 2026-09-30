// Top of the profile: who this is, where they stand, how to reach them,
// and the handful of actions HR takes from here.
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Briefcase,
  Calendar,
  Camera,
  KeyRound,
  Lock,
  Unlock,
  Mail,
  MapPin,
  MoreHorizontal,
  Pencil,
  Phone,
  Settings2,
  User,
  UserCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth";
import { employeesApi, type EmployeeDetail } from "@/lib/api/employees";
import { employeeProfileApi } from "@/lib/api/employeeProfile";
import { launchApi } from "@/lib/api/launch";
import { cn } from "@/lib/utils";
import { CategoryBadge } from "../CategoryBadge";
import { useCompleteness, completenessTone } from "./CompletenessCard";
import { isSeparated } from "./ExitBanner";
import { ContactValue } from "./sections";
import {
  Chip,
  daysUntil,
  errDetail,
  fmtDate,
  tenure,
  titleCase,
  useCanEdit,
} from "./ui";

export function ProfileHeader({
  employee,
  onEdit,
  onCredentials,
  onManageLifecycle,
  onOpenCompleteness,
}: {
  employee: EmployeeDetail;
  onEdit: () => void;
  onCredentials: () => void;
  onManageLifecycle: () => void;
  onOpenCompleteness: () => void;
}) {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canEdit = useCanEdit();
  const canUpdate = hasPermission("employee.update");
  const { data: managers = [] } = useQuery({
    queryKey: ["employees-as-managers"],
    queryFn: () => employeesApi.list(),
  });
  const manager = managers.find((m) => m.id === employee.reporting_to);
  const { data: completeness } = useCompleteness(employee.id);
  const separated = isSeparated(employee);

  return (
    <div className="overflow-hidden rounded-2xl border border-brand-brown-100 bg-card shadow-sm">
      <div className="h-20 bg-gradient-to-r from-brand-gold/25 via-brand-gold/10 to-transparent sm:h-24" />
      <div className="px-5 pb-5 sm:px-6">
        <div className="-mt-12 flex flex-col gap-4 sm:-mt-14 sm:flex-row sm:items-end">
          <Avatar employee={employee} editable={canUpdate && canEdit} />
          <div className="min-w-0 flex-1 sm:pb-1">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-display text-2xl font-bold text-brand-brown-darker sm:text-3xl">
                {employee.first_name} {employee.last_name}
              </h1>
              <span className="rounded bg-brand-brown-50 px-2 py-0.5 font-mono text-xs text-brand-brown-darker">
                {employee.employee_code}
              </span>
            </div>
            <div className="mt-0.5 text-sm text-brand-brown-light">
              {[employee.designation?.name, employee.department?.name]
                .filter(Boolean)
                .join(" · ") || "No designation yet"}
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <StatusChip employee={employee} />
              {!separated && <StageChip employee={employee} />}
              <CategoryBadge code={employee.category?.code} />
            </div>
          </div>
          {canUpdate && (
            <div className="flex shrink-0 flex-wrap gap-2 sm:pb-1">
              {canEdit && (
                <Button variant="outline" className="gap-2" onClick={onEdit}>
                  <Pencil className="size-4" /> Edit
                </Button>
              )}
              <Button variant="outline" className="gap-2" onClick={onCredentials}>
                <KeyRound className="size-4" /> Login
              </Button>
              <MoreMenu
                employee={employee}
                onManageLifecycle={onManageLifecycle}
              />
            </div>
          )}
        </div>

        <div className="mt-5 grid gap-x-6 gap-y-3 border-t border-brand-brown-50 pt-4 text-sm sm:grid-cols-2 lg:grid-cols-4">
          <Fact icon={Calendar} label="Joined">
            {employee.date_of_joining ? (
              <>
                {fmtDate(employee.date_of_joining)}
                <span className="ml-1.5 text-xs text-brand-brown-light">
                  {tenure(
                    employee.date_of_joining,
                    separated ? employee.exit_date : null,
                  )}
                </span>
              </>
            ) : (
              "—"
            )}
          </Fact>
          <Fact icon={UserCheck} label="Reports to">
            {manager ? (
              <Link
                to={`/employees/${manager.id}`}
                className="hover:text-brand-gold-dark hover:underline"
              >
                {manager.first_name} {manager.last_name}
              </Link>
            ) : (
              "—"
            )}
          </Fact>
          <Fact icon={MapPin} label="Works">
            {[titleCase(employee.work_mode), employee.work_location]
              .filter(Boolean)
              .join(" · ") || "—"}
          </Fact>
          {completeness && (
            <Fact icon={Briefcase} label="Profile">
              <button
                type="button"
                onClick={onOpenCompleteness}
                className="flex w-full items-center gap-2"
                title="See what's missing"
              >
                <span className="h-1.5 w-20 overflow-hidden rounded-full bg-brand-brown-100">
                  <span
                    className={cn(
                      "block h-full rounded-full",
                      completenessTone(completeness.percent),
                    )}
                    style={{ width: `${completeness.percent}%` }}
                  />
                </span>
                <span className="tabular-nums">{completeness.percent}%</span>
                {completeness.missing.length > 0 && (
                  <span className="text-xs text-warning">
                    {completeness.missing.length} missing
                  </span>
                )}
              </button>
            </Fact>
          )}
          <Fact icon={Mail} label="Email">
            {employee.personal_email ? (
              <ContactValue
                href={`mailto:${employee.personal_email}`}
                icon={null}
                text={employee.personal_email}
              />
            ) : (
              "—"
            )}
          </Fact>
          <Fact icon={Phone} label="Phone">
            {employee.personal_phone ? (
              <ContactValue
                href={`tel:${employee.personal_phone}`}
                icon={null}
                text={employee.personal_phone}
              />
            ) : (
              "—"
            )}
          </Fact>
        </div>
      </div>
    </div>
  );
}

function Fact({
  icon: Icon,
  label,
  children,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-w-0 items-start gap-2.5">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-brand-gold-dark" />
      <div className="min-w-0 flex-1">
        <div className="text-[11px] uppercase tracking-[0.12em] text-brand-brown-light">
          {label}
        </div>
        <div className="truncate text-brand-brown-darker">{children}</div>
      </div>
    </div>
  );
}

function Avatar({
  employee,
  editable,
}: {
  employee: EmployeeDetail;
  editable: boolean;
}) {
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const upload = useMutation({
    mutationFn: (file: File) => employeeProfileApi.uploadPhoto(employee.id, file),
    onSuccess: () => {
      toast.success("Photo updated");
      qc.invalidateQueries({ queryKey: ["employee", employee.id] });
      qc.invalidateQueries({ queryKey: ["employee-completeness", employee.id] });
    },
    onError: (e) => toast.error(errDetail(e, "Upload failed")),
  });

  const initials =
    `${employee.first_name?.[0] ?? ""}${employee.last_name?.[0] ?? ""}`.toUpperCase();

  return (
    <div className="relative h-24 w-24 shrink-0 sm:h-28 sm:w-28">
      <div className="grid h-full w-full place-items-center overflow-hidden rounded-2xl border-4 border-card bg-brand-gold/20 text-brand-brown-darker shadow">
        {employee.photo_url ? (
          <img src={employee.photo_url} alt="" className="h-full w-full object-cover" />
        ) : initials ? (
          <span className="font-display text-3xl font-bold">{initials}</span>
        ) : (
          <User className="h-10 w-10" />
        )}
      </div>
      {editable && (
        <>
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={upload.isPending}
            className="absolute -bottom-1 -right-1 grid h-8 w-8 place-items-center rounded-full border-2 border-card bg-brand-brown-darker text-white shadow hover:bg-brand-gold-dark"
            title={employee.photo_url ? "Change photo" : "Add photo"}
            aria-label={employee.photo_url ? "Change photo" : "Add photo"}
          >
            <Camera className="h-4 w-4" />
          </button>
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) upload.mutate(f);
              if (inputRef.current) inputRef.current.value = "";
            }}
          />
        </>
      )}
    </div>
  );
}

function StatusChip({ employee }: { employee: EmployeeDetail }) {
  switch (employee.status) {
    case "active":
      return <Chip tone="success">Active</Chip>;
    case "resigned":
      return <Chip tone="error">Resigned</Chip>;
    case "terminated":
      return <Chip tone="error">Terminated</Chip>;
    case "on_leave":
      return <Chip tone="info">On long leave</Chip>;
    default:
      return <Chip tone="error">{titleCase(employee.status)}</Chip>;
  }
}

function StageChip({ employee }: { employee: EmployeeDetail }) {
  if (!employee.is_on_probation) return <Chip tone="success">Confirmed</Chip>;
  const left = employee.probation_end_date
    ? daysUntil(employee.probation_end_date)
    : null;
  const label = employee.category?.code === "INTERN" ? "Intern" : "Probation";
  if (left === null) return <Chip tone="warning">{label}</Chip>;
  return (
    <Chip tone={left < 0 ? "error" : "warning"}>
      {label} ·{" "}
      {left < 0 ? `overdue ${-left}d` : left === 0 ? "ends today" : `${left} days left`}
    </Chip>
  );
}

function MoreMenu({
  employee,
  onManageLifecycle,
}: {
  employee: EmployeeDetail;
  onManageLifecycle: () => void;
}) {
  const qc = useQueryClient();
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const canEdit = useCanEdit();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);

  const unlock = useMutation({
    mutationFn: (unlocked: boolean) =>
      launchApi.setResignationUnlock(employee.id, unlocked),
    onSuccess: (r) => {
      toast.success(
        r.resignation_unlocked
          ? "Employee can now submit a resignation from the app"
          : "Resignation submission locked again",
      );
      qc.invalidateQueries({ queryKey: ["employee", employee.id] });
    },
    onError: (e) => toast.error(errDetail(e, "Could not change")),
  });

  const items: { label: string; icon: React.ReactNode; onClick: () => void; hint?: string }[] = [];
  if (canEdit) {
    items.push({
      label: "Intern / probation / confirmation",
      icon: <Settings2 className="h-4 w-4" />,
      onClick: onManageLifecycle,
    });
  }
  if (hasPermission("approval.act") && !isSeparated(employee)) {
    items.push(
      employee.resignation_unlocked
        ? {
            label: "Lock resignation submission",
            hint: "Currently unlocked in the app",
            icon: <Lock className="h-4 w-4" />,
            onClick: () => unlock.mutate(false),
          }
        : {
            label: "Unlock resignation submission",
            hint: "One-time, after a formal request",
            icon: <Unlock className="h-4 w-4" />,
            onClick: () => unlock.mutate(true),
          },
    );
  }
  if (!items.length) return null;

  return (
    <div className="relative" ref={ref}>
      <Button
        variant="outline"
        size="icon"
        aria-label="More actions"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <MoreHorizontal className="size-4" />
      </Button>
      {open && (
        <div className="absolute right-0 z-30 mt-2 w-72 overflow-hidden rounded-xl border border-brand-brown-100 bg-card py-1 shadow-lg">
          {items.map((it) => (
            <button
              key={it.label}
              type="button"
              className="flex w-full items-start gap-3 px-4 py-2.5 text-left text-sm hover:bg-brand-brown-50/60"
              onClick={() => {
                setOpen(false);
                it.onClick();
              }}
            >
              <span className="mt-0.5 text-brand-brown-light">{it.icon}</span>
              <span>
                <span className="block text-brand-brown-darker">{it.label}</span>
                {it.hint && (
                  <span className="block text-xs text-brand-brown-light">{it.hint}</span>
                )}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
