import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

export default function UnauthorizedPage() {
  return (
    <div className="min-h-screen grid place-items-center px-6 bg-surface-cream">
      <div className="max-w-md text-center">
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-error">
          ✖ 403 — Forbidden
        </div>
        <h1 className="mt-2 font-display text-4xl font-bold text-brand-brown-darker">
          You don't have <span className="display-em">access</span>
        </h1>
        <p className="mt-3 text-brand-brown-light text-sm">
          This page is reserved for users with a higher privilege level.
          Contact your administrator if you believe this is a mistake.
        </p>
        <div className="mt-6">
          <Button asChild>
            <Link to="/dashboard">Back to dashboard</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
