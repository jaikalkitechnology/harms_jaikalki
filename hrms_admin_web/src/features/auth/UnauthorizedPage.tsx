import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth";
import { ROLE_LABEL, type Role } from "@/lib/constants";

export default function UnauthorizedPage() {
  const user = useAuthStore((s) => s.user);
  const role = useAuthStore((s) => s.role);
  const roles = useAuthStore((s) => s.roles);
  const permissions = useAuthStore((s) => s.permissions);

  return (
    <div className="min-h-screen grid place-items-center px-6 bg-surface-cream">
      <div className="max-w-xl text-center">
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-error">
          ✖ 403 — Forbidden
        </div>
        <h1 className="mt-2 font-display text-3xl md:text-4xl font-bold text-brand-brown-darker">
          You don't have <span className="display-em">access</span>
        </h1>
        <p className="mt-3 text-brand-brown-light text-sm">
          This page is gated. The pages you can use are listed in the sidebar
          on your dashboard — any link missing there isn't available to your
          role.
        </p>

        {user && (
          <div className="mt-6 mx-auto max-w-md text-left bg-card border border-brand-brown-100 rounded-xl p-4 space-y-3">
            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-0.5">
                Signed in as
              </div>
              <div className="text-sm font-medium text-brand-brown-darker">
                {user.full_name || user.email}
              </div>
              <div className="text-xs text-brand-brown-light">{user.email}</div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-0.5">
                Roles
              </div>
              <div className="flex flex-wrap gap-1.5">
                {roles.length === 0 && (
                  <span className="text-xs text-brand-brown-light">
                    No roles assigned
                  </span>
                )}
                {roles.map((r) => (
                  <span
                    key={r}
                    className={`text-xs px-2 py-0.5 rounded ${
                      r === role
                        ? "bg-brand-gold/20 text-brand-brown-darker"
                        : "bg-brand-brown-50 text-brand-brown-darker"
                    }`}
                  >
                    {ROLE_LABEL[r as Role] ?? r}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <div className="text-[10px] font-mono uppercase tracking-[0.2em] text-brand-brown-light mb-0.5">
                Permissions ({permissions.length})
              </div>
              <div className="flex flex-wrap gap-1">
                {permissions.length === 0 && (
                  <span className="text-xs text-brand-brown-light">none</span>
                )}
                {permissions.slice(0, 12).map((p) => (
                  <code
                    key={p}
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-brand-brown-50 text-brand-brown-darker"
                  >
                    {p}
                  </code>
                ))}
                {permissions.length > 12 && (
                  <span className="text-[10px] text-brand-brown-light self-center">
                    +{permissions.length - 12} more
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="mt-6 flex gap-2 justify-center">
          <Button asChild>
            <Link to="/dashboard">Back to dashboard</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/settings">Account settings</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
