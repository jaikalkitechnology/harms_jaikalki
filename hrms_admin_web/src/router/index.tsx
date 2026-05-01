import { createBrowserRouter, Navigate } from "react-router-dom";
import { AdminLayout } from "@/components/layouts/AdminLayout";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import LoginPage from "@/features/auth/LoginPage";
import UnauthorizedPage from "@/features/auth/UnauthorizedPage";
import DashboardPage from "@/features/dashboard/DashboardPage";
import PlaceholderPage from "@/features/dashboard/PlaceholderPage";
import EmployeesListPage from "@/features/employees/EmployeesListPage";
import EmployeeDetailPage from "@/features/employees/EmployeeDetailPage";
import EmployeeCreatePage from "@/features/employees/EmployeeCreatePage";
import SalaryTemplatesPage from "@/features/salary-templates/SalaryTemplatesPage";
import InternExpensesPage from "@/features/intern-expenses/InternExpensesPage";
import AttendancePage from "@/features/attendance/AttendancePage";
import LeaveApprovalsPage from "@/features/leaves/LeaveApprovalsPage";
import HolidaysPage from "@/features/holidays/HolidaysPage";
import ApprovalsInboxPage from "@/features/approvals/ApprovalsInboxPage";
import DwpTeamPage from "@/features/dwp/DwpTeamPage";
import PayrollRunsPage from "@/features/payroll/PayrollRunsPage";
import ReimbursementsPage from "@/features/payroll/ReimbursementsPage";
import JusticeInboxPage from "@/features/justice/JusticeInboxPage";
import JusticeDetailPage from "@/features/justice/JusticeDetailPage";
import IccPage from "@/features/justice/IccPage";
import CustomersPage from "@/features/field/CustomersPage";
import FieldJobsPage from "@/features/field/FieldJobsPage";
import LiveMapPage from "@/features/field/LiveMapPage";
import LeadsPage from "@/features/sales/LeadsPage";
import PipelinePage from "@/features/sales/PipelinePage";
import SalesTargetsPage from "@/features/sales/SalesTargetsPage";
import VerificationQueuePage from "@/features/verification/VerificationQueuePage";
import VerificationAuditPage from "@/features/verification/VerificationAuditPage";
import VerificationTemplatesPage from "@/features/verification/VerificationTemplatesPage";
import CoursesPage from "@/features/lms/CoursesPage";
import LeaderboardPage from "@/features/lms/LeaderboardPage";

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
      { path: "employees", element: <EmployeesListPage /> },
      {
        path: "employees/new",
        element: (
          <ProtectedRoute requirePermission="employee.create">
            <EmployeeCreatePage />
          </ProtectedRoute>
        ),
      },
      { path: "employees/:id", element: <EmployeeDetailPage /> },
      { path: "salary-templates", element: <SalaryTemplatesPage /> },
      { path: "intern-expenses", element: <InternExpensesPage /> },
      {
        path: "departments",
        element: (
          <PlaceholderPage
            phase="★ Phase 2"
            title="Departments"
            description="Department CRUD UI lands alongside Phase 4.5; for now manage via /api/v1/departments."
          />
        ),
      },
      {
        path: "designations",
        element: (
          <PlaceholderPage
            phase="★ Phase 2"
            title="Designations"
            description="Designation CRUD UI lands alongside Phase 4.5; for now manage via /api/v1/designations."
          />
        ),
      },
      { path: "holidays", element: <HolidaysPage /> },
      {
        path: "shifts",
        element: (
          <PlaceholderPage
            phase="★ Phase 3"
            title="Shifts"
            description="Shift CRUD UI lands in Phase 5; backend supports it via /api/v1 already."
          />
        ),
      },
      { path: "attendance", element: <AttendancePage /> },
      { path: "leaves", element: <LeaveApprovalsPage /> },
      { path: "approvals", element: <ApprovalsInboxPage /> },
      { path: "dwp", element: <DwpTeamPage /> },
      {
        path: "payroll",
        element: (
          <ProtectedRoute requirePermission="payroll.run">
            <PayrollRunsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "reimbursements",
        element: (
          <ProtectedRoute requirePermission="approval.act">
            <ReimbursementsPage />
          </ProtectedRoute>
        ),
      },
      { path: "justice", element: <JusticeInboxPage /> },
      { path: "justice/:id", element: <JusticeDetailPage /> },
      { path: "icc", element: <IccPage /> },
      { path: "field/customers", element: <CustomersPage /> },
      { path: "field/jobs", element: <FieldJobsPage /> },
      { path: "field/live-map", element: <LiveMapPage /> },
      { path: "sales/leads", element: <LeadsPage /> },
      { path: "sales/pipeline", element: <PipelinePage /> },
      { path: "sales/targets", element: <SalesTargetsPage /> },
      { path: "verification", element: <VerificationQueuePage /> },
      { path: "verification/audit", element: <VerificationAuditPage /> },
      { path: "verification/templates", element: <VerificationTemplatesPage /> },
      { path: "lms/courses", element: <CoursesPage /> },
      { path: "lms/leaderboard", element: <LeaderboardPage /> },
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
