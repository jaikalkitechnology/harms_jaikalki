import type { ReactNode } from "react";
import { useAuthStore } from "@/store/auth";
import type { Role } from "@/lib/constants";

interface Props {
  permission?: string;
  role?: Role | Role[];
  children: ReactNode;
  fallback?: ReactNode;
}

export function PermissionGate({
  permission,
  role,
  children,
  fallback = null,
}: Props) {
  const hasPermission = useAuthStore((s) => s.hasPermission);
  const hasAnyRole = useAuthStore((s) => s.hasAnyRole);

  if (permission && !hasPermission(permission)) return <>{fallback}</>;
  if (role) {
    const roles = Array.isArray(role) ? role : [role];
    if (!hasAnyRole(roles)) return <>{fallback}</>;
  }
  return <>{children}</>;
}
