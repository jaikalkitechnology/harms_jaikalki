import { Navigate, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import type { ReactNode } from "react";
import type { Role } from "@/lib/constants";

interface Props {
  children: ReactNode;
  requireRole?: Role | Role[];
  requirePermission?: string;
}

export function ProtectedRoute({
  children,
  requireRole,
  requirePermission,
}: Props) {
  const isLoading = useAuthStore((s) => s.isLoading);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const hasAnyRole = useAuthStore((s) => s.hasAnyRole);
  const location = useLocation();

  if (isLoading) return <LoadingScreen />;

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }

  if (requireRole) {
    const roles = Array.isArray(requireRole) ? requireRole : [requireRole];
    if (!hasAnyRole(roles)) {
      return <Navigate to="/unauthorized" replace />;
    }
  }

  if (requirePermission && !hasPermission(requirePermission)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <>{children}</>;
}
