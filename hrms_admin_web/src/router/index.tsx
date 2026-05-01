import { createBrowserRouter, Navigate } from "react-router-dom";
import { AdminLayout } from "@/components/layouts/AdminLayout";
import LoginPage from "@/features/auth/LoginPage";
import DashboardPage from "@/features/dashboard/DashboardPage";
import PlaceholderPage from "@/features/dashboard/PlaceholderPage";

export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/dashboard" replace /> },
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <AdminLayout />,
    children: [
      { path: "dashboard", element: <DashboardPage /> },
      {
        path: "employees",
        element: (
          <PlaceholderPage
            phase="★ Phase 2"
            title="Employee Master"
            description="Employee directory, profiles, documents, and Jaikalki-specific categories (Intern / Trainee / Permanent / Contract) ship in Phase 2."
          />
        ),
      },
      {
        path: "attendance",
        element: (
          <PlaceholderPage
            phase="★ Phase 3"
            title="Attendance & Leave"
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
          <PlaceholderPage
            phase="★ Phase 7"
            title="Payroll & Offer Letters"
            description="Salary structures, payslips, and the Pooja-template offer letter generator ship in Phase 7."
          />
        ),
      },
      {
        path: "super-admin",
        element: (
          <PlaceholderPage
            phase="★ Phase 4.5"
            title="Super Admin"
            description="System config, role/permission editor, and module toggles ship in Phase 4.5."
          />
        ),
      },
      {
        path: "settings",
        element: (
          <PlaceholderPage
            phase="★ Foundation"
            title="Settings"
            description="Account & company settings will be wired up alongside auth in Phase 1.5."
          />
        ),
      },
    ],
  },
]);
