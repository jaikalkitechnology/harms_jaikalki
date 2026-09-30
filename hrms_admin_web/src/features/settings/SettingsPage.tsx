import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Building,
  CalendarDays,
  Clock,
  Crosshair,
  KeyRound,
  MapPin,
  Save,
  Shield,
  ShieldCheck,
  ShieldOff,
  User,
  Wallet,
} from "lucide-react";

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
import {
  adminMe,
  changePassword,
  mfaDisable,
  mfaEnroll,
  mfaVerify,
} from "@/lib/api/auth";
import { superAdminApi, type Branding } from "@/lib/api/super-admin";
import { useAuthStore } from "@/store/auth";
import { ROLE_LABEL, type Role } from "@/lib/constants";
import { useThemeStore, type ThemeMode } from "@/store/theme";
import { cn } from "@/lib/utils";
import { fmtIst } from "@/lib/datetime";
import { PayrollSettingsTab } from "./PayrollSettingsTab";

type Tab =
  | "account"
  | "security"
  | "company"
  | "preferences"
  | "office"
  | "leave"
  | "attendance"
  | "payroll";

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("account");
  const role = useAuthStore((s) => s.role);
  const isSuper = role === "super_admin";
  const canPayroll = useAuthStore((s) => s.hasPermission("payroll.run"));

  const tabs: Array<{ id: Tab; label: string; icon: typeof User }> = [
    { id: "account", label: "Account", icon: User },
    { id: "security", label: "Security", icon: Shield },
    { id: "preferences", label: "Preferences", icon: KeyRound },
    ...(isSuper
      ? ([
          { id: "office", label: "Office", icon: MapPin },
          { id: "leave", label: "Leave policy", icon: CalendarDays },
          { id: "attendance", label: "Attendance", icon: Clock },
        ] as const)
      : []),
    ...(isSuper || canPayroll
      ? ([{ id: "payroll", label: "Payroll", icon: Wallet }] as const)
      : []),
    { id: "company", label: "Company", icon: Building },
  ];

  return (
    <div className="space-y-6">
      <div className="overflow-x-auto -mx-4 px-4 md:mx-0 md:px-0">
        <div className="inline-flex gap-1 border border-brand-brown-50 rounded-lg p-1 bg-card">
          {tabs.map((t) => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 text-sm rounded-md whitespace-nowrap transition-colors",
                  active
                    ? "bg-brand-gold/15 text-brand-brown-darker"
                    : "text-brand-brown-light hover:bg-brand-brown-50",
                )}
              >
                <Icon className="h-4 w-4" />
                {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {tab === "account" && <AccountTab />}
      {tab === "security" && <SecurityTab />}
      {tab === "preferences" && <PreferencesTab />}
      {tab === "office" && <OfficeTab />}
      {tab === "leave" && <LeavePolicyTab />}
      {tab === "attendance" && <AttendanceTab />}
      {tab === "payroll" && <PayrollSettingsTab />}
      {tab === "company" && <CompanyTab />}
    </div>
  );
}

// ── Account ─────────────────────────────────────────────────────────
function AccountTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["admin-me"],
    queryFn: adminMe,
  });
  const [pwd, setPwd] = useState({
    old: "",
    next: "",
    confirm: "",
  });
  const change = useMutation({
    mutationFn: () =>
      changePassword({
        old_password: pwd.old,
        new_password: pwd.next,
      }),
    onSuccess: () => {
      toast.success("Password updated");
      setPwd({ old: "", next: "", confirm: "" });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(
        err?.response?.data?.detail ?? "Could not update password",
      ),
  });

  if (isLoading || !data) return <LoadingScreen />;

  const u = data.user;

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>
            Read-only here. Full edits land via /employees.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Field label="Full name" value={u.full_name} />
          <Field label="Email" value={u.email} />
          <Field label="Phone" value={u.phone ?? "—"} />
          <Field label="Primary role" value={ROLE_LABEL[data.role as Role] ?? data.role ?? "—"} />
          <Field
            label="Other roles"
            value={
              data.roles.filter((r) => r !== data.role).join(", ") || "—"
            }
          />
          <Field
            label="Last login"
            value={
              u.last_login_at
                ? fmtIst(u.last_login_at)
                : "—"
            }
          />
          <Field
            label="Status"
            value={u.is_active ? "Active" : "Inactive"}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Change password</CardTitle>
          <CardDescription>
            Minimum 8 characters. You'll stay signed in on this device.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <Label>Current password</Label>
            <Input
              type="password"
              value={pwd.old}
              onChange={(e) => setPwd({ ...pwd, old: e.target.value })}
            />
          </div>
          <div>
            <Label>New password</Label>
            <Input
              type="password"
              value={pwd.next}
              onChange={(e) => setPwd({ ...pwd, next: e.target.value })}
            />
          </div>
          <div>
            <Label>Confirm new password</Label>
            <Input
              type="password"
              value={pwd.confirm}
              onChange={(e) => setPwd({ ...pwd, confirm: e.target.value })}
            />
            {pwd.confirm.length > 0 && pwd.confirm !== pwd.next && (
              <div className="text-xs text-error mt-1">
                Passwords don't match
              </div>
            )}
          </div>
          <Button
            disabled={
              !pwd.old ||
              pwd.next.length < 8 ||
              pwd.next !== pwd.confirm ||
              change.isPending
            }
            onClick={() => change.mutate()}
          >
            <Save className="h-4 w-4 mr-1" /> Update password
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-0.5">
        {label}
      </div>
      <div className="text-sm text-brand-brown-darker">{value}</div>
    </div>
  );
}

// ── Security (MFA) ─────────────────────────────────────────────────
function SecurityTab() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["admin-me"],
    queryFn: adminMe,
  });
  const [enrollPayload, setEnrollPayload] = useState<
    null | { secret: string; otpauth_uri: string }
  >(null);
  const [code, setCode] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null);

  const enroll = useMutation({
    mutationFn: () => mfaEnroll(),
    onSuccess: (resp) => setEnrollPayload(resp),
    onError: () => toast.error("Could not start enrollment"),
  });

  const verify = useMutation({
    mutationFn: () => mfaVerify(code),
    onSuccess: (resp) => {
      setBackupCodes(resp.backup_codes);
      setEnrollPayload(null);
      setCode("");
      toast.success("Two-factor authentication enabled");
      qc.invalidateQueries({ queryKey: ["admin-me"] });
    },
    onError: () => toast.error("Invalid code"),
  });

  const disable = useMutation({
    mutationFn: () => mfaDisable(code),
    onSuccess: () => {
      toast.success("Two-factor disabled");
      setCode("");
      qc.invalidateQueries({ queryKey: ["admin-me"] });
    },
    onError: () => toast.error("Invalid code"),
  });

  if (isLoading || !data) return <LoadingScreen />;
  const enabled = data.user.mfa_enabled;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {enabled ? (
              <ShieldCheck className="h-5 w-5 text-success" />
            ) : (
              <ShieldOff className="h-5 w-5 text-brand-brown-light" />
            )}
            Two-factor authentication
          </CardTitle>
          <CardDescription>
            {enabled
              ? "TOTP is required for super-admin / HR logins."
              : "Strongly recommended — uses any TOTP app (Google Authenticator, 1Password, Authy)."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!enabled && !enrollPayload && (
            <Button onClick={() => enroll.mutate()}>
              Set up two-factor
            </Button>
          )}

          {!enabled && enrollPayload && (
            <div className="space-y-3">
              <div className="text-sm">
                Scan this URI in your authenticator app, then enter the
                6-digit code below to confirm.
              </div>
              <div className="border border-brand-brown-50 rounded p-3 bg-brand-brown-50/30">
                <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-1">
                  otpauth URI
                </div>
                <code className="text-xs break-all font-mono">
                  {enrollPayload.otpauth_uri}
                </code>
              </div>
              <div className="text-xs text-brand-brown-light">
                Or enter the secret manually:{" "}
                <code className="font-mono">{enrollPayload.secret}</code>
              </div>
              <div className="flex gap-2 items-end">
                <div className="flex-1">
                  <Label>6-digit code</Label>
                  <Input
                    inputMode="numeric"
                    maxLength={6}
                    value={code}
                    onChange={(e) =>
                      setCode(e.target.value.replace(/\D/g, ""))
                    }
                  />
                </div>
                <Button
                  disabled={code.length !== 6 || verify.isPending}
                  onClick={() => verify.mutate()}
                >
                  Confirm
                </Button>
              </div>
            </div>
          )}

          {enabled && (
            <div className="flex gap-2 items-end">
              <div className="flex-1">
                <Label>Enter a 6-digit code from your app to disable</Label>
                <Input
                  inputMode="numeric"
                  maxLength={6}
                  value={code}
                  onChange={(e) =>
                    setCode(e.target.value.replace(/\D/g, ""))
                  }
                />
              </div>
              <Button
                variant="outline"
                disabled={code.length !== 6}
                onClick={() => {
                  if (confirm("Disable two-factor authentication?"))
                    disable.mutate();
                }}
              >
                Disable
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {backupCodes && (
        <Card>
          <CardHeader>
            <CardTitle>Backup codes</CardTitle>
            <CardDescription>
              Save these somewhere safe — they're shown ONCE and let you
              sign in if you lose your authenticator.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {backupCodes.map((c) => (
                <code
                  key={c}
                  className="font-mono text-sm bg-brand-brown-50 px-3 py-2 rounded"
                >
                  {c}
                </code>
              ))}
            </div>
            <div className="mt-3">
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  navigator.clipboard.writeText(backupCodes.join("\n"));
                  toast.success("Copied");
                }}
              >
                Copy all
              </Button>{" "}
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setBackupCodes(null)}
              >
                I've saved them
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ── Preferences (theme) ────────────────────────────────────────────
function PreferencesTab() {
  const mode = useThemeStore((s) => s.mode);
  const setMode = useThemeStore((s) => s.setMode);
  const opts: Array<{ id: ThemeMode; label: string; desc: string }> = [
    { id: "light", label: "Light", desc: "Always use the light theme." },
    { id: "dark", label: "Dark", desc: "Always use the dark theme." },
    { id: "system", label: "System", desc: "Follow OS preference." },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Theme</CardTitle>
        <CardDescription>
          Stored locally per browser.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        {opts.map((o) => (
          <label
            key={o.id}
            className={cn(
              "flex items-center gap-3 border rounded-lg p-3 cursor-pointer",
              mode === o.id
                ? "border-brand-gold-dark bg-brand-gold/10"
                : "border-brand-brown-50",
            )}
          >
            <input
              type="radio"
              name="theme"
              value={o.id}
              checked={mode === o.id}
              onChange={() => setMode(o.id)}
            />
            <div>
              <div className="font-medium text-sm">{o.label}</div>
              <div className="text-xs text-brand-brown-light">{o.desc}</div>
            </div>
          </label>
        ))}
      </CardContent>
    </Card>
  );
}

// ── Company (read-only branding view) ──────────────────────────────
function CompanyTab() {
  const role = useAuthStore((s) => s.role);
  const isSuper = role === "super_admin";
  const { data, isLoading } = useQuery({
    queryKey: ["branding"],
    queryFn: superAdminApi.getBranding,
    enabled: isSuper,
  });

  if (!isSuper) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-brand-brown-light">
          Company-wide settings can only be edited by Super Admins.
        </CardContent>
      </Card>
    );
  }

  if (isLoading || !data) return <LoadingScreen />;

  const b = data as Branding;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Company branding</CardTitle>
        <CardDescription>
          Read-only summary. Full editor lives at /super-admin/branding.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid md:grid-cols-2 gap-3">
        <Field label="Company name" value={b.company_name} />
        <Field label="Custom domain" value={b.custom_domain ?? "—"} />
        <Field label="Primary colour" value={b.primary_color} />
        <Field label="Secondary colour" value={b.secondary_color} />
        <Field label="Font family" value={b.font_family} />
        <Field label="Logo URL" value={b.logo_url ?? "—"} />
      </CardContent>
    </Card>
  );
}

// ── Office geo-fence ───────────────────────────────────────────────
function OfficeTab() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["office-location"],
    queryFn: superAdminApi.getOfficeLocation,
  });
  const [form, setForm] = useState({ lat: "", lng: "", radius_m: "500" });
  const [picking, setPicking] = useState(false);
  const [myPos, setMyPos] = useState<{ lat: number; lng: number } | null>(null);

  // Hydrate the form once the server payload arrives.
  useEffect(() => {
    if (data) {
      setForm({
        lat: String(data.lat),
        lng: String(data.lng),
        radius_m: String(data.radius_m),
      });
    }
  }, [data]);

  const save = useMutation({
    mutationFn: () =>
      superAdminApi.setOfficeLocation({
        lat: Number(form.lat),
        lng: Number(form.lng),
        radius_m: Number(form.radius_m),
      }),
    onSuccess: (resp) => {
      toast.success("Office location saved");
      setForm({
        lat: String(resp.lat),
        lng: String(resp.lng),
        radius_m: String(resp.radius_m),
      });
      qc.invalidateQueries({ queryKey: ["office-location"] });
    },
    onError: (err: { response?: { data?: { detail?: string } } }) =>
      toast.error(err?.response?.data?.detail ?? "Save failed"),
  });

  const useCurrentLocation = () => {
    if (!navigator.geolocation) {
      toast.error("Geolocation not supported in this browser");
      return;
    }
    setPicking(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        setForm((f) => ({
          ...f,
          lat: latitude.toFixed(6),
          lng: longitude.toFixed(6),
        }));
        setMyPos({ lat: latitude, lng: longitude });
        toast.success("Captured your current GPS reading");
        setPicking(false);
      },
      (err) => {
        toast.error(`Location: ${err.message}`);
        setPicking(false);
      },
      { enableHighAccuracy: true, timeout: 15000 },
    );
  };

  const previewMapUrl = useMemo(() => {
    const lat = Number(form.lat);
    const lng = Number(form.lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
    const r = Number(form.radius_m) || 500;
    const halfDeg = (r / 111_000) * 4; // rough — show ~4× the radius
    const left = lng - halfDeg;
    const right = lng + halfDeg;
    const top = lat + halfDeg;
    const bottom = lat - halfDeg;
    return `https://www.openstreetmap.org/export/embed.html?bbox=${left}%2C${bottom}%2C${right}%2C${top}&layer=mapnik&marker=${lat}%2C${lng}`;
  }, [form.lat, form.lng, form.radius_m]);

  if (isLoading) return <LoadingScreen />;

  const distance = myPos && data
    ? haversineMeters(myPos.lat, myPos.lng, Number(form.lat), Number(form.lng))
    : null;

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5" /> Office geo-fence
          </CardTitle>
          <CardDescription>
            Employees can only mark <strong>office</strong>-mode attendance
            from inside this radius. WFH / hybrid modes are unaffected.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <Label>Latitude</Label>
              <Input
                value={form.lat}
                onChange={(e) => setForm({ ...form, lat: e.target.value })}
                placeholder="19.285300"
                inputMode="decimal"
              />
            </div>
            <div>
              <Label>Longitude</Label>
              <Input
                value={form.lng}
                onChange={(e) => setForm({ ...form, lng: e.target.value })}
                placeholder="72.853300"
                inputMode="decimal"
              />
            </div>
          </div>
          <div>
            <Label>Radius (metres)</Label>
            <Input
              type="number"
              min={10}
              max={50000}
              value={form.radius_m}
              onChange={(e) => setForm({ ...form, radius_m: e.target.value })}
            />
            <div className="text-xs text-brand-brown-light mt-1">
              500 m covers a typical office building plus its parking; 200 m
              is tight but secure; lift to ~1000 m for a campus.
            </div>
          </div>

          <div className="flex gap-2 flex-wrap">
            <Button onClick={() => save.mutate()} disabled={save.isPending}>
              <Save className="h-4 w-4 mr-1" /> Save
            </Button>
            <Button
              variant="outline"
              onClick={useCurrentLocation}
              disabled={picking}
            >
              <Crosshair className="h-4 w-4 mr-1" />
              {picking ? "Locating…" : "Use my current location"}
            </Button>
          </div>

          {distance != null && (
            <div className="text-xs text-brand-brown-light">
              Your current position is <strong>{Math.round(distance)} m</strong>{" "}
              from the configured office point.
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Preview</CardTitle>
          <CardDescription>
            OpenStreetMap pin at the configured coordinates.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {previewMapUrl ? (
            <iframe
              title="Office location preview"
              src={previewMapUrl}
              className="w-full h-72 rounded-lg border border-brand-brown-50"
            />
          ) : (
            <div className="text-sm text-brand-brown-light">
              Enter valid lat / lng to preview.
            </div>
          )}
          <a
            href={
              Number.isFinite(Number(form.lat))
                ? `https://www.openstreetmap.org/?mlat=${form.lat}&mlon=${form.lng}#map=18/${form.lat}/${form.lng}`
                : "#"
            }
            target="_blank"
            rel="noreferrer"
            className="text-xs text-brand-gold-dark underline mt-2 inline-block"
          >
            Open in OpenStreetMap →
          </a>
        </CardContent>
      </Card>
    </div>
  );
}

function haversineMeters(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  if (![lat1, lng1, lat2, lng2].every((n) => Number.isFinite(n))) return 0;
  const R = 6_371_000;
  const toRad = (x: number) => (x * Math.PI) / 180;
  const dlat = toRad(lat2 - lat1);
  const dlng = toRad(lng2 - lng1);
  const a =
    Math.sin(dlat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dlng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

// ── Leave policy ───────────────────────────────────────────────────
function LeavePolicyTab() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["leave-policy"],
    queryFn: superAdminApi.getLeavePolicy,
  });

  const [form, setForm] = useState({
    sandwich_enabled: false,
    sandwich_count_holidays: true,
    earned_accrual_enabled: false,
    earned_accrual_days_required: 19,
    earned_accrual_credit_days: 1,
    earned_accrual_leave_type_code: "EL",
  });

  useEffect(() => {
    if (data) setForm({ ...form, ...data });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const save = useMutation({
    mutationFn: () =>
      superAdminApi.setLeavePolicy({
        ...form,
        earned_accrual_days_required: Number(form.earned_accrual_days_required),
        earned_accrual_credit_days: Number(form.earned_accrual_credit_days),
      }),
    onSuccess: () => {
      toast.success("Leave policy saved");
      qc.invalidateQueries({ queryKey: ["leave-policy"] });
    },
    onError: () => toast.error("Save failed"),
  });

  const recompute = useMutation({
    mutationFn: () => superAdminApi.recomputeEarnedLeaves(),
    onSuccess: (r) => {
      if (!r.enabled) {
        toast.message("Earned-accrual is disabled — flip the switch first.");
        return;
      }
      if (r.error) {
        toast.error(r.error);
        return;
      }
      toast.success(
        `Recomputed for ${r.processed} employees · +${r.credited_total} new days`,
      );
    },
    onError: () => toast.error("Recompute failed"),
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5" /> Sandwich rule
          </CardTitle>
          <CardDescription>
            When enabled, intermediate Sundays — and optionally public
            holidays — between two leave days are also counted. A leave
            spanning Saturday → Monday becomes <strong>3 days</strong>{" "}
            instead of 2. Single-day or weekend-only requests are
            unaffected.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <label className="flex items-start gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              className="mt-1"
              checked={form.sandwich_enabled}
              onChange={(e) =>
                setForm({ ...form, sandwich_enabled: e.target.checked })
              }
            />
            <span>
              <span className="font-medium">Enable sandwich leave rule</span>
              <span className="block text-xs text-brand-brown-light">
                Sundays inside a leave range count when both endpoints are
                working days.
              </span>
            </span>
          </label>

          <label className="flex items-start gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              className="mt-1"
              disabled={!form.sandwich_enabled}
              checked={form.sandwich_count_holidays}
              onChange={(e) =>
                setForm({
                  ...form,
                  sandwich_count_holidays: e.target.checked,
                })
              }
            />
            <span>
              <span className="font-medium">Also count public holidays</span>
              <span className="block text-xs text-brand-brown-light">
                Off by default would let employees skip a holiday between two
                leaves; on by default penalises them like Sundays.
              </span>
            </span>
          </label>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CalendarDays className="h-5 w-5" /> Earned-leave accrual
          </CardTitle>
          <CardDescription>
            For every <strong>N attendance days</strong> (Sundays counted as
            present), automatically credit <strong>X leaves</strong> to a
            specific leave type. Recomputation is idempotent — safe to run
            on demand or daily.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <label className="flex items-start gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              className="mt-1"
              checked={form.earned_accrual_enabled}
              onChange={(e) =>
                setForm({
                  ...form,
                  earned_accrual_enabled: e.target.checked,
                })
              }
            />
            <span className="font-medium">Enable auto-accrual</span>
          </label>

          <div className="grid sm:grid-cols-3 gap-3">
            <div>
              <Label>Days required</Label>
              <Input
                type="number"
                min={1}
                max={365}
                value={form.earned_accrual_days_required}
                onChange={(e) =>
                  setForm({
                    ...form,
                    earned_accrual_days_required: Number(e.target.value),
                  })
                }
              />
            </div>
            <div>
              <Label>Credit (days)</Label>
              <Input
                type="number"
                step="0.5"
                min={0.5}
                max={30}
                value={form.earned_accrual_credit_days}
                onChange={(e) =>
                  setForm({
                    ...form,
                    earned_accrual_credit_days: Number(e.target.value),
                  })
                }
              />
            </div>
            <div>
              <Label>Leave type code</Label>
              <Input
                value={form.earned_accrual_leave_type_code}
                onChange={(e) =>
                  setForm({
                    ...form,
                    earned_accrual_leave_type_code: e.target.value
                      .toUpperCase()
                      .replace(/[^A-Z0-9]/g, ""),
                  })
                }
                placeholder="EL"
              />
            </div>
          </div>

          <div className="text-xs text-brand-brown-light">
            Example: 19 + 1 + EL means each 19 attendance days credits 1
            day to the <strong>EL</strong> leave type.
          </div>
        </CardContent>
      </Card>

      <div className="md:col-span-2 flex flex-wrap gap-2 justify-end">
        <Button
          variant="outline"
          disabled={recompute.isPending || !form.earned_accrual_enabled}
          onClick={() => recompute.mutate()}
        >
          {recompute.isPending ? "Recomputing…" : "Recompute earned leaves now"}
        </Button>
        <Button onClick={() => save.mutate()} disabled={save.isPending}>
          <Save className="h-4 w-4 mr-1" /> Save policy
        </Button>
      </div>
    </div>
  );
}

// ── Attendance policy ──────────────────────────────────────────────
function AttendanceTab() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["attendance-policy"],
    queryFn: superAdminApi.getAttendancePolicy,
  });
  const [form, setForm] = useState({
    late_grace_minutes: 0,
    default_shift_start: "09:00",
    late_mark_minutes: 10,
    halfday_after_minutes: 60,
    halfday_free_count: 2,
  });

  useEffect(() => {
    if (data)
      setForm({
        late_grace_minutes: Number(data.late_grace_minutes ?? 0),
        default_shift_start: String(data.default_shift_start ?? "09:00"),
        late_mark_minutes: Number(data.late_mark_minutes ?? 10),
        halfday_after_minutes: Number(data.halfday_after_minutes ?? 60),
        halfday_free_count: Number(data.halfday_free_count ?? 2),
      });
  }, [data]);

  const save = useMutation({
    mutationFn: () =>
      superAdminApi.setAttendancePolicy({
        late_grace_minutes: form.late_grace_minutes,
        default_shift_start: form.default_shift_start,
        late_mark_minutes: form.late_mark_minutes,
        halfday_after_minutes: form.halfday_after_minutes,
        halfday_free_count: form.halfday_free_count,
      }),
    onSuccess: () => {
      toast.success("Attendance policy saved");
      qc.invalidateQueries({ queryKey: ["attendance-policy"] });
    },
    onError: () => toast.error("Save failed"),
  });

  if (isLoading) return <LoadingScreen />;

  return (
    <Card className="max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5" /> Late-arrival rule
        </CardTitle>
        <CardDescription>
          When an employee checks in more than the configured number of
          minutes after their shift start, the day is automatically
          marked as <strong>half day</strong>. Set 0 to disable.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid sm:grid-cols-2 gap-3">
          <div>
            <Label>Grace minutes (late → half day)</Label>
            <Input
              type="number"
              min={0}
              max={480}
              value={form.late_grace_minutes}
              onChange={(e) =>
                setForm({
                  ...form,
                  late_grace_minutes: Number(e.target.value),
                })
              }
            />
            <div className="text-xs text-brand-brown-light mt-1">
              Examples: 10 (strict), 30 (typical), 60 (lenient).
            </div>
          </div>
          <div>
            <Label>Default shift start</Label>
            <Input
              type="time"
              value={form.default_shift_start}
              onChange={(e) =>
                setForm({ ...form, default_shift_start: e.target.value })
              }
            />
            <div className="text-xs text-brand-brown-light mt-1">
              Used when an employee has no assigned shift. Otherwise the
              employee's actual shift start is honoured.
            </div>
          </div>
        </div>

        <div className="border-t border-brand-brown-100 pt-3">
          <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-gold-dark mb-2">
            Shift late / half-day rule
          </div>
          <div className="grid sm:grid-cols-3 gap-3">
            <div>
              <Label>Late after (min)</Label>
              <Input
                type="number"
                min={0}
                max={240}
                value={form.late_mark_minutes}
                onChange={(e) =>
                  setForm({
                    ...form,
                    late_mark_minutes: Number(e.target.value),
                  })
                }
              />
              <div className="text-xs text-brand-brown-light mt-1">
                Past this many minutes after shift start, the day is
                flagged <strong>late</strong>.
              </div>
            </div>
            <div>
              <Label>Half-day after (min)</Label>
              <Input
                type="number"
                min={0}
                max={480}
                value={form.halfday_after_minutes}
                onChange={(e) =>
                  setForm({
                    ...form,
                    halfday_after_minutes: Number(e.target.value),
                  })
                }
              />
              <div className="text-xs text-brand-brown-light mt-1">
                A check-in later than this counts as a “very late”
                occurrence (e.g. 60 = 1 hr).
              </div>
            </div>
            <div>
              <Label>Forgiven / cycle</Label>
              <Input
                type="number"
                min={0}
                max={31}
                value={form.halfday_free_count}
                onChange={(e) =>
                  setForm({
                    ...form,
                    halfday_free_count: Number(e.target.value),
                  })
                }
              />
              <div className="text-xs text-brand-brown-light mt-1">
                First N very-late days each month cycle stay full. From
                the (N+1)th, the day is auto half-day. e.g. 2 ⇒ 3rd
                very-late day onward is half-day.
              </div>
            </div>
          </div>
        </div>

        <div>
          <Button onClick={() => save.mutate()} disabled={save.isPending}>
            <Save className="h-4 w-4 mr-1" /> Save
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
