import { createBrowserRouter, Navigate } from "react-router-dom";
import { AdminLayout } from "@/components/layouts/AdminLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import LoginPage from "@/features/auth/LoginPage";
import UnauthorizedPage from "@/features/auth/UnauthorizedPage";
import DashboardPage from "@/features/dashboard/DashboardPage";
import PlaceholderPage from "@/features/dashboard/PlaceholderPage";

export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/dashboard" replace /> },
  { path: "/login", element: <LoginPage /> },
  { path: "/unauthorized", element: <UnauthorizedPage /> },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AdminLayout />
      </ProtectedRoute>
    ),
    children: [
      { path: "dashboard", element: <DashboardPage /> },
      {
        path: "employees",
        element: (
          <ProtectedRoute requirePermission="employee.view.all">
            <PlaceholderPage
              phase="★ Phase 2"
              title="Employee Master"
              description="Employee directory, profiles, documents, and Jaikalki-specific categories (Intern / Trainee / Permanent / Contract) ship in Phase 2."
            />
          </ProtectedRoute>
        ),
      },
      {
        path: "departments",
        element: (
          <PlaceholderPage
            phase="★ Phase 2"
            title="Departments"
            description="Department directory ships with the employee master in Phase 2."
          />
        ),
      },
      {
        path: "designations",
        element: (
          <PlaceholderPage
            phase="★ Phase 2"
            title="Designations"
            description="Designation matrix (with Jaikalki L1-L5 levels) ships in Phase 2."
          />
        ),
      },
      {
        path: "holidays",
        element: (
          <PlaceholderPage
            phase="★ Phase 3"
            title="Holidays"
            description="Holiday calendar configuration ships with attendance in Phase 3."
          />
        ),
      },
      {
        path: "shifts",
        element: (
          <PlaceholderPage
            phase="★ Phase 3"
            title="Shifts"
            description="Shift policies and rotations ship with attendance in Phase 3."
          />
        ),
      },
      {
        path: "attendance",
        element: (
          <PlaceholderPage
            phase="★ Phase 3"
            title="Attendance"
            description="Geo-fenced check-in, shift policies, and leave workflows ship in Phase 3."
          />
        ),
      },
      {
        path: "approvals",
        element: (
          <PlaceholderPage
            phase="★ Phase 4"
            title="Universal Approvals"
            description="Multi-level approval engine across modules ships in Phase 4."
          />
        ),
      },
      {
        path: "payroll",
        element: (
          <ProtectedRoute requirePermission="payroll.run">
            <PlaceholderPage
              phase="★ Phase 7"
              title="Payroll & Offer Letters"
              description="Salary structures, payslips, and the Pooja-template offer letter generator ship in Phase 7."
            />
          </ProtectedRoute>
        ),
      },
      {
        path: "reports",
        element: (
          <PlaceholderPage
            phase="★ Phase 13"
            title="Reports"
            description="Cross-module reporting and exports ship in Phase 13."
          />
        ),
      },
      {
        path: "super-admin/*",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <PlaceholderPage
              phase="★ Phase 4.5"
              title="Super Admin"
              description="System config, role/permission editor, module toggles, audit logs, and branding ship in Phase 4.5."
            />
          </ProtectedRoute>
        ),
      },
      {
        path: "settings",
        element: (
          <PlaceholderPage
            phase="★ Foundation"
            title="Settings"
            description="Account & company settings will be expanded alongside Super Admin in Phase 4.5."
          />
        ),
      },
    ],
  },
  { path: "*", element: <Navigate to="/dashboard" replace /> },
]);
