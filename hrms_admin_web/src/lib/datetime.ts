// Centralised IST formatting.
//
// Backend writes naive UTC strings via Python's datetime.utcnow().toisoformat().
// JavaScript's Date constructor treats bare ISO strings (no TZ suffix) as
// LOCAL time — wrong for our case. Append a "Z" so it's parsed as UTC, then
// format in Asia/Kolkata.

const IST = "Asia/Kolkata";

function toUtcDate(input: string | number | Date | null | undefined): Date | null {
  if (input == null || input === "") return null;
  if (input instanceof Date) return input;
  if (typeof input === "number") return new Date(input);
  // ISO string — append Z if no tz suffix is present.
  const hasTz = /Z$|[+-]\d{2}:?\d{2}$/.test(input);
  return new Date(hasTz ? input : input + "Z");
}

const dt = (opts: Intl.DateTimeFormatOptions) =>
  new Intl.DateTimeFormat("en-IN", { timeZone: IST, ...opts });

const fmtDateOnly = dt({
  year: "numeric",
  month: "short",
  day: "2-digit",
});
const fmtTimeOnly = dt({
  hour: "2-digit",
  minute: "2-digit",
  hour12: true,
});
const fmtDateTime = dt({
  year: "numeric",
  month: "short",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  hour12: true,
});
const fmtDateTimeWithSeconds = dt({
  year: "numeric",
  month: "short",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: true,
});

/** Format as "03 May 2026, 04:25 pm" in IST. */
export function fmtIst(input: string | number | Date | null | undefined, fallback = "—"): string {
  const d = toUtcDate(input);
  return d ? fmtDateTime.format(d) : fallback;
}

/** Format as "03 May 2026" in IST. */
export function fmtIstDate(input: string | number | Date | null | undefined, fallback = "—"): string {
  const d = toUtcDate(input);
  return d ? fmtDateOnly.format(d) : fallback;
}

/** Format as "04:25 pm" in IST. */
export function fmtIstTime(input: string | number | Date | null | undefined, fallback = "—"): string {
  const d = toUtcDate(input);
  return d ? fmtTimeOnly.format(d) : fallback;
}

/** Format with seconds — useful for audit logs. */
export function fmtIstFull(input: string | number | Date | null | undefined, fallback = "—"): string {
  const d = toUtcDate(input);
  return d ? fmtDateTimeWithSeconds.format(d) : fallback;
}

/** Relative humanised label, e.g. "5 minutes ago" / "in 2 hours". */
export function fmtRelativeIst(input: string | number | Date | null | undefined): string {
  const d = toUtcDate(input);
  if (!d) return "—";
  const diffMs = d.getTime() - Date.now();
  const abs = Math.abs(diffMs);
  const min = 60 * 1000;
  const hour = 60 * min;
  const day = 24 * hour;
  const rtf = new Intl.RelativeTimeFormat("en-IN", { numeric: "auto" });
  if (abs < hour) return rtf.format(Math.round(diffMs / min), "minute");
  if (abs < day) return rtf.format(Math.round(diffMs / hour), "hour");
  if (abs < 30 * day) return rtf.format(Math.round(diffMs / day), "day");
  return fmtIstDate(d);
}
