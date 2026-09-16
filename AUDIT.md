# Jaikalki HRMS — Deep Audit

_Prepared 2026-09-16. Covers `hrms_backend` (FastAPI), `hrms_admin_web` (React) and `hrms_mobile` (Flutter)._

---

## Executive Summary

The platform is broadly feature-complete for a mid-size Indian HRMS: auth, employees, attendance, leaves, payroll, DWP, sales, LMS, exams, trainers, performance, letters, justice, verification and super-admin are all in place across all three surfaces. Delivery quality is good enough for pilot deployment, but the codebase has classic post-MVP debt: heavy runtime `ALTER TABLE` startup (no clean Alembic migration for recent columns), stubbed super-admin MFA, no meaningful test coverage on any tier, no route-level code-splitting on the admin web, and a mobile app with ≥ 674 hard-coded English strings despite Hindi ARB scaffolding. Nothing on this list is a blocker; most items are 1–3 day fixes each.

The single most impactful piece of work: **route-level code splitting on the admin web** (drops first-paint by ~2 MB gzipped) and **squashing `_PENDING_COLUMNS` into one Alembic revision** on the backend (removes race and startup drift).

---

## 1. Backend — `hrms_backend/`

FastAPI + async SQLAlchemy 2 + Pydantic v2. Router entry at `app/api/router.py`.

### 1.1 What's Done

| Domain | Models | Router | Status |
|---|---|---|---|
| Auth | `User`, `Role`, `Permission`, `RolePermission`, `UserRole`, `RefreshToken`, `PasswordResetOtp`, `MfaBackupCode` | `api/v1/auth.py` + `api/admin/auth.py` (cookie login, CSRF header) | ✅ |
| Employees + profile | `Employee`, `EmployeeAddress`, `EmployeeBankDetails`, `EmergencyContact`, `EmployeeNominee`, `FamilyMember`, `EmployeePassport`, `EmployeeDocument`, `EmployeeCategory`, `EmployeeProbation`, `InternTravelExpense`, `SalaryTemplate`, `AttendanceCycle` | `employees.py`, `employee_profile.py`, `intern_expenses.py` | ✅ |
| Organization | `Department` (JSON `enabled_modules`, `leave_approver_user_ids`), `Designation`, `Shift`, `EmployeeShift` | `organization.py` | ✅ |
| Attendance | `Attendance`, `AttendanceRegularization` | `attendance.py` (self-mark, CSV upload/template/export, calendar, summary, regularization) | ✅ back-date windows on `Employee.backdate_from/to` |
| Leaves | `LeaveType`, `LeaveBalance`, `LeaveAdjustment`, `LeaveRequest`, `CompOff`, `Holiday`, `EarnedLeaveAccrual` | `leaves.py` + `services/leave_policy.py` | ✅ approver union (manager reportees ∪ HR/Admin/Director see-all ∪ mapped-department members) in `employee_service.leave_visible_employee_ids:118-139`. Pending-as-paid + absence-sandwich policies live in `payroll_attendance.py:113-124, 277-304`. |
| Payroll | `PayrollRun`, `Payslip`, `Reimbursement`, `BankFileExport`, `InvestmentDeclaration`, `GeneratedDocument` | `payroll.py` (disburse, PF ECR, bank CSV, mobile disbursed-gate at `payroll.py:181-213`) | ✅ |
| DWP | `DwpTemplate`, `DwpTemplateField`, `DwpSubmission`, `DwpSubmissionField`, `DwpComment`, `DwpTag`, `DwpReminderSetting` | `dwp.py` | ✅ |
| Field force | `FieldEmployee`, `Customer`, `Visit`, `VisitPhoto`, `FieldJob`, `FieldExpense`, `LocationTrack` | `field_force.py` | ✅ |
| Sales | leads / pipeline / targets / products / quotes | `sales.py` + `services/quote_pdf.py` | ✅ |
| Verification | queue + PDF report | `verification.py` + `services/verification_pdf.py` | ✅ |
| LMS | `Course`, `CourseModule`, `CourseLesson`, `CourseEnrollment`, `Badge` | `lms.py` | ✅ |
| Exam | `Exam`, `ExamQuestion`, `QuestionOption`, `ExamAttempt`, `AttemptAnswer`, `Certificate`, `QuestionBank` | `exam.py` | ✅ |
| Trainer | sessions + trainers | `trainer.py` | ✅ |
| Performance | goals, feedback, 1-on-1, director dashboard | `performance.py` | ✅ |
| Polish | jobs, visitors, assets, resignations | `polish.py` | ✅ |
| Justice | complaints, ICC, POSH annual, retaliation flags | `justice.py` | ✅ |
| Reports | `reports.py` + `services/reports_service.py` | ✅ |
| Launch | audit, notifications, device tokens, resignations | `launch.py` | ✅ |
| Letter templates | `LetterTemplate` + renderer with Jaikalki letterhead (icon + wordmark + CIN/GST/regd/watermark) | `letter_templates.py` + `services/letter_template_service.py` | ✅ |
| Documents | offer / confirmation / experience letters, payslip PDF | `documents.py` + `services/jaikalki_documents.py` | ✅ |
| Super Admin | system config, roles, admin users, modules, audit logs, branding, backups, API keys, email templates, geo-fence | `admin/super_admin.py` | ✅ |

### 1.2 Improvements Required

**Correctness**
- `admin/auth.py:152-162` — **super-admin MFA accepts the static "000000" until 2027-01-01** (silent time-bomb). Replace with the real `mfa_service.verify_mfa_code_for_login`.
- `employee_service.org_chart:582-584` — iterates `e.designation.name` / `e.department.name` without eager loads → `MissingGreenlet` in async or hidden sync queries. Add `selectinload`.
- `leave_service.cancel_leave` never mirrors to `approval_engine` — cancelled leaves linger in the universal inbox.
- `payroll.approve_reimbursement` / `reject_reimbursement` don't mirror to the approval engine (`payroll.py:457-508`) — inbox drift.
- `attendance.upsert_by_date:407` and `update_attendance:301-325` — no `check_out > check_in` validation → negative `total_minutes` possible.
- `payroll.py:582-626` (bank file upload) swallows every upload exception and persists `local://…` URLs silently.
- `services/leave_policy.recompute_earned_leaves:242-259` — 2 counts per employee in a Python loop; group-by SQL will fix N+1.
- `cancel_leave:318-322` stamps `approved_at` without `approver_id` — inconsistent audit trail.
- Startup drift: `AuditMiddleware:172-188` commits inside the request path. Move to `BackgroundTasks`.

**Security**
- Cookie `SameSite=lax` hard-coded (`admin/auth.py:40`) — cross-origin SPA silently loses cookies. Set `SameSite=None; Secure` when `settings.CROSS_ORIGIN=True`.
- CSRF cookie `httponly=False` **plus no `SameSite=strict`** (`admin/auth.py:57-63`) — XSS on admin domain would exfiltrate the CSRF token. Consider signed double-submit + strict.
- Password-reset OTP is 6 digits with 5 attempts (`password_reset_service.py:48`). Weak against distributed brute force. Move to 8 digits or alphanumeric + per-IP throttle.
- `password_reset_service.py:83-84` returns "Account not found" — enumerates emails and contradicts the always-202 response elsewhere.
- Rate limit is IP-only in-memory (`core/middleware.py:52-114`) — same-NAT bypass + lost on restart. Move to Redis, add per-email counters, extend to `/mfa/verify` and `/reset-password`.
- Seed scripts ship real bcrypt-hashed weak passwords (`scripts/seed_employees.py:330` `changeme123`, `seed_field_force.py:96` `Password@123`). Guard with `if settings.ENVIRONMENT != "production": raise`.
- `employee_service.create_employee:226` seeds `changeme123` in the **real prod path**, not just seed.
- Upload validation gaps — `attendance.py:73-83` selfie has no size cap / content-type allowlist; `payroll.py:592-608` bank-file uploader same.
- `admin/super_admin.trigger_backup:718-737` shells out to a script whose path derives from `HRMS_BACKUP_DIR` env; check the path is inside an allowlist.
- PII in error messages (names / amounts in `payroll_service`, `leave_service`).
- `X-Payslip-Filter` debug header is shipped in production (`payroll.py:187`) — remove.

**Consistency**
- Mixed permission gating on leaves (`leaves.py:139` uses `require_permission("leave.approve.team")`, `leaves.py:229` uses custom `require_leave_approver`). Pick one taxonomy. Reimbursements use `approval.act`, holidays use `admin.users.manage`, offer letter uses `employee.create`, confirmation letter uses `employee.update` — no canonical rule.
- Status enums are strings everywhere except `Attendance.status` (DB `Enum` at `models/attendance.py:85`). Extract shared `StrEnum` classes into `app/core/enums.py`.
- Endpoints missing `response_model=`: `dashboard.py` (1), `employee_profile.py` (17), `organization.py`, `employees.py` (~16). Some return raw dicts (`attendance.py:430`).

**Migration & schema hygiene**
- **~50 runtime `ALTER TABLE` calls in `database._PENDING_COLUMNS:61-162`** — race on read-replicas, hides drift, and swallows FK failures (`database.py:210`). Squash into one Alembic revision and retire `sync_columns`.
- Missing FKs: `payroll_runs.disbursed_by` → `users(id)`; `Department.leave_approver_user_ids` should be a bridge table `department_leave_approvers(department_id, user_id)`; `Department.enabled_modules` same story.
- No composite indexes anywhere (`grep -r "Index(" models/` returns 0). See § 1.4 for the concrete list.

**Testing gaps**
- 20 files under `tests/`, none for letter_templates, organization, documents, dashboard, password_reset, mfa, super_admin, intern_expenses, notification_service. No property tests for payroll math. No CSRF-specific test.

### 1.3 New Features to Add

1. **Expense claims workflow** — separate from `Reimbursement`: trip advance → expense report → settlement, multi-currency, mileage.
2. **360 feedback anonymisation** — configurable levels; hide responder identity based on role.
3. **LMS quiz auto-grading** — models exist; add a grader that closes `ExamAttempt`, awards `Badge`, streams into learning stats.
4. **Offer-acceptance signature capture** — persist signed image + timestamp + IP under `GeneratedDocument`; `POST /payroll/offer-letter/{id}/accept`.
5. **E-signature on generated letters** — extend `render_letter_pdf` to accept signature PNG + signer coords.
6. **WhatsApp / email adapters** — `notification_service` is scaffolded; wire Gupshup/MSG91/Twilio + `EmailTemplate` mapping.
7. **Self-service address change with HR approval** — mirror `apply_leave` → `approval_engine.submit_for_approval("employee.address_change")`.
8. **Digital ID card** — QR-signed PDF/PNG per employee.
9. **Org chart endpoint** — service is at `employee_service.org_chart:573`, just needs a route.
10. **Biometric device sync** — `POST /attendance/biometric-webhook` for ZKTeco / Matrix / Realtime bulk pushes.
11. **Background verification integration** — AuthBridge / IDfy adapters.
12. **GST invoice generation** for sales quotes (extend `quote_pdf.py` with GSTIN/HSN/SAC/CGST/SGST/IGST).
13. **Letter template versioning + audit log** — `LetterTemplateVersion` + FK from `GeneratedDocument.template_version_id`.
14. **Per-employee document vault** — categorised buckets (Form-16, ITR proof, payslips) with retention + signed URLs.
15. **EPFO / ESIC filing** — extend PF challan to signed EPFO ECR upload; add ESIC MC push.

### 1.4 Optimizations

**Eager-loading fixes (N+1 killers)**
- `employee_service.org_chart:573-595` — add `selectinload(Employee.designation, Designation.department)`.
- `leaves.team_calendar:301-341` — collapse 3 queries into 1 with `selectinload(LeaveRequest.leave_type)`.
- `payroll.export_run_csv` and `export_pf_challan:118-151` — restrict employee fetch to `{p.employee_id for p in run.payslips}` (already done in bank export at line 599).
- `super_admin.list_admins:402-416` — `_user_role_codes` in per-user loop.
- `super_admin.list_roles:261-267` — `_role_with_permissions` per row.
- `attendance._synthesize_leave_rows` — pre-load `LeaveType` names once.

**DB indexes to add** (all missing today):
- `attendance(employee_id, date)` composite (currently two separate indexes + unique).
- `leave_requests(employee_id, status)`, `leave_requests(status, applied_at)`, `leave_requests(from_date, to_date)`.
- `payslips(payroll_run_id, employee_id)`, `payslips(employee_id, year, month)`.
- `reimbursements(employee_id, status)`, `reimbursements(status, created_at)`.
- `attendance_regularizations(status, created_at)`.
- `approvals(status, request_type, created_at)`.
- `audit_logs(actor_user_id, occurred_at)`, `audit_logs(action, occurred_at)`.
- `notifications(user_id, is_read)`.
- `dwp_submissions(employee_id, submission_date)`.
- `sales_leads(assigned_to, status)`, `visits(field_employee_id, visit_date)`.
- `password_reset_otps(email, consumed_at, created_at)`.

**Caching**
- `Cache-Control: private, max-age=60` on `/leaves/types`, `/leaves/holidays`, `/organization/departments`, `/lms/courses`, `/admin/modules`, `/admin/branding`, `/admin/permissions/categories`, `/admin/office-location`.
- **ETag on `GET /employees/{id}`** keyed by `updated_at`.
- Redis-cached counters (`pending_leaves_by_approver`, `open_approvals_by_module`) with 60 s TTL for the sidebar badges.

**Heavy work off-request**
- Push `render_payslip_pdf`, `generate_offer_letter`, `render_letter_pdf`, `quote_pdf` into `BackgroundTasks` / Arq (workers scaffolded at `app/workers/`); cache PDFs in storage keyed by `(doc_type, employee_id, hash)`.
- Batch `approval_engine.submit_for_approval` in bulk-import flows (attendance CSV / bulk employees).
- Retire per-request `AuditMiddleware` DB commit; drain a queue from a worker.

---

## 2. Admin Web — `hrms_admin_web/`

React 18 + TypeScript + Vite + Tailwind + React Router 6 + zustand + TanStack Query 5. Axios client with CSRF + refresh interceptor.

### 2.1 What's Done

**Workspace** — Dashboard, Employees list + create + detail, Salary templates, Intern expenses.
**Operations** — Departments (+ mobile-modules + leave-approvers mapping), Designations, Holidays, **Letters CRUD + template editor** (new), Shifts, Attendance / calendar / upload, Leaves approvals, Approvals inbox, DWP team + admin.
**Payroll** — Runs (finalize / disburse / PF ECR / bank CSV / delete), Reimbursements, Compensation revisions.
**Sales** — Leads (930 L), Pipeline (thin — no DnD), Targets.
**Field** — Customers, Field jobs, Live map.
**Verification** — Queue, Audit, Templates.
**Learning** — LMS courses list + detail, Leaderboard, Question bank, Exams, Certificates + verify, Trainers, Sessions.
**Performance / Reports** — Director dashboard, Saved reports, Export report (CSV).
**Polish** — Assets, Visitors, Job postings, Notifications, Audit log, Resignations.
**Justice** — Inbox, detail, ICC.
**Super Admin** — System config, permission catalog, role builder, admin users, modules, audit logs, branding, backups, API keys, email templates.
**Auth** — Login + MFA + Forgot + Unauthorized. Recent fix in `src/lib/api/client.ts` + `src/store/auth.ts` (session-scoped `auth_active` flag) resolved the two-attempt sign-in.

### 2.2 Improvements Required

**Correctness / UX**
- `ProtectedRoute.tsx:43-45` — missing permission bounces silently to `/unauthorized`; no toast, no home-page fallback for viewers without `employee.view.all`.
- `EmployeesListPage.tsx:24-32` — filter changes don't debounce and race against `retry:1`.
- `LettersPage.tsx:49` — `LoadingScreen` blanks the whole page including the header on first load; use in-place skeleton.
- `PayrollRunsPage.tsx:94-97` — only invalidates its own two query keys; new-run detail can stay stale.
- Lookup queries (`["departments"]`, `["categories"]`) never invalidated when the lookups themselves change (`HolidaysPage.tsx`, `DesignationsPage.tsx`, `ShiftsPage.tsx`).
- Zod validation: only `LoginPage.tsx` uses it. Add to `EmployeeCreatePage.tsx`, `HolidaysPage.tsx`, `ShiftsPage.tsx`, `SalaryTemplatesPage.tsx`.

**Auth**
- `store/auth.ts:83-95` — `submitMfa` doesn't clear `pendingCredentials` on failure; a wrong code leaves creds in memory.
- `auth:unauthorized` broadcast fires even for optional widgets legitimately returning 401. Consider per-endpoint annotation instead of the global toggle.
- `checkAuth:109` toggles `isLoading: true` on every HMR reload — causes route flash.

**Accessibility**
- Only **8** `aria-label` occurrences in the entire tree; icon-only Edit/Delete/Close buttons across `EmployeeDetailPage`, `PayrollRunsPage`, `LettersPage` have no accessible name.
- **No dialog primitive** — every modal is a hand-rolled `<div>` overlay. No focus trap, no `role="dialog"`, no ESC handling. Add Radix `Dialog`, `Select`, `DropdownMenu`, `Tabs` to `components/ui/`.
- Colour-only status (`PayrollRunsPage.tsx:40-45`) — add icons + text badges.
- Custom `<select>` replacements without `role="listbox"` / arrow-key nav.

**Design-system inconsistency**
- 310 raw `<button>` occurrences across 60 files mix with `<Button variant=…>`. `ResignationsPage.tsx` alone has 8+ raw buttons.
- 743 palette-class hits across 68 files, many raw `bg-red-*` / `text-green-*` co-existing with brand tokens.
- Inline `style={{…}}` at `LoginPage.tsx:77-81`, `SalesTargetsPage.tsx`, `BrandingPage.tsx`.
- Duplicate `BadgeCheck` alias in `Sidebar.tsx:6,23`.

**PermissionGate coverage**
- Only **3** feature files import `PermissionGate` (`EmployeeDetailPage`, `EmployeesListPage`, `HolidaysPage`). Every write action in Departments / Shifts / Designations / Letters / Salary Templates / Sales / Verification / LMS / Exams / Trainers / DWP / Reimbursements / Reports / Compensation is UI-visible regardless of permission — router gates the page, not the buttons.

**File-size / structure**
- Files > 500 lines that should be split:
  - `EmployeeDetailPage.tsx` **2 110** (monolith — top priority)
  - `SettingsPage.tsx` 1 105
  - `EmployeeProfileExtras.tsx` 1 096
  - `AttendanceLeaveCard.tsx` 955
  - `LeadsPage.tsx` 930
  - `CertificatesPage.tsx` 874
  - Plus ~20 files in the 500–730 range.

**Loading / pagination / downloads**
- 63 files show "Loading" text; no shimmer skeletons anywhere.
- No pagination on employees, payslips, leaves, approvals, letters, audit logs.
- Every blob download (`PayrollRunsPage:47-61`, `ExportReportPage:104-108`, `AttendancePage:140-143`, `LettersDocsCard:53`, `SuperAuditLogsPage:56`) buffers full response into memory — can OOM the tab on large exports.

**Testing**
- **Zero tests.** No vitest/jest. Add at least smoke coverage for LoginPage, ProtectedRoute, `apiClient.401` refresh flow.

### 2.3 New Features to Add

1. **Bulk actions on employees** — activate/deactivate/reassign department (`employeesApi` already accepts `employee_ids[]`).
2. **Bulk payslip email** from a completed run.
3. **Filter chips + saved views** on the Employees list, backed by a zustand slice.
4. **Announcements board** driven by `launchApi`.
5. **Calendar view for shifts** with `react-big-calendar`.
6. **Drag-and-drop pipeline** using `dnd-kit` (`PipelinePage.tsx` is currently a 157-line stub).
7. **Letter template preview panel** in `LettersPage`.
8. **Letter generation audit log** ("who generated what for whom").
9. **Org chart tree** view.
10. **Kanban for approvals** (currently a table).
11. **Dark-mode toggle** (`useThemeStore` already exists in `store/theme.ts`, expose in `Header`).
12. **i18n scaffolding** with `react-i18next` (~30 000 LOC of hard-coded English).
13. **Download-as-Excel** on reports.
14. **Universal search palette (⌘K)** using `cmdk`.
15. **Embed payslip preview** inside `EmployeeDetailPage`.
16. **Quick-add employee wizard** on the dashboard.
17. **Offer-letter e-sign** flow.
18. **Activity timeline per employee** merging leaves, letters, salary revisions, docs.

### 2.4 Optimizations

- **Route-level code splitting** — `src/router/index.tsx:1-68` imports every page synchronously. Wrap each in `React.lazy` + `<Suspense fallback={<LoadingScreen />}>`. **Estimated saving: ~2 MB gzipped on first paint.**
- Query cache tuning (`App.tsx:12` sets `staleTime: 30s`): bump `["departments"]`, `["categories"]`, `["designations"]`, `["shifts"]`, `["holidays"]`, `["letter-placeholders"]` to 5–10 min.
- List virtualization on `EmployeesListPage`, `ApprovalsInboxPage`, `LeaveApprovalsPage`, `CertificatesPage`, `AuditLogPage` with `@tanstack/react-virtual`.
- Extract a shared `src/lib/download.ts` that streams via `response.data.stream()` for files > 5 MB.
- Replace raw `bg-red-*` / `text-green-*` with brand tokens (Tailwind purge stays lean).
- Prefer `<Link>` over `useNavigate` for row-to-detail so router prefetches.
- Enable `structuralSharing` + `placeholderData: keepPreviousData` on paginated queries.
- Scrub the one remaining `console.*` in `src/lib/sentry.ts:1`.

---

## 3. Mobile — `hrms_mobile/`

Flutter 3.22 / Dart 3.4, `flutter_bloc` + `get_it` + `go_router` + `dio`.

### 3.1 What's Done

Wiring: `buildRouter` in `lib/core/routing/app_router.dart:119` (~55 routes, redirect-based auth gate); DI in `lib/core/di/injection.dart`; Dio in `lib/core/network/dio_client.dart` with `AuthInterceptor` + queued `RefreshInterceptor` + `LoggingInterceptor`; theme forced dark (`lib/app.dart:53`); L10n scaffold `lib/l10n/app_l10n.dart` + `app_en.arb` / `app_hi.arb` (72 lines each); FCM + local notifications `lib/core/push/push_notifications_service.dart`.

| Feature | Pages / lines | Cubit or Bloc | Status |
|---|---|---|---|
| Auth | `login_page` + `login_form`, `biometric_button` | `auth_bloc.dart` (326 L) | ✅ login + biometric soft-logout (`auth_bloc.dart:267`) + change-password + forgot-password + MFA-setup |
| Profile | `profile_page.dart` (**1 177 L**) | FutureBuilder | ✅ statutory + nominee cards + password-change dialog delivered |
| Employees | list + detail | `employees_cubit`, `employee_detail_cubit` | ✅ |
| Attendance | home + calendar (**627 L**) | `attendance_cubit` (image_picker) | ✅ self-mark + selfie + calendar (leave / pending badges) |
| Leaves | home (389 L), manager inbox | `leaves_cubit` | ✅ apply / balances / inbox / decide |
| Approvals | generic inbox | `approvals_inbox_cubit` | ✅ |
| DWP | home + form | `dwp_cubit` | ✅ morning + EOD + streak + history |
| Payroll | home (445 L) | `payroll_cubit` | ✅ payslips list + PDF fetch + reimbursement claim (trusts server disbursed-gate) |
| Field / sales | field_home, live_map, visit; my_leads, new_lead, pipeline, targets | in-page state | ✅ |
| Verification | queue + form (565 L) | in-page | ✅ |
| Polish | book_room, my_assets, jobs | — | ✅ |
| LMS + Exam + Trainer | home, badges, course_detail, exam list + taking, my_certificates (439 L), trainer marketplace, sessions | — | ✅ |
| Performance | goals, feedback_inbox | — | ✅ |
| Reports | director_dashboard (501 L) | — | ✅ |
| Justice / Resignation / Internal jobs / Intern expenses | 4 justice pages + resignation + jobs + intern_expenses | intern_expenses_cubit | ✅ |
| Launch | notifications, mfa_setup, forgot_password | — | ✅ |
| Shell / More / Settings / Splash / Onboarding / Dashboard (779 L) / Visitors / Book room / My assets | + `more_menu_page` with dept module gating | dashboard_cubit, settings_cubit | ✅ |

### 3.2 Improvements Required

**Correctness**
- `PayrollHomePage` reuses the cubit correctly, but `submitReimbursement` (`payroll_cubit.dart:82`) re-calls `load()` which re-emits `loading` and hides the sheet abruptly. Emit an incremental update instead.
- `AttendanceCalendarPage:33` — no `mounted` guard around `setState` inside `RefreshIndicator` (line 77).
- `ProfilePage:42` — `setState` inside `_refresh` without `if (mounted)`; `_load()` at line 34 swallows all errors (401 vs 500 indistinguishable).
- `RefreshInterceptor._refreshing:35` — redundant with `QueuedInterceptor`; retry via `sl<Dio>()` re-runs the auth interceptor, so the token is attached twice.
- **Change-password should proactively revoke** — `auth_repository_impl.dart:63` never touches storage. Add `_storage.clearRefreshToken()` + `setBiometricEnabled(false)` on success.
- 15 list screens lack pull-to-refresh (`verification_queue_page`, `my_leads_page`, `manager_inbox_page`, `feedback_inbox_page`, …).
- 40 files still use `.withOpacity(...)` (97 hits) — deprecated in Flutter 3.27; migrate to `.withValues(alpha: …)`.
- `_BlocStream` in `app_router.dart:389` is never disposed (GoRouter outlives `MaterialApp`).

**Localisation**
- `app_hi.arb` is 72 lines — but the source has **≥ 674 raw `Text('…')` literals across 73 files** vs only 13 `AppL10n.of(context)` sites. Extract all strings to ARB.

**Offline / errors**
- Only `shared/widgets/offline_banner.dart` consumes `connectivity_plus`; no dio-level cache or retry, no offline queue for attendance / leave submissions.
- `PayrollCubit:62` swallows exceptions to `"Could not load payroll"` — lose 4xx detail.

**Deep links / cold-start**
- `app_router.dart:123` redirects on splash and doesn't preserve the intended deep link. Add a `pending` route param.

**Permissions**
- Missing on Android: `READ_MEDIA_IMAGES` for API 33+ if uploading gallery images. iOS missing `NSMicrophoneUsageDescription` (mobile_scanner may need it). Others (biometric, camera, notifications, location) declared.

**Analytics / crash reporting**
- **None.** No Crashlytics / Sentry / analytics import anywhere in `lib/`. Only `debugPrint`.

**File-size**
- `profile_page.dart` **1 177**, `dashboard_page.dart` **779**, `attendance_calendar_page.dart` **627**, `verification_form_page.dart` 565, `sales_targets_page.dart` 526, `justice_submit_page.dart` 516, `lead_detail_page.dart` 512, `director_dashboard_page.dart` 501.

**Testing**
- **One** file (`test/widget_test.dart`). Effective coverage: zero.

### 3.3 New Features to Add

1. **Push topic subscription** (`payroll_disbursed`, `leave_decision`, `dwp_reminder`) — hook into `push_notifications_service.dart:127`.
2. **Offline queue** for attendance selfie + leave applications (Hive box; drain on `connectivity_plus` restore).
3. **Dark-mode toggle** — `SettingsCubit` already models `ThemeMode`; `app.dart:53` hardcodes `ThemeMode.dark`. Wire the state through.
4. **On-device face recognition** (`google_mlkit_face_detection`) before selfie POST.
5. **QR visitor-pass PDF export** via `share_plus`.
6. **In-app PDF payslip preview** (`pdfx` or `syncfusion_flutter_pdfviewer`).
7. **"What's New" cards** keyed off `SharedPreferences` version.
8. **Fuzzy directory search** (`fuzzywuzzy`).
9. **Slack / Teams share** for letters (`share_plus`).
10. **Pinned in-app HR chat** per employee.
11. **Birthday / anniversary reminders** via `flutter_local_notifications`.
12. **Home-screen check-in widget** (`home_widget` package).
13. **One-tap timesheet fill** for consecutive present days.

### 3.4 Optimizations

- `cached_network_image` is in `pubspec.yaml:36` but **zero call sites** — swap into `_ProfileHero`, employee list avatars, LMS course thumbnails.
- Convert non-builder `ListView` variants to `ListView.builder` / `SliverList` (42 files).
- Lower `image_picker` quality from 2000 px → 1280 px (`verification_form_page.dart:132`) — 2-3× smaller upload.
- Dedup concurrent identical GETs in `DioClient` via an in-flight map.
- Add `HydratedBloc` for `AttendanceCubit`, `PayrollCubit`, `LeavesCubit` so a cold start renders cached data.
- Split biggest files (`profile_page`, `dashboard_page`, `attendance_calendar_page`) into per-section widget files.
- Release: `android/app/build.gradle` has no `--tree-shake-icons`, no `minifyEnabled true`, no `shrinkResources true`, no ProGuard. Enable all three.
- Replace `google_fonts` (fetches at runtime) with a bundled subset in `assets/fonts` — saves ~200 kB runtime and the first-run fetch.

---

## 4. Cross-cutting Recommendations

| # | Item | Where | Effort | Impact |
|---|---|---|---|---|
| 1 | **Route-level code-splitting** on admin web | `hrms_admin_web/src/router/index.tsx` | 1 d | -2 MB first paint |
| 2 | **Squash `_PENDING_COLUMNS` into an Alembic migration** and retire `sync_columns` | `hrms_backend/app/database.py` + `alembic/versions/` | 2 d | Deterministic startup, safe read replicas |
| 3 | **Real MFA verify** — replace static `"000000"` gate | `hrms_backend/app/api/admin/auth.py:152` | 0.5 d | Closes prod hole |
| 4 | **Real change-password revocation on mobile** | `hrms_mobile/lib/features/auth/data/repositories/auth_repository_impl.dart:63` | 0.5 d | Kills stolen refresh tokens |
| 5 | **Composite DB indexes** for attendance / leaves / payslips / audit / notifications | new Alembic revision | 0.5 d | Order-of-magnitude on hot queries |
| 6 | **PermissionGate every write action** on admin web | ~30 files | 1.5 d | Prevents UI showing forbidden actions |
| 7 | **List virtualization** + **pagination** (backend + admin) | Employees / Payslips / Leaves / Approvals / Audit logs | 2 d | Handles 10 k+ rows |
| 8 | **Extract huge files** — `EmployeeDetailPage.tsx` (2 110 L), `profile_page.dart` (1 177 L), `dashboard_page.dart` (779 L) | multiple | 2 d | Maintainability |
| 9 | **Move PDF / offer / letter generation into background workers** | `hrms_backend/app/workers/` | 1.5 d | Frees the request path |
| 10 | **Crashlytics on mobile + Sentry on backend + admin** | wiring | 0.5 d | Production observability |
| 11 | **Cache-Control + ETag on lookup endpoints** | backend + client query staleTime bumps | 0.5 d | Lower load, faster UI |
| 12 | **First test pass** — LoginPage smoke, apiClient 401 refresh, payroll math property tests | 2 d | Regression floor |
| 13 | **i18n extraction** (mobile Text literals → ARB; admin strings → react-i18next) | 3 d | Ships Hindi + future locales |
| 14 | **Real cookie SameSite policy** driven by `settings.CROSS_ORIGIN` | `hrms_backend/app/api/admin/auth.py:40` | 0.25 d | Cross-domain SPA works cleanly |
| 15 | **Rate-limit login + MFA + reset with Redis** | `hrms_backend/app/core/middleware.py` | 1 d | Brute-force protection |
| 16 | **Bulk actions on employees + bulk payslip email** | admin + backend | 2 d | Ops speedup |
| 17 | **Letter template versioning + audit log** | backend model + admin panel + Letters page tab | 2 d | Compliance |
| 18 | **Offline queue on mobile** (Hive + connectivity_plus) | `hrms_mobile/lib/core/offline/` | 3 d | Field workforce reliability |

**Ordering suggestion:** items 1 – 5 are one week of load-bearing fixes that unlock everything else. 6 – 12 form the "production readiness" sprint. 13 – 18 belong to the next quarter.

---

_All findings are the output of three parallel sub-audits (backend, admin, mobile). File paths + line ranges above are literal — grep the citation to reproduce._
