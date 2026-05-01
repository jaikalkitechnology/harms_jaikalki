import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate, useLocation } from "react-router-dom";
import { toast } from "sonner";
import { Eye, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/shared/LoadingScreen";
import { Logo } from "@/components/shared/Logo";
import { useAuthStore } from "@/store/auth";
import { COMPANY_NAME } from "@/lib/constants";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(4, "Password too short"),
  rememberMe: z.boolean().default(false),
});

type LoginValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const login = useAuthStore((s) => s.login);
  const submitMfa = useAuthStore((s) => s.submitMfa);
  const cancelMfa = useAuthStore((s) => s.cancelMfa);
  const needsMfa = useAuthStore((s) => s.needsMfa);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "", rememberMe: false },
  });

  useEffect(() => {
    if (isAuthenticated) {
      const from =
        (location.state as { from?: string } | null)?.from ?? "/dashboard";
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location.state]);

  async function onSubmit(values: LoginValues) {
    setSubmitting(true);
    try {
      await login(values.email, values.password, values.rememberMe);
      toast.success("Welcome back");
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response
        ?.status;
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Sign in failed";
      if (status === 401 && !detail.toLowerCase().includes("mfa")) {
        toast.error("Invalid email or password");
      } else if (!detail.toLowerCase().includes("mfa")) {
        toast.error(detail);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-surface-cream">
      <div className="relative hidden lg:flex flex-col justify-between p-12 bg-brand-brown-darker text-surface-warm overflow-hidden">
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 30%, rgba(244,183,31,0.4), transparent 50%), radial-gradient(circle at 80% 70%, rgba(244,183,31,0.2), transparent 50%)",
          }}
        />
        <div className="relative">
          <Logo variant="horizontal-dark" className="h-12 w-auto" />
        </div>
        <div className="relative">
          <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold mb-3">
            ★ Human Capital, Reimagined
          </div>
          <h2 className="font-display text-5xl font-bold leading-tight">
            Welcome to <span className="display-em">Jaikalki HRMS</span>
          </h2>
          <p className="mt-4 max-w-md text-brand-brown-100">
            One platform for attendance, payroll, approvals, and the
            field-force — built for {COMPANY_NAME}.
          </p>
        </div>
        <div className="relative text-[10px] font-mono uppercase tracking-[0.3em] text-brand-brown-100/70">
          v0.1 · Phase 1.5 · Admin Auth
        </div>
      </div>

      <div className="flex items-center justify-center p-8">
        <Card className="w-full max-w-md">
          <CardContent className="pt-8">
            <div className="lg:hidden mb-6 flex justify-center">
              <Logo variant="horizontal-light" className="h-12 w-auto" />
            </div>

            {needsMfa ? (
              <MfaPrompt
                onCancel={cancelMfa}
                onSubmit={async (code) => {
                  setSubmitting(true);
                  try {
                    await submitMfa(code);
                    toast.success("Welcome back");
                  } catch {
                    toast.error("Invalid MFA code");
                  } finally {
                    setSubmitting(false);
                  }
                }}
                submitting={submitting}
              />
            ) : (
              <>
                <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark mb-2">
                  ★ Admin Sign-in
                </div>
                <h1 className="font-display text-3xl font-bold text-brand-brown-darker">
                  Sign in to <span className="display-em">your console</span>
                </h1>
                <p className="text-sm text-brand-brown-light mt-2">
                  Use your Jaikalki admin credentials.
                </p>

                <form
                  onSubmit={form.handleSubmit(onSubmit)}
                  className="mt-8 space-y-5"
                  noValidate
                >
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      autoComplete="email"
                      placeholder="admin@jaikalki.com"
                      aria-invalid={!!form.formState.errors.email}
                      {...form.register("email")}
                    />
                    {form.formState.errors.email && (
                      <p className="text-xs text-error">
                        {form.formState.errors.email.message}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        autoComplete="current-password"
                        placeholder="••••••••"
                        aria-invalid={!!form.formState.errors.password}
                        {...form.register("password")}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((v) => !v)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-brown-light hover:text-brand-brown-darker"
                        aria-label={showPassword ? "Hide password" : "Show password"}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4" />
                        ) : (
                          <Eye className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                    {form.formState.errors.password && (
                      <p className="text-xs text-error">
                        {form.formState.errors.password.message}
                      </p>
                    )}
                  </div>

                  <label className="flex items-center gap-2 text-xs font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                    <input
                      type="checkbox"
                      className="accent-brand-gold-dark"
                      {...form.register("rememberMe")}
                    />
                    Remember me
                  </label>

                  <Button
                    type="submit"
                    variant="default"
                    size="lg"
                    className="w-full"
                    disabled={submitting}
                  >
                    {submitting ? <Spinner /> : "Continue"}
                  </Button>

                  <div className="text-center text-xs font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                    <a
                      href="/forgot"
                      className="hover:text-brand-gold-dark"
                    >
                      Forgot password?
                    </a>
                  </div>
                </form>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MfaPrompt({
  onCancel,
  onSubmit,
  submitting,
}: {
  onCancel: () => void;
  onSubmit: (code: string) => Promise<void>;
  submitting: boolean;
}) {
  const [code, setCode] = useState("");

  return (
    <>
      <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark mb-2">
        ★ Two-factor required
      </div>
      <h1 className="font-display text-3xl font-bold text-brand-brown-darker">
        Enter your <span className="display-em">6-digit code</span>
      </h1>
      <p className="text-sm text-brand-brown-light mt-2">
        Open your authenticator app and enter the current code.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (code.length === 6) onSubmit(code);
        }}
        className="mt-8 space-y-5"
      >
        <div className="space-y-2">
          <Label htmlFor="mfa">MFA Code</Label>
          <Input
            id="mfa"
            inputMode="numeric"
            pattern="\d{6}"
            maxLength={6}
            autoFocus
            autoComplete="one-time-code"
            placeholder="000000"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            className="tracking-[0.5em] text-center font-mono text-lg"
          />
        </div>
        <Button
          type="submit"
          variant="default"
          size="lg"
          className="w-full"
          disabled={submitting || code.length !== 6}
        >
          {submitting ? <Spinner /> : "Verify"}
        </Button>
        <Button
          type="button"
          variant="ghost"
          className="w-full"
          onClick={onCancel}
        >
          Cancel
        </Button>
      </form>
    </>
  );
}
