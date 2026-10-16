import { DAY_STATUS, type TeamRollup, type TeamToday } from "@/lib/api/team";
import { cn } from "@/lib/utils";
import { Chip } from "@/features/employees/profile/ui";

export const inr = (v: string | number | null | undefined) =>
  `₹${Number(v ?? 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

export const hhmm = (iso: string | null) =>
  iso ? new Date(iso).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }) : "";

export function Avatar({ name, photo, size = 36 }: { name: string; photo: string | null; size?: number }) {
  const initials = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
  return photo ? (
    <img
      src={photo}
      alt=""
      className="shrink-0 rounded-full object-cover"
      style={{ width: size, height: size }}
    />
  ) : (
    <span
      className="grid shrink-0 place-items-center rounded-full bg-brand-gold/20 font-semibold text-brand-gold-dark"
      style={{ width: size, height: size, fontSize: size * 0.36 }}
    >
      {initials}
    </span>
  );
}

export function StatusChip({ today }: { today: TeamToday }) {
  const s = DAY_STATUS[today.status];
  return (
    <span className="flex flex-col items-start gap-0.5">
      <Chip tone={s.tone}>{s.label}</Chip>
      {today.check_in && (
        <span className="text-[11px] text-brand-brown-light">
          in {hhmm(today.check_in)}
          {today.check_out ? ` · out ${hhmm(today.check_out)}` : ""}
        </span>
      )}
    </span>
  );
}

export function TargetBar({ pct, sub }: { pct: number | null; sub?: string }) {
  const p = Math.max(0, Math.min(100, pct ?? 0));
  const tone = (pct ?? 0) >= 100 ? "bg-success" : (pct ?? 0) >= 60 ? "bg-brand-gold" : "bg-warning";
  return (
    <div className="min-w-[140px]">
      <div className="flex items-center gap-2">
        <span className="h-1.5 w-24 overflow-hidden rounded-full bg-brand-brown-50">
          <span className={cn("block h-full", tone)} style={{ width: `${p}%` }} />
        </span>
        <span className="text-xs font-medium text-brand-brown-darker">{pct != null ? `${pct}%` : "—"}</span>
      </div>
      {sub && <div className="mt-0.5 text-[11px] text-brand-brown-light">{sub}</div>}
    </div>
  );
}

export function TeamLine({ t }: { t: TeamRollup }) {
  return (
    <span className="text-xs leading-5 text-brand-brown-darker">
      <span className="font-medium">{t.size} {t.size === 1 ? "person" : "people"}</span>
      {t.attendance_pct != null && <span> · {t.attendance_pct}% present</span>}
      {t.target_pct != null && <span> · {t.target_pct}% of target</span>}
      {t.absent + t.late > 0 && (
        <span className="text-warning"> · {t.absent ? `${t.absent} absent` : ""}{t.absent && t.late ? ", " : ""}{t.late ? `${t.late} late` : ""}</span>
      )}
    </span>
  );
}
