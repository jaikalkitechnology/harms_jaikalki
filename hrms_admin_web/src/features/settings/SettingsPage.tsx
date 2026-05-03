import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Building,
  Crosshair,
  KeyRound,
  MapPin,
  Save,
  Shield,
  ShieldCheck,
  ShieldOff,
  User,
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

type Tab = "account" | "security" | "company" | "preferences" | "office";

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("account");
  const role = useAuthStore((s) => s.role);
  const isSuper = role === "super_admin";

  const tabs: Array<{ id: Tab; label: string; icon: typeof User }> = [
    { id: "account", label: "Account", icon: User },
    { id: "security", label: "Security", icon: Shield },
    { id: "preferences", label: "Preferences", icon: KeyRound },
    ...(isSuper
      ? ([{ id: "office", label: "Office", icon: MapPin }] as const)
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
                ? new Date(u.last_login_at).toLocaleString()
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
