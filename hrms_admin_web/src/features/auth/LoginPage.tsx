import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Logo } from "@/components/shared/Logo";
import { COMPANY_NAME } from "@/lib/constants";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Phase 1.5 will wire real auth via /api/admin/auth/login.
    navigate("/dashboard");
  }

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left — branding */}
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
          v0.1 · Phase 0 · Foundation
        </div>
      </div>

      {/* Right — form */}
      <div className="flex items-center justify-center p-8 bg-surface-cream">
        <Card className="w-full max-w-md">
          <CardContent className="pt-8">
            <div className="lg:hidden mb-6 flex justify-center">
              <Logo variant="horizontal-light" className="h-12 w-auto" />
            </div>

            <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark mb-2">
              ★ Admin Sign-in
            </div>
            <h1 className="font-display text-3xl font-bold text-brand-brown-darker">
              Sign in to <span className="display-em">your console</span>
            </h1>
            <p className="text-sm text-brand-brown-light mt-2">
              Use your Jaikalki admin credentials.
            </p>

            <form onSubmit={handleSubmit} className="mt-8 space-y-5">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@jaikalki.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>

              <Button type="submit" variant="default" size="lg" className="w-full">
                Continue
              </Button>

              <div className="text-center text-xs font-mono uppercase tracking-[0.2em] text-brand-brown-light">
                <Link to="/forgot" className="hover:text-brand-gold-dark">
                  Forgot password?
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
