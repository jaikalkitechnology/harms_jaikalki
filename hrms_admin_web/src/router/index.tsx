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
import AttendanceCalendarPage from "@/features/attendance/AttendanceCalendarPage";
import AttendanceUploadPage from "@/features/attendance/AttendanceUploadPage";
import LeaveApprovalsPage from "@/features/leaves/LeaveApprovalsPage";
import HolidaysPage from "@/features/holidays/HolidaysPage";
import LettersPage from "@/features/letters/LettersPage";
import ApprovalsInboxPage from "@/features/approvals/ApprovalsInboxPage";
import DwpTeamPage from "@/features/dwp/DwpTeamPage";
import AdminDwpPage from "@/features/dwp/AdminDwpPage";
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
import CourseDetailPage from "@/features/lms/CourseDetailPage";
import LeaderboardPage from "@/features/lms/LeaderboardPage";
import QuestionBankPage from "@/features/exam/QuestionBankPage";
import ExamsPage from "@/features/exam/ExamsPage";
import CertificateVerifyPage from "@/features/exam/CertificateVerifyPage";
import CertificatesPage from "@/features/exam/CertificatesPage";
import TrainersPage from "@/features/trainer/TrainersPage";
import SessionsPage from "@/features/trainer/SessionsPage";
import DirectorDashboardPage from "@/features/reports/DirectorDashboardPage";
import SavedReportsPage from "@/features/reports/SavedReportsPage";
import ExportReportPage from "@/features/reports/ExportReportPage";
import AssetsPage from "@/features/polish/AssetsPage";
import VisitorsPage from "@/features/polish/VisitorsPage";
import JobPostingsPage from "@/features/polish/JobPostingsPage";
import NotificationsPage from "@/features/launch/NotificationsPage";
import AuditLogPage from "@/features/launch/AuditLogPage";
import ResignationsPage from "@/features/launch/ResignationsPage";
import SalaryRevisionsPage from "@/features/compensation/SalaryRevisionsPage";
import SystemConfigPage from "@/features/super-admin/SystemConfigPage";
import PermissionCatalogPage from "@/features/super-admin/PermissionCatalogPage";
import RoleBuilderPage from "@/features/super-admin/RoleBuilderPage";
import AdminUsersPage from "@/features/super-admin/AdminUsersPage";
import ModulesPage from "@/features/super-admin/ModulesPage";
import SuperAuditLogsPage from "@/features/super-admin/SuperAuditLogsPage";
import BrandingPage from "@/features/super-admin/BrandingPage";
import BackupsPage from "@/features/super-admin/BackupsPage";
import ApiKeysPage from "@/features/super-admin/ApiKeysPage";
import EmailTemplatesPage from "@/features/super-admin/EmailTemplatesPage";
import DepartmentsPage from "@/features/organization/DepartmentsPage";
import DesignationsPage from "@/features/organization/DesignationsPage";
import ShiftsPage from "@/features/organization/ShiftsPage";
import SettingsPage from "@/features/settings/SettingsPage";

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
      { path: "departments", element: <DepartmentsPage /> },
      { path: "designations", element: <DesignationsPage /> },
      { path: "holidays", element: <HolidaysPage /> },
      { path: "letters", element: <LettersPage /> },
      { path: "shifts", element: <ShiftsPage /> },
      { path: "attendance", element: <AttendancePage /> },
      {
        path: "attendance/calendar",
        element: (
          <ProtectedRoute requirePermission="attendance.view.all">
            <AttendanceCalendarPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "attendance/upload",
        element: (
          <ProtectedRoute requirePermission="attendance.view.all">
            <AttendanceUploadPage />
          </ProtectedRoute>
        ),
      },
      { path: "leaves", element: <LeaveApprovalsPage /> },
      { path: "approvals", element: <ApprovalsInboxPage /> },
      { path: "dwp", element: <DwpTeamPage /> },
      {
        path: "dwp/admin",
        element: (
          <ProtectedRoute requirePermission="approval.act">
            <AdminDwpPage />
          </ProtectedRoute>
        ),
      },
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
      { path: "lms/courses/:id", element: <CourseDetailPage /> },
      { path: "lms/leaderboard", element: <LeaderboardPage /> },
      { path: "exams/questions", element: <QuestionBankPage /> },
      { path: "exams", element: <ExamsPage /> },
      { path: "exams/verify", element: <CertificateVerifyPage /> },
      { path: "exams/certificates", element: <CertificatesPage /> },
      { path: "trainers", element: <TrainersPage /> },
      { path: "trainers/sessions", element: <SessionsPage /> },
      { path: "reports/dashboard", element: <DirectorDashboardPage /> },
      { path: "reports/saved", element: <SavedReportsPage /> },
      {
        path: "reports/export",
        element: (
          <ProtectedRoute requirePermission="report.view.all">
            <ExportReportPage />
          </ProtectedRoute>
        ),
      },
      { path: "assets", element: <AssetsPage /> },
      { path: "visitors", element: <VisitorsPage /> },
      { path: "jobs", element: <JobPostingsPage /> },
      { path: "notifications", element: <NotificationsPage /> },
      { path: "audit", element: <AuditLogPage /> },
      { path: "resignations", element: <ResignationsPage /> },
      { path: "compensation", element: <SalaryRevisionsPage /> },
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
        path: "super-admin/system",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <SystemConfigPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "super-admin/permissions",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <PermissionCatalogPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "super-admin/roles",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <RoleBuilderPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "super-admin/admins",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <AdminUsersPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "super-admin/modules",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <ModulesPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "super-admin/audit",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <SuperAuditLogsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "super-admin/branding",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <BrandingPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "super-admin/backups",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <BackupsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "super-admin/api-keys",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <ApiKeysPage />
          </ProtectedRoute>
        ),
      },
      {
        path: "super-admin/email-templates",
        element: (
          <ProtectedRoute requireRole="super_admin">
            <EmailTemplatesPage />
          </ProtectedRoute>
        ),
      },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/dashboard" replace /> },
]);
